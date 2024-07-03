document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const likedSongsInput = document.getElementById('liked-songs-input');
    const savedPlaylistInput = document.getElementById('saved-playlist-input');
    const sortSongsForm = document.getElementById('sort-songs-form');
    const resultsSection = document.getElementById('results');
    const playlistCover = document.getElementById('playlist-cover');
    const playlistNameDisplay = document.getElementById('playlist-name-display');
    const songCount = document.getElementById('song-count');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            if (button.dataset.tab === 'liked-songs') {
                likedSongsInput.style.display = 'block';
                savedPlaylistInput.style.display = 'none';
            } else {
                likedSongsInput.style.display = 'none';
                savedPlaylistInput.style.display = 'block';
            }
        });
    });

    sortSongsForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const choice = document.querySelector('.tab-button.active').dataset.tab === 'liked-songs' ? 'liked' : 'playlist';
        const targetGenre = document.getElementById('target-genre').value;
        const playlistName = document.getElementById('playlist-name-input').value;
        const maxTracks = choice === 'liked' ? document.getElementById('liked-songs-limit').value : null;
        const savedPlaylist = choice === 'playlist' ? document.getElementById('saved-playlist-select').value : null;

        fetch('/sort_songs_action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                choice: choice,
                targetGenre: targetGenre,
                playlistName: playlistName,
                maxTracks: maxTracks,
                savedPlaylist: savedPlaylist
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                playlistCover.src = data.coverUrl;
                playlistNameDisplay.textContent = data.playlistName;
                songCount.textContent = `Number of songs: ${data.songCount}`;
                resultsSection.classList.remove('hidden');
            } else {
                alert(`Error: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while sorting songs.');
        });
    });

    // Fetch user's playlists to populate the saved playlist select element
    fetch('/get_user_playlists')
        .then(response => response.json())
        .then(data => {
            const savedPlaylistSelect = document.getElementById('saved-playlist-select');
            data.forEach(playlist => {
                const option = document.createElement('option');
                option.value = playlist.uri;
                option.textContent = playlist.name;
                savedPlaylistSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error fetching playlists:', error);
        });
});