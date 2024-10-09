document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const songSeedInput = document.getElementById('song-seed-input');
    const playlistSeedInput = document.getElementById('playlist-seed-input');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            if (this.dataset.tab === 'song-seed') {
                songSeedInput.style.display = 'block';
                playlistSeedInput.style.display = 'none';
            } else {
                songSeedInput.style.display = 'none';
                playlistSeedInput.style.display = 'block';
            }
        });
    });

    populatePlaylistDropdown();
});

async function populatePlaylistDropdown() {
    try {
        const response = await fetch('/get_user_playlists');
        const playlists = await response.json();
        
        const playlistSelect = document.getElementById('seed-playlist');
        playlists.forEach(playlist => {
            const option = document.createElement('option');
            option.value = playlist.uri;
            option.textContent = playlist.name;
            playlistSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error populating playlist dropdown:', error);
    }
}

let animationInterval;
let dots = 0;

document.getElementById('generate-songs-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    startGenerating();

    try {
        const activeTab = document.querySelector('.tab-button.active').dataset.tab;
        const seedValue = activeTab === 'song-seed' 
            ? document.getElementById('seed-song').value 
            : document.getElementById('seed-playlist').value;
        const numOfSongs = document.getElementById('number-of-songs').value;
        const playlistName = document.getElementById('playlist-name-input').value;

        if (!seedValue || !numOfSongs || !playlistName) {
            throw new Error("Please fill in all fields.");
        }

        let songURIs;

        if (activeTab === 'song-seed') {
            const response = await fetch('/search_song', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: seedValue })
            });
            const result = await response.json();
            if (result.error) {
                throw new Error(result.error);
            }
            songURIs = result.song_uris;
        } else {
            const response = await fetch('/get_playlist_songs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ playlist_uri: seedValue })
            });
            const result = await response.json();
            if (result.error) {
                throw new Error(result.error);
            }
            songURIs = result.song_uris;
        }

        if (!songURIs || songURIs.length === 0) {
            throw new Error("No songs found. Please try a different seed.");
        }
        
        const response = await fetch('/generate_playlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                song_uris: songURIs,
                num_of_songs: numOfSongs,
                playlist_name: playlistName
            })
        });

        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }

        alert(`Playlist created successfully! Playlist Name: ${result.playlistName || playlistName}`);

        displayPlaylistInfo({
            coverUrl: result.coverUrl, 
            name: result.playlistName || playlistName,
            songCount: result.actual_song_count
        });

    } catch (error) {
        alert(error.message);
    } finally {
        endGenerating();
    }
});

function startGenerating() {
    const generateButton = document.getElementById('generate-songs-button');
    const progressContainer = document.getElementById('progress-container');
    const resultsContainer = document.getElementById('results');

    generateButton.disabled = true;
    progressContainer.classList.remove('hidden');
    resultsContainer.classList.add('hidden');
    
    dots = 0;
    animationInterval = setInterval(animateEllipsis, 500);
}

function animateEllipsis() {
    const progressText = document.getElementById('progress-text');
    dots = (dots + 1) % 4;
    progressText.textContent = 'Generating' + '.'.repeat(dots);
}

function endGenerating() {
    const generateButton = document.getElementById('generate-songs-button');
    const progressContainer = document.getElementById('progress-container');

    clearInterval(animationInterval);
    animationInterval = null;
    generateButton.disabled = false;
    progressContainer.classList.add('hidden');
    
    // Reset progress text
    const progressText = document.getElementById('progress-text');
    progressText.textContent = 'Generating';
}

function displayPlaylistInfo(playlistData) {
    console.log('Displaying playlist info:', playlistData);
    
    const playlistCover = document.getElementById('playlist-cover');
    const playlistNameElement = document.getElementById('playlist-name-display');
    const songCountElement = document.getElementById('song-count');
    const resultsElement = document.getElementById('results');

    if (playlistCover) {
        playlistCover.src = playlistData.coverUrl || '';
    } else {
        console.error('Element with id "playlist-cover" not found');
    }

    if (playlistNameElement) {
        playlistNameElement.textContent = playlistData.name;
    } else {
        console.error('Element with id "playlist-name-display" not found');
    }

    if (songCountElement) {
        songCountElement.textContent = `${playlistData.songCount} songs`;
    } else {
        console.error('Element with id "song-count" not found');
    }

    if (resultsElement) {
        resultsElement.classList.remove('hidden');
        resultsElement.classList.add('visible');
    } else {
        console.error('Element with id "results" not found');
    }
}