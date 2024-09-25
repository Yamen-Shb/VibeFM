import os
from flask import session
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables from .env file
load_dotenv()

# Load environment variables
client_id = os.environ.get("SPOTIPY_CLIENT_ID")
client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI")

# Define the Spotify OAuth scope
scope = 'user-library-read playlist-modify-private user-read-recently-played user-top-read user-read-playback-state user-read-currently-playing playlist-modify-public playlist-modify-private playlist-read-private'

# Set a custom cache path
cache_path = "/tmp/.cache"  # Use /tmp for Vercel's ephemeral filesystem

# Function to get a session-specific cache path
def session_cache_path():
    return f"{cache_path}-{session.get('uuid')}"

# Create the SpotifyOAuth object (move this inside a function)
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        show_dialog=True,
        cache_path=session_cache_path(),
        requests_timeout=30
    )

# Function to get the Spotify authorization URL
def get_auth_url():
    return create_spotify_oauth().get_authorize_url()

# Function to exchange the authorization code for an access token and refresh token
def get_tokens(code):
    token_info = create_spotify_oauth().get_access_token(code)
    return token_info

# Function to clear the cache
def clear_cache():
    if os.path.exists(session_cache_path()):
        os.remove(session_cache_path())