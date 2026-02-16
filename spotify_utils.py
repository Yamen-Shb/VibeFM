def getPlaylistID(sp, playlist_name):
    # Set the limit to the number of playlists you want to fetch per request
    limit = 50

    # Initialize offset for pagination
    offset = 0

    while True:
        # Fetch playlists in batches
        playlists_batch = sp.current_user_playlists(offset=offset, limit=limit)['items']

        # Check if the playlist is in the current batch
        for playlist in playlists_batch:
            if playlist['name'] == playlist_name:
                return playlist['id']

        # No more playlists to fetch
        if len(playlists_batch) < limit:
            break

        # Increment the offset for the next batch
        offset += limit

    # Playlist not found
    return None


def searchForSong(sp, query):
    try:
        # Perform the search using the Spotify API
        results = sp.search(q=query, type='track', limit=1)

        # Extract the URI of the first track if results are found
        if 'tracks' in results and 'items' in results['tracks'] and results['tracks']['items']:
            firstTrackURI = results['tracks']['items'][0]['uri']
            return {'song_uris': [firstTrackURI]}
        else:
            return {'error': 'No tracks found'}
    except Exception as e:
        print(f"Error in searchForSong: {e}")
        return {'error': str(e)}
