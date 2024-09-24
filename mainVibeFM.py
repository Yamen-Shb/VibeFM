from functools import wraps
import os
from dotenv import load_dotenv
import spotipy
from flask import Flask, render_template, request, redirect, session, jsonify
import user_authentication
import user_stats
import spotify_utils
import recommend_songs
import playlist_manager

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
if not app.secret_key:
    raise ValueError("No SECRET_KEY set for Flask application")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    # Generate a unique state for CSRF protection
    state = secrets.token_urlsafe(16)
    session['spotify_auth_state'] = state
    
    # Redirect the user to the Spotify authentication URL
    auth_url = user_authentication.get_auth_url(state)
    return redirect(auth_url)

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Clear any cached tokens
    user_authentication.clear_cache()
    return redirect('/')

@app.route('/callback')
def callback():
    # Verify the state to prevent CSRF attacks
    if request.args.get('state') != session.get('spotify_auth_state'):
        return 'State mismatch. Possible CSRF attack.', 400
    
    # Handle the redirect from Spotify after authentication
    code = request.args.get('code')
    token_info = user_authentication.get_tokens(code)
    
    if not token_info:
        return 'Failed to get token', 400
    
    # Store the tokens in the user's session
    session['access_token'] = token_info['access_token']
    session['refresh_token'] = token_info.get('refresh_token')
    session['token_expiry'] = token_info['expires_at']

    # Initialize the Spotify client with the user's access token
    sp = spotipy.Spotify(auth=session['access_token'])

    # Retrieve the user's information from Spotify
    user_info = sp.current_user()
    session['name'] = user_info.get('display_name') or user_info['id']

    # Redirect the user to the main application page
    return redirect('/app')

@app.route('/app')
@login_required
def app_route():
    return render_template('dashboard.html', name=session.get('name'))

@app.route('/top-tracks')
@login_required
def top_tracks():
    return render_template('top_tracks.html')

@app.route('/top-tracks/<time_range>')
@login_required
def get_top_tracks(time_range):
    sp = spotipy.Spotify(auth=session['access_token'])
    tracks = user_stats.getTopTracks(sp, time_range)
    return jsonify(tracks)


@app.route('/top-artists')
@login_required
def top_artists():
    # Call the backend to get top artists
    return render_template('top_artists.html')


@app.route('/top-artists/<time_range>')
@login_required
def get_top_artists(time_range):
    access_token = session.get('access_token')
    if access_token is None:
        return redirect('/login')

    sp = spotipy.Spotify(auth=access_token)
    artists = user_stats.getTopArtists(sp, time_range)

    return jsonify(artists)


@app.route('/generate-songs')
@login_required
def generate_songs():
    # Call the backend to generate songs
    return render_template('generate_songs.html')


@app.route('/search_song', methods=['POST'])
@login_required
def search_song():
    access_token = session.get('access_token')
    if access_token is None:
        return jsonify({"error": "User not authenticated"}), 401

    sp = spotipy.Spotify(auth=access_token)
    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({"error": "Missing query"}), 400

    result = spotify_utils.searchForSong(sp, query)
    return jsonify(result)


@app.route('/get_user_playlists')
@login_required
def get_user_playlists():
    access_token = session.get('access_token')
    if access_token is None:
        return jsonify({"error": "User not authenticated"}), 401

    sp = spotipy.Spotify(auth=access_token)
    playlists = sp.current_user_playlists()
    
    playlist_data = [{"name": playlist['name'], "uri": playlist['uri']} for playlist in playlists['items']]
    return jsonify(playlist_data)


@app.route('/get_playlist_songs', methods=['POST'])
@login_required
def get_playlist_songs():
    access_token = session.get('access_token')
    if access_token is None:
        return jsonify({"error": "User not authenticated"}), 401

    sp = spotipy.Spotify(auth=access_token)
    data = request.json
    playlistURI = data.get('playlist_uri')

    if not playlistURI:
        return jsonify({"error": "Missing playlist URI"}), 400

    result = playlist_manager.getPlaylistSongURIs(sp, playlistURI)
    return jsonify(result)

@app.route('/generate_playlist', methods=['POST'])
@login_required
def generate_playlist():
    access_token = session.get('access_token')
    if access_token is None:
        return jsonify({"error": "User not authenticated"}), 401

    sp = spotipy.Spotify(auth=access_token)
    data = request.json
    songURIs = data.get('song_uris')
    numOfSongs = int(data.get('num_of_songs'))
    playlistName = data.get('playlist_name')


    if not songURIs or not numOfSongs or not playlistName:
        return jsonify({"error": "Missing parameters"}), 400

    result = recommend_songs.recommendBasedOnSeed(sp, songURIs, numOfSongs, playlistName)
    
    if 'error' in result:
        return jsonify(result), 500

    # Retrieve the cover image URL of the created playlist
    playlist_id = result.get('playlist_id')
    if playlist_id:
        playlist = sp.playlist(playlist_id)
        cover_url = playlist['images'][0]['url'] if playlist['images'] else None
        result['coverUrl'] = cover_url

    return jsonify(result)


@app.route('/sort-songs')
@login_required
def sort_songs():
    # Call the backend to sort songs
    return render_template('sort_songs.html')


@app.route('/sort_songs_action', methods=['POST'])
@login_required
def sort_songs_action():
    access_token = session.get('access_token')
    if access_token is None:
        return jsonify({"error": "User not authenticated"}), 401

    sp = spotipy.Spotify(auth=access_token)
    data = request.json
    choice = data.get('choice')  # 'liked' or 'playlist'
    target_genre = data.get('targetGenre')
    playlist_name = data.get('playlistName')
    max_tracks = data.get('maxTracks')

    if not choice or not target_genre or not playlist_name:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        result = playlist_manager.sortSongs(sp, choice, target_genre, playlist_name, max_tracks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if 'error' in result:
        return jsonify(result), 500

    # Retrieve the cover image URL of the created playlist
    playlist_id = result.get('playlist_id')
    if playlist_id:
        playlist = sp.playlist(playlist_id)
        cover_url = playlist['images'][0]['url'] if playlist['images'] else None
        result['coverUrl'] = cover_url

    return jsonify(result)

@app.before_request
def check_token_expiration():
    if 'access_token' in session and 'token_expiry' in session:
        now = int(time.time())
        if session['token_expiry'] - now < 60:
            token_info = user_authentication.refresh_token(session['refresh_token'])
            if token_info:
                session['access_token'] = token_info['access_token']
                session['token_expiry'] = token_info['expires_at']
            else:
                session.clear()
                return redirect('/login')

if __name__ == '__main__':
    app.run()
