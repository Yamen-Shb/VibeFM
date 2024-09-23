import os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Load environment variables
client_id = os.environ.get("SPOTIPY_CLIENT_ID")
client_secret = os.environ.get("SPOTIPY_CLIENT_SECRET")
redirect_uri = os.environ.get("SPOTIPY_REDIRECT_URI")

# Log environment variables (be careful not to log sensitive information in production)
logger.debug(f"Client ID: {client_id}")
logger.debug(f"Redirect URI: {redirect_uri}")

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
    auth_url = sp_oauth.get_authorize_url()
    logger.debug(f"Generated auth URL: {auth_url}")
    return auth_url

# Function to exchange the authorization code for an access token and refresh token
def get_tokens(code):
    try:
        token_info = sp_oauth.get_access_token(code)
        logger.debug("Successfully retrieved token info")
        return token_info
    except Exception as e:
        logger.error(f"Error getting tokens: {str(e)}")
        return None

# Function to clear the cache
def clear_cache():
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            logger.debug("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
    else:
        logger.debug("No cache file found to clear")

# Function to check if all required environment variables are set
def check_env_variables():
    required_vars = ["SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET", "SPOTIPY_REDIRECT_URI"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True

# Call this function before initializing SpotifyOAuth
if not check_env_variables():
    raise EnvironmentError("Missing required environment variables")