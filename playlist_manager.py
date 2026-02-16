import time

def createPlaylist(sp, playlistName):
    playlistDescription = "Created by VibeFM :)"

    # Get the current user's username (ID)
    user_info = sp.current_user()
    user_id = user_info['id']

    # Create the new playlist
    createdPlaylist = sp.user_playlist_create(user_id, playlistName, description=playlistDescription)

    playlistID = createdPlaylist['id']
    return playlistID


def fetchTracks(sp, playlist_id=None, maxTracks=None):
    offset = 0
    limit=50
    allTracks = []

    while True:
        if playlist_id:
            results = sp.playlist_items(playlist_id, limit=limit, offset=offset, 
                                        fields='items(track(name,uri,artists(uri)))')
        else:
            results = sp.current_user_saved_tracks(limit=limit, offset=offset)

        if not results['items']:
            break

        allTracks.extend([item['track'] for item in results['items'] if item['track']])

        if maxTracks and len(allTracks) >= maxTracks:
            allTracks = allTracks[:maxTracks]
            break

        offset += limit

    return allTracks


def getPlaylistSongURIs(sp, playlistURI):
    try:
        tracks = fetchTracks(sp, playlist_id=playlistURI, maxTracks=None)
        songURIsInPlaylist = [track['uri'] for track in tracks if track is not None]
        return {'song_uris': songURIsInPlaylist}
    except Exception as e:
        print(f"Error fetching playlist songs: {e}")
        return {'error': str(e)}


def sortSongs(sp, choice, targetGenre, playlistName, maxTracks=None):
    offset = 0
    limit = 50
    matchingTracks = []
    artistCache = {}

    while True:
        tracks = fetchTracks(sp, choice, maxTracks)
        
        if not tracks:
            break

        for track in tracks:
            for artist in track['artists']:
                artistURI = artist['uri']
                
                if artistURI not in artistCache:
                    artistDetails = sp.artist(artistURI)
                    artistCache[artistURI] = artistDetails['genres']

                if any(targetGenre.lower() in genre.lower() for genre in artistCache[artistURI]):
                    matchingTracks.append(track['uri'])
                    break  # No need to check other artists for this track
            
            if maxTracks and len(matchingTracks) >= maxTracks:
                break

        if maxTracks and len(matchingTracks) >= maxTracks:
            break

        offset += limit

    if not matchingTracks:
        return {"error": "No matching tracks found"}

    # Create a new playlist and add songs
    playlistId = createPlaylist(sp, playlistName)
    addSongsToPlaylist(sp, playlistId, matchingTracks)

    return {
        "success": True,
        "playlist_id": playlistId,
        "tracks_added": len(matchingTracks)
    }

# Comments please, this is so ugly
def addSongsToPlaylist(sp, playlistID, songURIs):
    URIsInPlaylist = getPlaylistSongURIs(sp, playlistID)
    URIsInPlaylistSet = set(URIsInPlaylist)
    nonMatchingSongsToAdd = []

    if not URIsInPlaylist:
        iterationCount = 0
        while True:
            if len(songURIs) > 100:
                iterationCount += 1
                subsetOfSongsToAdd = songURIs[0:100]
                sp.playlist_add_items(playlistID, subsetOfSongsToAdd)
                del songURIs[0:100]
            elif 100 >= len(songURIs) > 0:
                sp.playlist_add_items(playlistID, songURIs)
                iterationCount += 1
                break
            if len(songURIs) == 0:
                break
        return
    else:
        iterationCount = 0
        while True:
            if len(songURIs) > 100:
                iterationCount += 1
                subsetOfSongsToCheck = songURIs[0:100]
                del songURIs[0:100]

                for song_uri in subsetOfSongsToCheck:
                    if song_uri not in URIsInPlaylistSet:
                        nonMatchingSongsToAdd.append(song_uri)
                        
            elif 100 >= len(songURIs) > 0:
                iterationCount += 1
                for song_uri in songURIs:
                    if song_uri not in URIsInPlaylistSet:
                        nonMatchingSongsToAdd.append(song_uri)

                break

    if nonMatchingSongsToAdd:
        # Add the songs to the playlist
        while True:
            if len(nonMatchingSongsToAdd) > 100:
                subsetOfSongsToAdd = nonMatchingSongsToAdd[0:100]
                sp.playlist_add_items(playlistID, subsetOfSongsToAdd)
                del nonMatchingSongsToAdd[0:100]
            elif 100 >= len(nonMatchingSongsToAdd) > 0:
                sp.playlist_add_items(playlistID, nonMatchingSongsToAdd)
                break
            if len(nonMatchingSongsToAdd) == 0:
                break