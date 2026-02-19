document.addEventListener('DOMContentLoaded', function () {
    // ── State ──
    let selectedSeeds = [];
    let swipeQueue = [];
    let currentIndex = 0;
    let likedCount = 0;
    let skippedCount = 0;
    let searchTimeout = null;
    let swipeTarget = 'liked';
    let isDragging = false;
    let startX = 0;
    let currentX = 0;
    let isLoadingMore = false;
    let queueFullyLoaded = false;
    let currentAudio = null;
    let isAnimating = false;
    let prev_track = null;

    // ── DOM refs ──
    const seedSetup = document.getElementById('seed-setup');
    const loadingScreen = document.getElementById('loading-screen');
    const swipeScreen = document.getElementById('swipe-screen');
    const doneScreen = document.getElementById('done-screen');

    const seedSearch = document.getElementById('seed-search');
    const searchResults = document.getElementById('search-results');
    const seedsList = document.getElementById('seeds-list');
    const seedCountEl = document.getElementById('seed-count');
    const startSeedsBtn = document.getElementById('start-seeds-btn');
    const startRandomBtn = document.getElementById('start-random-btn');
    const targetSelect = document.getElementById('target-select');
    const loadingSeeds = document.getElementById('loading-seeds');

    const swipeCard = document.getElementById('swipe-card');
    const cardArt = document.getElementById('card-art');
    const cardTitle = document.getElementById('card-title');
    const cardArtist = document.getElementById('card-artist');
    const cardAlbum = document.getElementById('card-album');
    const overlayLeft = document.getElementById('swipe-overlay-left');
    const overlayRight = document.getElementById('swipe-overlay-right');
    const likedCountEl = document.getElementById('liked-count');
    const remainingCountEl = document.getElementById('remaining-count');
    const skippedCountEl = document.getElementById('skipped-count');

    const btnSkip = document.getElementById('btn-skip');
    const btnLike = document.getElementById('btn-like');
    const btnBack = document.getElementById('btn-back');
    const restartBtn = document.getElementById('restart-btn');
    const doneSummary = document.getElementById('done-summary');

    // ── Prevent image drag on the card ──
    cardArt.addEventListener('dragstart', function (e) { e.preventDefault(); });
    cardArt.style.pointerEvents = 'none';
    cardArt.setAttribute('draggable', 'false');

    // ── Load user playlists into target dropdown ──
    fetch('/get_user_playlists')
        .then(r => r.json())
        .then(playlists => {
            if (Array.isArray(playlists)) {
                playlists.forEach(pl => {
                    const opt = document.createElement('option');
                    opt.value = pl.uri;
                    opt.textContent = '\uD83D\uDCC1 ' + pl.name;
                    targetSelect.appendChild(opt);
                });
            }
        })
        .catch(() => {});

    targetSelect.addEventListener('change', function () {
        swipeTarget = this.value;
    });

    // ── Search with debounce ──
    seedSearch.addEventListener('input', function () {
        const query = this.value.trim();
        clearTimeout(searchTimeout);

        if (query.length < 2) {
            searchResults.classList.add('hidden');
            return;
        }

        searchTimeout = setTimeout(() => {
            fetch('/api/discover/search_tracks?q=' + encodeURIComponent(query))
                .then(r => r.json())
                .then(tracks => renderSearchResults(tracks))
                .catch(() => searchResults.classList.add('hidden'));
        }, 300);
    });

    document.addEventListener('click', function (e) {
        if (!e.target.closest('.search-wrapper')) {
            searchResults.classList.add('hidden');
        }
    });

    function renderSearchResults(tracks) {
        searchResults.innerHTML = '';
        if (!tracks.length) {
            searchResults.innerHTML = '<div class="search-result-item"><span style="color:#b3b3b3">No results found</span></div>';
            searchResults.classList.remove('hidden');
            return;
        }
        tracks.forEach(track => {
            if (selectedSeeds.find(s => s.id === track.id)) return;
            const item = document.createElement('div');
            item.className = 'search-result-item';
            item.innerHTML =
                '<img src="' + (track.album_art || '') + '" alt="">' +
                '<div class="search-result-info">' +
                '<div class="track-name">' + escapeHtml(track.name) + '</div>' +
                '<div class="artist-name">' + escapeHtml(track.artist) + '</div>' +
                '</div>';
            item.addEventListener('click', () => addSeed(track));
            searchResults.appendChild(item);
        });
        searchResults.classList.remove('hidden');
    }

    function addSeed(track) {
        if (selectedSeeds.length >= 5) return;
        if (selectedSeeds.find(s => s.id === track.id)) return;
        selectedSeeds.push(track);
        renderSeeds();
        seedSearch.value = '';
        searchResults.classList.add('hidden');
    }

    function removeSeed(id) {
        selectedSeeds = selectedSeeds.filter(s => s.id !== id);
        renderSeeds();
    }

    function renderSeeds() {
        seedCountEl.textContent = selectedSeeds.length;
        startSeedsBtn.disabled = selectedSeeds.length === 0;
        seedsList.innerHTML = '';
        selectedSeeds.forEach(seed => {
            const chip = document.createElement('div');
            chip.className = 'seed-chip';
            chip.innerHTML =
                (seed.album_art ? '<img src="' + seed.album_art + '" alt="">' : '') +
                '<span class="seed-text">' + escapeHtml(seed.name) + ' \u2014 ' + escapeHtml(seed.artist) + '</span>' +
                '<span class="remove-seed" data-id="' + seed.id + '">\u2715</span>';
            chip.querySelector('.remove-seed').addEventListener('click', () => removeSeed(seed.id));
            seedsList.appendChild(chip);
        });
    }

    // ── Start session ──
    startSeedsBtn.addEventListener('click', () => startSession(selectedSeeds.map(s => s.uri)));
    startRandomBtn.addEventListener('click', () => startSession([]));

    restartBtn.addEventListener('click', () => {
        stopPreview();
        selectedSeeds = [];
        swipeQueue = [];
        currentIndex = 0;
        likedCount = 0;
        skippedCount = 0;
        isLoadingMore = false;
        queueFullyLoaded = false;
        isAnimating = false;
        prev_track = null;
        updateBackButton();
        renderSeeds();
        showScreen(seedSetup);
    });

    function startSession(seedUris) {
        showScreen(loadingScreen);
        loadingSeeds.textContent = seedUris.length
            ? 'Seeds: ' + selectedSeeds.map(s => s.name).join(', ')
            : 'Picking random liked songs as seeds...';

        swipeQueue = [];
        currentIndex = 0;
        likedCount = 0;
        skippedCount = 0;
        isLoadingMore = true;
        queueFullyLoaded = false;
        isAnimating = false;
        prev_track = null;
        updateBackButton();

        fetch('/api/discover/generate_stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seed_uris: seedUris })
        }).then(response => {
            if (!response.ok) throw new Error('Failed to start generation');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let firstBatchReceived = false;

            function processStream() {
                reader.read().then(({ done, value }) => {
                    if (done) {
                        isLoadingMore = false;
                        queueFullyLoaded = true;
                        updateStats();
                        if (swipeQueue.length === 0) {
                            alert('No similar tracks found. Try different seeds.');
                            showScreen(seedSetup);
                        }
                        // If user was waiting at end of partial queue, check now
                        if (!isAnimating && currentIndex >= swipeQueue.length) {
                            finishSession();
                        }
                        return;
                    }

                    buffer += decoder.decode(value, { stream: true });
                    var lines = buffer.split('\n');
                    buffer = '';

                    for (var i = 0; i < lines.length; i++) {
                        var line = lines[i];
                        if (line.startsWith('data: ')) {
                            try {
                                var data = JSON.parse(line.substring(6));
                                if (data.error) {
                                    alert('Error: ' + data.error);
                                    if (swipeQueue.length === 0) {
                                        showScreen(seedSetup);
                                        return;
                                    }
                                }
                                if (data.batch && data.batch.length > 0) {
                                    swipeQueue.push.apply(swipeQueue, data.batch);
                                    // Preload images for new batch
                                    data.batch.forEach(function(t) {
                                        if (t.album_art) {
                                            var img = new Image();
                                            img.src = t.album_art;
                                        }
                                    });
                                }
                                if (data.seeds_used && data.seeds_used.length > 0) {
                                }
                                if (!firstBatchReceived && swipeQueue.length > 0) {
                                    firstBatchReceived = true;
                                    updateStats();
                                    displayCurrentCard();
                                    showScreen(swipeScreen);
                                } else {
                                    updateStats();
                                }
                                if (data.done) {
                                    isLoadingMore = false;
                                    queueFullyLoaded = true;
                                    updateStats();
                                }
                            } catch (e) {
                                buffer = lines.slice(i).join('\n');
                                break;
                            }
                        } else if (line !== '') {
                            buffer += line + '\n';
                        }
                    }
                    processStream();
                }).catch(err => {
                    isLoadingMore = false;
                    queueFullyLoaded = true;
                    if (swipeQueue.length === 0) {
                        alert('Failed to generate queue: ' + err.message);
                        showScreen(seedSetup);
                    }
                    updateStats();
                });
            }
            processStream();
        }).catch(err => {
            alert('Failed to generate queue: ' + err.message);
            showScreen(seedSetup);
        });
    }

    // ── Audio preview ──
    function playPreview(url) {
        stopPreview();
        if (!url) {
            updatePreviewIndicator(false, false);
            return;
        }
        currentAudio = new Audio(url);
        currentAudio.volume = 0.5;
        currentAudio.play().catch(function() {});
        currentAudio.addEventListener('ended', function() {
            updatePreviewIndicator(false, true);
        });
        updatePreviewIndicator(true, true);
    }

    function stopPreview() {
        if (currentAudio) {
            currentAudio.pause();
            currentAudio.src = '';
            currentAudio = null;
        }
        updatePreviewIndicator(false, !!swipeQueue[currentIndex]?.preview_url);
    }

    function updatePreviewIndicator(isPlaying, hasPreview) {
        const indicator = document.getElementById('preview-indicator');
        if (!indicator) return;
        if (!hasPreview) {
            indicator.classList.remove('visible');
            return;
        }
        indicator.textContent = isPlaying ? '⏸' : '▶';
        indicator.classList.add('visible');
    }

    // Make card tappable to toggle preview
    swipeCard.addEventListener('click', function (e) {
        // Prevent if animating or no track
        if (isAnimating || currentIndex >= swipeQueue.length) return;
        // If dragging, don't toggle
        if (Math.abs(currentX) > 10) return; // Small threshold to avoid accidental toggle during drag
        const track = swipeQueue[currentIndex];
        if (currentAudio && !currentAudio.paused) {
            stopPreview();
        } else {
            playPreview(track.preview_url);
        }
    });

    // ── Card display ──
    function displayCurrentCard() {
        isAnimating = false;

        if (currentIndex >= swipeQueue.length) {
            if (queueFullyLoaded) {
                finishSession();
            }
            // If still loading, just wait — the stream handler will trigger display
            return;
        }

        var track = swipeQueue[currentIndex];
        cardTitle.textContent = track.name;
        cardArtist.textContent = track.artist;
        cardAlbum.textContent = track.album || '';

        // Immediately hide the old image, then set the new one
        if (track.album_art) {
            cardArt.src = track.album_art;
            cardArt.style.display = '';
        } else {
            cardArt.src = '';
            cardArt.style.display = 'none';
        }

        swipeCard.style.transform = '';
        swipeCard.style.opacity = '1';
        swipeCard.classList.remove('animating');
        overlayLeft.style.opacity = 0;
        overlayRight.style.opacity = 0;

        // Preload next card image
        if (currentIndex + 1 < swipeQueue.length) {
            var next = swipeQueue[currentIndex + 1];
            if (next.album_art) {
                var preloadImg = new Image();
                preloadImg.src = next.album_art;
            }
        }

        updateStats();
        // Auto-play preview
        playPreview(track.preview_url);
    }

    function updateStats() {
        likedCountEl.textContent = likedCount;
        skippedCountEl.textContent = skippedCount;
        var remaining = Math.max(0, swipeQueue.length - currentIndex);
        remainingCountEl.textContent = remaining + (isLoadingMore ? '+' : '');
    }

    // ── Swipe actions ──
    function swipeRight() {
        if (isAnimating || currentIndex >= swipeQueue.length) return;
        var track = swipeQueue[currentIndex];

        stopPreview();
        animateCard('right');

        // Liking resets the back button
        prev_track = null;
        updateBackButton();

        var target = swipeTarget === 'liked' ? 'liked' : swipeTarget.split(':').pop();
        fetch('/api/discover/swipe_right', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: track.name, artist: track.artist, target: target })
        })
        .then(r => r.json())
        .then(data => {
            if (data.not_found) {
                showToast('Not found on Spotify');
            }
        })
        .catch(() => {});

        likedCount++;
        currentIndex++;
    }

    function swipeLeft() {
        if (isAnimating || currentIndex >= swipeQueue.length) return;

        // Save current track so user can go back
        prev_track = { index: currentIndex };

        stopPreview();
        animateCard('left');
        skippedCount++;
        currentIndex++;

        updateBackButton();
    }

    function animateCard(direction) {
        isAnimating = true;
        var offset = direction === 'right' ? 600 : -600;
        swipeCard.classList.add('animating');
        swipeCard.style.transform = 'translateX(' + offset + 'px) rotate(' + (direction === 'right' ? 20 : -20) + 'deg)';
        swipeCard.style.opacity = '0';
        setTimeout(function() { displayCurrentCard(); }, 350);
    }

    btnSkip.addEventListener('click', swipeLeft);
    btnLike.addEventListener('click', swipeRight);

    // ── Back button: go back to the last skipped track ──
    btnBack.addEventListener('click', function () {
        if (!prev_track || isAnimating) return;

        stopPreview();
        currentIndex = prev_track.index;
        skippedCount--;
        prev_track = null;
        updateBackButton();
        displayCurrentCard();
    });

    // Initialise back button as disabled
    updateBackButton();

    // ── Keyboard controls ──
    document.addEventListener('keydown', (e) => {
        if (swipeScreen.classList.contains('hidden')) return;
        if (e.key === 'ArrowLeft') { e.preventDefault(); swipeLeft(); }
        else if (e.key === 'ArrowRight') { e.preventDefault(); swipeRight(); }
        else if (e.key === ' ') {
            e.preventDefault();
            // Toggle preview on space
            if (currentIndex >= swipeQueue.length) return;
            const track = swipeQueue[currentIndex];
            if (currentAudio && !currentAudio.paused) {
                stopPreview();
            } else {
                playPreview(track.preview_url);
            }
        }
    });

    // ── Touch / mouse drag on card ──
    swipeCard.addEventListener('mousedown', dragStart);
    swipeCard.addEventListener('touchstart', dragStart, { passive: true });
    document.addEventListener('mousemove', dragMove);
    document.addEventListener('touchmove', dragMove, { passive: false });
    document.addEventListener('mouseup', dragEnd);
    document.addEventListener('touchend', dragEnd);

    function dragStart(e) {
        if (swipeScreen.classList.contains('hidden') || isAnimating) return;
        isDragging = true;
        startX = e.type === 'touchstart' ? e.touches[0].clientX : e.clientX;
        currentX = 0;
        swipeCard.style.transition = 'none';
    }

    function dragMove(e) {
        if (!isDragging) return;
        var clientX = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX;
        currentX = clientX - startX;
        swipeCard.style.transform = 'translateX(' + currentX + 'px) rotate(' + (currentX * 0.08) + 'deg)';
        var threshold = 50;
        if (currentX > threshold) {
            overlayRight.style.opacity = Math.min((currentX - threshold) / 80, 1);
            overlayLeft.style.opacity = 0;
        } else if (currentX < -threshold) {
            overlayLeft.style.opacity = Math.min((-currentX - threshold) / 80, 1);
            overlayRight.style.opacity = 0;
        } else {
            overlayLeft.style.opacity = 0;
            overlayRight.style.opacity = 0;
        }
    }

    function dragEnd() {
        if (!isDragging) return;
        isDragging = false;
        swipeCard.style.transition = '';
        if (currentX > 100) { swipeRight(); }
        else if (currentX < -100) { swipeLeft(); }
        else {
            swipeCard.style.transform = '';
            overlayLeft.style.opacity = 0;
            overlayRight.style.opacity = 0;
        }
    }

    // ── Session complete ──
    function finishSession() {
        stopPreview();
        prev_track = null;
        updateBackButton();
        doneSummary.textContent = 'You liked ' + likedCount + ' track' + (likedCount !== 1 ? 's' : '') + ' and skipped ' + skippedCount + '.';
        showScreen(doneScreen);
    }

    // ── Toast notification ──
    function showToast(message) {
        var toast = document.getElementById('toast-notification');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast-notification';
            toast.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#333;color:#fff;padding:10px 20px;border-radius:8px;font-size:0.9em;z-index:100;opacity:0;transition:opacity 0.3s;';
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.style.opacity = '1';
        setTimeout(function() { toast.style.opacity = '0'; }, 2500);
    }

    // ── Helpers ──
    function showScreen(screen) {
        [seedSetup, loadingScreen, swipeScreen, doneScreen].forEach(s => s.classList.add('hidden'));
        screen.classList.remove('hidden');
    }

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    // ── Helper to update back button state ──
    function updateBackButton() {
        if (prev_track) {
            btnBack.disabled = false;
            btnBack.classList.remove('disabled');
        } else {
            btnBack.disabled = true;
            btnBack.classList.add('disabled');
        }
    }
});
