document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const songSeedInput = document.getElementById('song-seed-input');
    const playlistSeedInput = document.getElementById('playlist-seed-input');
    const form = document.getElementById('generate-songs-form');

    // Tab switching
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

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const seedType = document.querySelector('.tab-button.active').dataset.tab;
        const numberOfSongs = document.getElementById('number-of-songs').value;
        const newPlaylistName = document.getElementById('playlist-name').value;
        
        let seedValue;
        if (seedType === 'song-seed') {
            seedValue = document.getElementById('seed-song').value;
        } else {
            seedValue = document.getElementById('seed-playlist').value;
        }

        // Here you would call your API to generate the playlist
        console.log('Generating playlist with:', {
            seedType,
            seedValue,
            numberOfSongs,
            newPlaylistName
        });

        // After successful generation, you can show the results
        // document.getElementById('results').classList.remove('hidden');
        // Populate the generated-songs-list
    });

    // You'll need to populate the playlist select options when the page loads
    // This would typically involve fetching the user's playlists from your backend
    function populatePlaylistOptions() {
        // Fetch playlists and populate the select element
    }

    populatePlaylistOptions();
});