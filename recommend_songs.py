import audio_features
import spotify_utils
import playlist_manager


def chooseSeed(sp, username):
    print("Choose your seed:")
    print("1. Search for a Song")
    print("2. Choose a Playlist")
    choice = input("Enter your choice (1 or 2): ")

    if choice == '1':
        query = input("Enter the name of the song: ")
        songURI = spotify_utils.searchForSong(sp, query)
        if songURI:
            return [songURI]
        else:
            print("Song not found.")
            return chooseSeed(sp, username)
    elif choice == '2':
        playlistURI = playlist_manager.choosePlaylist(sp)
        # Your logic to fetch all song URIs from the playlist URI
        playlistURIs = playlist_manager.getPlaylistSongURIs(sp, playlistURI)
        return playlistURIs
    else:
        print("Invalid choice. Please enter 1 or 2.")
        return chooseSeed(sp, username)


def recommendBasedOnSeed(sp, username):
    songURIs = chooseSeed(sp, username)

    if not songURIs:
        print("No songs selected. Exiting.")
        return

    # Calculate average audio features if more than one song is selected
    if len(songURIs) > 1:
        audioFeature = audio_features.calculateAvgAudioFeatures(sp, songURIs)
    else:
        # Get audio features for a single song
        audioFeature = audio_features.getAudioFeatures(sp, songURIs[0])

    if not audioFeature:
        print("No audio features found. Exiting.")
        return

    numOfSongs = input("Enter the number of songs you want to generate: ")
    numOfSongs = int(numOfSongs)

    if 1 <= len(songURIs) <= 5:
        # Use the audio features as seed to get recommendations
        recommendations = sp.recommendations(seed_tracks=songURIs,
                                             target_acousticness=audioFeature['acousticness'],
                                             target_danceability=audioFeature['danceability'],
                                             target_energy=audioFeature['energy'],
                                             target_valence=audioFeature['valence'],
                                             target_tempo=audioFeature['tempo'],
                                             limit=numOfSongs+1)
    else:
        # Use the audio features as seed to get recommendations
        recommendations = sp.recommendations(seed_tracks=songURIs[0:5],
                                             target_acousticness=audioFeature['acousticness'],
                                             target_danceability=audioFeature['danceability'],
                                             target_energy=audioFeature['energy'],
                                             target_valence=audioFeature['valence'],
                                             target_tempo=audioFeature['tempo'],
                                             limit=numOfSongs+1)

    # Print or process the recommendations as needed
    if recommendations['tracks']:
        print("Recommended Tracks:")

        # Extract the track URIs from the recommendations
        trackURIs = [track['uri'] for track in recommendations['tracks']]

        for track in recommendations['tracks']:
            if track['uri'] not in songURIs:
                artists = ', '.join([artist['name'] for artist in track['artists']])
                print(f"{track['name']} by {artists}")

        # Create a new playlist and add the tracks to it
        playlistID = playlist_manager.createPlaylist(sp)
        playlist_manager.addSongsToPlaylist(sp, playlistID, trackURIs)

        print(f"Playlist was created and tracks added successfully.")
    else:
        print("No recommendations found.")