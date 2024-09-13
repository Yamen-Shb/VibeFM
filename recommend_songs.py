import audio_features
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
            playlist = sp.playlist(playlistID)
            actualSongCount = playlist['tracks']['total']
            
            return {
                "playlist_id": playlistID, 
                "track_uris": trackURIs,
                "actual_song_count": actualSongCount  
            }
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
    maxAttempts = 20 

    if len(songURIs) == 1:
        numOfSongs +=1
    
    
    while len(generatedTracks) < numOfSongs and maxAttempts > 0:
        remaining = numOfSongs - len(generatedTracks)
        limit = min(remaining, 100)
        
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
        
        maxAttempts -= 1
    
    return generatedTracks[:numOfSongs]