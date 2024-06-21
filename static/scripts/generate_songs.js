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

document.getElementById('generate-songs-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const activeTab = document.querySelector('.tab-button.active').dataset.tab;
    const seedValue = activeTab === 'song-seed' 
        ? document.getElementById('seed-song').value 
        : document.getElementById('seed-playlist').value;
    const numOfSongs = document.getElementById('number-of-songs').value;
    const playlistName = document.getElementById('playlist-name').value;

    if (!seedValue || !numOfSongs || !playlistName) {
        alert("Please fill in all fields.");
        return;
    }

    let songURIs;

    if (activeTab === 'song-seed') {
        console.log('Searching for song:', seedValue);
        const response = await fetch('/search_song', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: seedValue })
        });
        const result = await response.json();
        console.log('Search result:', result);
        if (result.error) {
            alert(result.error);
            return;
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
            alert(result.error);
            return;
        }
        songURIs = result.song_uris;
    }

    console.log('Song URIs:', songURIs);

    if (!songURIs || songURIs.length === 0) {
        alert("No songs found. Please try a different seed.");
        return;
    }

    console.log('Sending to /generate_playlist:', {
        song_uris: songURIs,
        num_of_songs: numOfSongs,
        playlist_name: playlistName
    });
    
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
        alert(result.error);
    } else {
        alert(`Playlist created successfully! Playlist ID: ${result.playlist_id}`);
        // Optionally, display the generated songs
        const generatedSongsList = document.getElementById('generated-songs-list');
        generatedSongsList.innerHTML = '';
        result.track_uris.forEach(uri => {
            const li = document.createElement('li');
            li.textContent = uri;
            generatedSongsList.appendChild(li);
        });
        document.getElementById('results').classList.remove('hidden');
    }
});