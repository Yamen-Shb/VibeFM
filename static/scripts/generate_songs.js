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
    const playlistName = document.getElementById('playlist-name-input').value;

    if (!seedValue || !numOfSongs || !playlistName) {
        alert("Please fill in all fields.");
        return;
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

    if (!songURIs || songURIs.length === 0) {
        alert("No songs found. Please try a different seed.");
        return;
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
        alert(result.error);
    } else {
        alert(`Playlist created successfully! Playlist Name: ${result.playlistName || playlistName}`);

        displayPlaylistInfo({
            coverUrl: result.coverUrl, 
            name: result.playlistName || playlistName,
            songCount: result.track_uris.length
        });

        const resultsElement = document.getElementById('results');
        if (resultsElement) {
            resultsElement.classList.remove('hidden');
            resultsElement.classList.add('visible');
        } else {
            console.error('Element with id "results" not found');
        }
    }
});

function displayPlaylistInfo(playlistData) {
    console.log('Displaying playlist info:', playlistData);
    
    const playlistCover = document.getElementById('playlist-cover');
    const playlistNameElement = document.getElementById('playlist-name-display');
    const songCountElement = document.getElementById('song-count');

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
        const songCount = playlistData.songCount || playlistData.track_uris?.length || 0;
        console.log(`Song count is: ${songCount}`);
        songCountElement.textContent = `${songCount} songs`;
    } else {
        console.error('Element with id "song-count" not found');
    }

    const resultsElement = document.getElementById('results');
    if (resultsElement) {
        resultsElement.classList.remove('hidden');
        resultsElement.classList.add('visible');
    } else {
        console.error('Element with id "results" not found');
    }
}