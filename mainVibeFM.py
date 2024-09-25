import os
from dotenv import load_dotenv
import spotipy
from flask import Flask, render_template, request, redirect, session, jsonify
import user_authentication
import user_stats
import spotify_utils
import recommend_songs
import playlist_manager

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    session['uuid'] = os.urandom(24).hex()

    # Redirect the user to the Spotify authentication URL
    auth_url = user_authentication.get_auth_url()
    return redirect(auth_url)

@app.route('/logout')
def logout():
    session.clear()
    user_authentication.clear_cache()
    return redirect('/')

@app.route('/callback')
def callback():
    # Handle the redirect from Spotify after authentication
    code = request.args.get('code')
    token_info = user_authentication.get_tokens(code)
    access_token = token_info['access_token']
    refresh_token = token_info.get('refresh_token')

    # Store the tokens in the user's session
    session['access_token'] = access_token
    session['refresh_token'] = refresh_token

    # Initialize the Spotify client with the user's access token
    sp = spotipy.Spotify(auth=access_token)

    # Retrieve the user's information from Spotify
    user_info = sp.current_user()
    if 'display_name' in user_info and user_info['display_name']:
        name = user_info['display_name']
    else:
        name = user_info['id']

    # Store the username in the session
    session['name'] = name

    # Redirect the user to the main application page
    return redirect('/app')

@app.route('/app')
def app_route():
    # Check if the user is authenticated
    access_token = get_token()
    if access_token is None:
        return redirect('/login')

    # Initialize the Spotify client with the user's access token
    sp = spotipy.Spotify(auth=access_token)

    # Retrieve the username from the session
    name = session.get('name')

    return render_template('dashboard.html', name=name)


@app.route('/top-tracks')
def top_tracks():
    # Call the backend to get top tracks
    return render_template('top_tracks.html')

@app.route('/top-tracks/<time_range>')
def get_top_tracks(time_range):
    access_token = session.get('access_token')
    if access_token is None:
        return redirect('/login')

    sp = spotipy.Spotify(auth=access_token)
    tracks = user_stats.getTopTracks(sp, time_range)
    
    return jsonify(tracks)


@app.route('/top-artists')
def top_artists():
    # Call the backend to get top artists
    return render_template('top_artists.html')


@app.route('/top-artists/<time_range>')
def get_top_artists(time_range):
    access_token = session.get('access_token')
    if access_token is None:
        return redirect('/login')

    sp = spotipy.Spotify(auth=access_token)
    artists = user_stats.getTopArtists(sp, time_range)

    return jsonify(artists)


@app.route('/generate-songs')
def generate_songs():
    # Call the backend to generate songs
    return render_template('generate_songs.html')


@app.route('/search_song', methods=['POST'])
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
def get_user_playlists():
    access_token = session.get('access_token')
    if access_token is None:
        return jsonify({"error": "User not authenticated"}), 401

    sp = spotipy.Spotify(auth=access_token)
    playlists = sp.current_user_playlists()
    
    playlist_data = [{"name": playlist['name'], "uri": playlist['uri']} for playlist in playlists['items']]
    return jsonify(playlist_data)


@app.route('/get_playlist_songs', methods=['POST'])
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
def sort_songs():
    # Call the backend to sort songs
    return render_template('sort_songs.html')


@app.route('/sort_songs_action', methods=['POST'])
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


if __name__ == '__main__':
    app.run(debug=True)