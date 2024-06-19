import spotify_utils

# Get the user's top tracks
def topTracks(sp, timeRange):
    results = sp.current_user_top_tracks(limit=50, time_range=timeRange)
    topTracks = []

    if 'items' in results and results['items']:
        topTracks.extend(results['items'])

    tracksInfo = [
        {
            'name': track['name'],
            'artists': ', '.join(artist['name'] for artist in track['artists'])
        }
        for track in topTracks
    ]

    return tracksInfo


def topArtists(sp, timeRange):
    results = sp.current_user_top_tracks(limit=50, time_range=timeRange)
    topArtists = []

    if 'items' in results and results['items']:
        topArtists.extend(results['items'])

    topArtistsInfo = [
        {
            'name': artist['name'],
        }
        for artist in topArtists
    ]

    return topArtistsInfo