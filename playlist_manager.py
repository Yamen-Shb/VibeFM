import spotify_utils
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


def getPlaylistSongURIs(sp, playlistURI):
    # Initialize some variables
    offset = 0
    limit = 100  # Maximum limit for fetching songs
    song_uris_in_playlist = []

    try:
        while True:
            # Fetch a batch of songs (up to the API limit)
            results = sp.playlist_items(playlistURI, offset=offset, limit=limit)

            if not results['items']:
                break  # No more songs to fetch

            # Extract song URIs from the batch and add them to the list
            batch_uris = [item['track']['uri'] for item in results['items'] if item['track'] is not None]
            song_uris_in_playlist.extend(batch_uris)

            # Update the offset for the next batch
            offset += limit

        return {'song_uris': song_uris_in_playlist}
    except Exception as e:
        print(f"Error fetching playlist songs: {e}")
        return {'error': str(e)}


def sortSongs(sp, artistCache, username):
    offset = 0
    limit = 50  # Set an initial limit for pagination
    counter = 0
    reachedSongNumber = True
    likedTracks = []
    matchingTracks = []
    numberOfTracksToCheck = 0

    # List of genres
    existingGenres = ["rock", "pop", "hip-hop", "jazz", "indie", "rap", "r&b", "arab", "phonk"]

    choice = input("Enter your choice (1 for playlist, 2 for liked songs): ")

    if choice == '1':
        while True:
            playlist_id = choosePlaylist(sp)
            if playlist_id:
                print(f"Selected playlist ID: {playlist_id}")
                break
            else:
                print("Playlist not found, please try again.")

    else:
        playlist_id = None  # Indicates that we're getting liked songs

        numberOfTracksToCheckInput = input(
            "Please input the number of songs you want to sort through (0 if all liked songs): ")
        numberOfTracksToCheck = int(numberOfTracksToCheckInput)

        while numberOfTracksToCheck < 0:
            numberOfTracksToCheckInput = input("Invalid number of songs. Please try again: ")
            numberOfTracksToCheck = int(numberOfTracksToCheckInput)

    target_genre = input("Please input your target genre: ")

    while target_genre not in existingGenres:
        print("Genre does not exist, please enter an existing genre!")
        target_genre = input("Please input your target genre: ")

    while True:
        results = sp.playlist_items(playlist_id, limit=limit, offset=offset) if playlist_id else sp.current_user_saved_tracks(limit=limit, offset=offset)

        if not results['items']:
            break

        likedTracks.extend(results['items'])

        if not reachedSongNumber:
            break

        for trackInfo in results['items']:
            counter += 1
            genreMatch = False
            currentLikedSong = trackInfo['track']

            if counter % 25 == 0:
                time.sleep(1.2)

            if playlist_id is None:
                if counter == numberOfTracksToCheck:
                    reachedSongNumber = False
                    break

            # Access the list of artists for the current song
            artists = currentLikedSong['artists']

            # Print the counter once for each song
            print(counter, end=" ")

            # Print song details only once per song
            print(f"Song: {currentLikedSong['name']} - Genres: ", end="")

            genres_list = []  # Store genres in a list

            for artist in artists:
                artistURI = artist['uri']

                # Check if artist information is in the cache
                if artistURI in artistCache:
                    artistsDetails = artistCache[artistURI]
                else:
                    # Make an API call to get artist details
                    artistsDetails = sp.artist(artistURI)
                    # Cache the artist information
                    artistCache[artistURI] = artistsDetails

                if 'genres' in artistsDetails:
                    # Store genres in the list
                    genres_list.extend(artistsDetails['genres'])

                    for genre in artistsDetails['genres']:
                        if target_genre in genre:
                            matchingTracks.append(currentLikedSong['uri'])
                            genreMatch = True
                            break

                    # Break out of the loop if genreMatch is True
                    if genreMatch:
                        break

            # Print the concatenated genres
            print(', '.join(genres_list))

        offset += len(results['items'])  # Update the offset for the next page

    if len(matchingTracks) == 0:
        print("There are no songs matching this genre in your liked tracks, sorry!")
        return

    print(f"{len(matchingTracks)} matching tracks")
    choice = input("Would you like to add these songs to a "
                   "new playlist or an existing playlist (1 "
                   "for new 2 for existing): ")

    # Optimize this because entering a number isn't professional
    # Convert the user's input to an integer
    choice = int(choice)

    if choice == 1:
        addSongsToPlaylist(sp, username, createPlaylist(sp), matchingTracks)
    elif choice == 2:
        # Optimize this because typing a name to make a choice is terrible
        playlistURI = choosePlaylist(sp)
        addSongsToPlaylist(sp, username, playlistURI, matchingTracks)


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