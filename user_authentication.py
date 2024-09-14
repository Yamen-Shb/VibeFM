import os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

# Load environment variables from .env file
load_dotenv()

# Load environment variables
client_id = os.environ.get("SPOTIPY_CLIENT_ID")
client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI")

# Load Genius and Last.fm API keys from environment variables
# genius_client_id = os.environ.get('GENIUS_CLIENT_ID')
# genius_client_secret = os.environ.get('GENIUS_CLIENT_SECRET')
# lastfm_api_key = os.environ.get('LASTFM_API_KEY')

# Define the Spotify OAuth scope
scope = 'user-library-read playlist-modify-private user-read-recently-played user-top-read user-read-playback-state user-read-currently-playing playlist-modify-public playlist-modify-private playlist-read-private'

# Set a custom cache path
cache_path = "/tmp/.cache"  # Use /tmp for Vercel's ephemeral filesystem

# Create the SpotifyOAuth object
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    show_dialog=True,
    cache_path=cache_path,
    requests_timeout=30
)

# Function to get the Spotify authorization URL
def get_auth_url():
    return sp_oauth.get_authorize_url()

# Function to exchange the authorization code for an access token and refresh token
def get_tokens(code):
    token_info = sp_oauth.get_access_token(code)
    return token_info

# Function to clear the cache
def clear_cache():
    if os.path.exists(cache_path):
        os.remove(cache_path)