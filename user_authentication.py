import os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import logging
from flask import session, request
import secrets

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Load environment variables
client_id = os.environ.get("SPOTIPY_CLIENT_ID")
client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI")

# Define the Spotify OAuth scope
scope = 'user-library-read playlist-modify-private user-read-recently-played user-top-read user-read-playback-state user-read-currently-playing playlist-modify-public playlist-modify-private playlist-read-private'

# Function to create a new SpotifyOAuth object for each session
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        show_dialog=True,
        cache_path=None  # Don't use cache_path to avoid shared caching
    )

# Function to get the Spotify authorization URL
def get_auth_url():
    # Generate a unique state for CSRF protection
    state = secrets.token_urlsafe(16)
    session['spotify_auth_state'] = state
    
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url(state=state)
    logger.debug(f"Generated auth URL: {auth_url}")
    return auth_url

# Function to exchange the authorization code for an access token and refresh token
def get_tokens(code):
    try:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.get_access_token(code, check_cache=False)
        if token_info:
            # Store tokens in session
            session['access_token'] = token_info['access_token']
            session['refresh_token'] = token_info['refresh_token']
            session['expires_at'] = token_info['expires_at']
            logger.debug("Successfully retrieved and stored token info in session")
        return token_info
    except Exception as e:
        logger.error(f"Error getting tokens: {str(e)}")
        return None

# Function to clear the session
def clear_session():
    session.clear()
    logger.debug("Session cleared")

# Function to check if the user is authenticated
def is_authenticated():
    return 'access_token' in session

# Function to get the current user's access token
def get_access_token():
    if not is_authenticated():
        return None
    
    if session['expires_at'] < int(time.time()):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(session['refresh_token'])
        session['access_token'] = token_info['access_token']
        session['expires_at'] = token_info['expires_at']
    
    return session['access_token']

# Function to handle logout
def logout():
    clear_session()
    # Optionally, revoke the Spotify token here

# Function to check if all required environment variables are set
def check_env_variables():
    required_vars = ["SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET", "SPOTIPY_REDIRECT_URI"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True

# Call this function before initializing the app
if not check_env_variables():
    raise EnvironmentError("Missing required environment variables")