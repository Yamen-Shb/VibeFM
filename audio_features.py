import spotify_utils


def getAudioFeatures(sp, track_id):
    # Get audio features for a track
    print(track_id)
    print([track_id])
    features = sp.audio_features([track_id])

    if not features:
        return None

    features = features[0]

    audioData = {
            'tempo': features['tempo'],
            'energy': features['energy'],
            'danceability': features['danceability'],
            'valence': features['valence'],
            'acousticness': features['acousticness'],
            'instrumentalness': features['instrumentalness'],
            # Add more features as needed
    }

    return audioData


def printAudioFeatures(sp, trackID):
    audioFeatures = getAudioFeatures(sp, trackID)

    if audioFeatures:
        print(f"Audio Features for Track {trackID}:")
        for feature, value in audioFeatures.items():
            print(f"{feature.capitalize()}: {value}")
    else:
        print(f"No audio features found for track with ID {trackID}")
        return None


def calculateAvgAudioFeatures(sp, songURIs):
    # Initialize variables to store the sum of audio features
    totalTempo = 0
    totalEnergy = 0
    totalDanceability = 0
    totalValence = 0
    totalAcousticness = 0
    totalInstrumentalness = 0

    # Iterate through each song URI and get its audio features
    for uri in songURIs:
        audioFeatures = getAudioFeatures(sp, uri)

        if audioFeatures:
            # Accumulate the audio features
            totalTempo += audioFeatures['tempo']
            totalEnergy += audioFeatures['energy']
            totalDanceability += audioFeatures['danceability']
            totalValence += audioFeatures['valence']
            totalAcousticness += audioFeatures['acousticness']
            totalInstrumentalness += audioFeatures['instrumentalness']

    # Calculate the average audio features
    numSongs = len(songURIs)
    if numSongs > 0:
        averageAudioFeatures = {
            'tempo': totalTempo / numSongs,
            'energy': totalEnergy / numSongs,
            'danceability': totalDanceability / numSongs,
            'valence': totalValence / numSongs,
            'acousticness': totalAcousticness / numSongs,
            'instrumentalness': totalInstrumentalness / numSongs,
            # Add more features as needed
        }
        return averageAudioFeatures
    else:
        print("No valid songs to calculate average features.")
        return None