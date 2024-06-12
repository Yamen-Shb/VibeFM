import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import recommend_songs
import user_stats
import playlist_manager
import audio_features
import spotify_utils
from flask import Flask, render_template, request, jsonify

# Load environment variables from .env file
load_dotenv()

# Set your Spotify API credentials from environment variables
client_id = os.getenv("SPOTIPY_CLIENT_ID")
client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")
username = os.getenv("USERNAME")

# Initialize the Spotify client with user authorization
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope='user-library-read playlist-modify-private user-read-recently-played '
          'user-top-read user-read-playback-state user-read-currently-playing '
          'playlist-modify-public playlist-modify-private playlist-read-private',
    requests_timeout=30
))

# Load Genius and Last.fm API keys from environment variables
genius_client_id = os.getenv('GENIUS_CLIENT_ID')
genius_client_secret = os.getenv('GENIUS_CLIENT_SECRET')
lastfm_api_key = os.getenv('LASTFM_API_KEY')

# Define a cache to store artist information and genres
artistCache = {}

def main():
    import cProfile
    import pstats
    with cProfile.Profile() as pr:
        recommend_songs.recommendBasedOnSeed(sp, username)
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()

if __name__ == '__main__':
    main()
