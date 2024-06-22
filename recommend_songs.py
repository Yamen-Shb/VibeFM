import audio_features
import spotify_utils
import playlist_manager
import random

def recommendBasedOnSeed(sp, songURIs, numOfSongs, playlistName):
    if not songURIs:
        return {"error": "No song URIs provided"}

    # Calculate average audio features if more than one song is selected
    if len(songURIs) > 1:
        audioFeature = audio_features.calculateAvgAudioFeatures(sp, songURIs)
    else:
        # Get audio features for a single song
        audioFeature = audio_features.getAudioFeatures(sp, songURIs[0])

    if not audioFeature:
        return {"error": "No audio features found"}

    recommendations = fetchRecommendations(sp, audioFeature, numOfSongs, songURIs)

    if recommendations:
        # Extract the track URIs from the recommendations
        trackURIs = [track['uri'] for track in recommendations]

        if trackURIs:
            # Create a new playlist and add the unique tracks to it
            playlistID = playlist_manager.createPlaylist(sp, playlistName)
            playlist_manager.addSongsToPlaylist(sp, playlistID, trackURIs)
            return {"playlist_id": playlistID, "track_uris": trackURIs}
        else:
            return {"error": "No unique tracks to add to the playlist"}
    else:
        return {"error": "No recommendations found"}


def fetchRecommendations(sp, audioFeature, numOfSongs, songURIs):
    if len(songURIs) <= 5:
        usedURIs = songURIs
    else:
        usedURIs = random.sample(songURIs, 5)
    
    generatedTracks = []
    maxAttempts = 10  # Maximum number of attempts to reach the desired number of songs
    
    for _ in range(maxAttempts):
        if len(generatedTracks) >= numOfSongs:
            break
        
        limit = min(numOfSongs - len(generatedTracks), 100)
        recommendations = sp.recommendations(
            seed_tracks=usedURIs,
            target_acousticness=audioFeature['acousticness'],
            target_danceability=audioFeature['danceability'],
            target_energy=audioFeature['energy'],
            target_valence=audioFeature['valence'],
            target_tempo=audioFeature['tempo'],
            limit=limit
        )
        
        newTracks = [track for track in recommendations['tracks'] 
                     if track['uri'] not in songURIs and 
                     track['uri'] not in [t['uri'] for t in generatedTracks]]
        
        generatedTracks.extend(newTracks)
        
        if len(songURIs) > 5:
            usedURIs = random.sample(songURIs, 5)
    
    return generatedTracks[:numOfSongs]  # Ensure we return exactly numOfSongs tracks