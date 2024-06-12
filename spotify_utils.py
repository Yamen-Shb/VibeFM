import os
import spotipy
import chardet
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth


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
            return firstTrackURI
        else:
            return None
    except Exception as e:
        print(f"Error during song search: {e}")
        return None


def currentlyPlayingTrack(sp):
    results = sp.currently_playing()

    if results is not None:
        currently_playing_track = results['item']
        print(
            f"Currently playing song: {currently_playing_track['name']} "
            f"by {', '.join(artist['name'] for artist in currently_playing_track['artists'])}")
    else:
        print("No songs currently playing.")

    if currently_playing_track:
        # Return the track_id
        return currently_playing_track['id']
    else:
        return None


def mostRecentlyPlayedTrack(sp):
    # Get the user's recently played tracks
    results = sp.current_user_recently_played(limit=1)

    if results['items']:
        most_recent_track = results['items'][0]['track']
        print(
            f"Most Recently Played Song: {most_recent_track['name']} "
            f"by {', '.join(artist['name'] for artist in most_recent_track['artists'])}")
    else:
        print("No recently played songs found.")


def artistsTopTracksOrAlbums(sp):
    counter = 0

    # Artist name you want to search for
    artist_name = input("Please search for an artist: ")

    # Search for the artist
    results = sp.search(q=artist_name, type="artist", limit=1)

    # Check if search results were found
    if results["artists"]["total"] > 0:
        artist = results["artists"]["items"][0]
        artist_uri = artist["uri"]
        results = sp.artist_top_tracks(artist_uri, country='US')

    # Extract and print the track names
    for track in results['tracks']:
        counter += 1
        print(str(counter) + '. ' + track['name'])
    else:
        if counter == 10:
            print("artist genres:", artist["genres"])
        else:
            print(f"No results found for '{artist_name}'")


def detect_encoding(text):
    try:
        result = chardet.detect(text.encode('latin-1'))
        return result['encoding']
    except UnicodeEncodeError:
        # If there is an encoding error, return 'utf-8'
        return 'utf-8'
