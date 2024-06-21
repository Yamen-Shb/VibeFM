import os
from dotenv import load_dotenv
import spotipy
from flask import Flask, render_template, request, redirect, session, jsonify
import user_authentication
import user_stats
import spotify_utils
import recommend_songs
import playlist_manager

# Define a cache to store artist information and genres
artistCache = {}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    # Redirect the user to the Spotify authentication URL
    auth_url = user_authentication.get_auth_url()
    return redirect(auth_url)

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
    access_token = session.get('access_token')
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
    print("Received search_song request")
    access_token = session.get('access_token')
    if access_token is None:
        print("No access token")
        return jsonify({"error": "User not authenticated"}), 401

    sp = spotipy.Spotify(auth=access_token)
    data = request.json
    query = data.get('query')
    print(f"Searching for query: {query}")

    if not query:
        print("No query provided")
        return jsonify({"error": "Missing query"}), 400

    result = spotify_utils.searchForSong(sp, query)
    print(f"Search result: {result}")
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
    print("Received generate_playlist request")
    access_token = session.get('access_token')
    if access_token is None:
        print("No access token")
        return jsonify({"error": "User not authenticated"}), 401

    sp = spotipy.Spotify(auth=access_token)
    data = request.json
    print(f"Received data: {data}")
    songURIs = data.get('song_uris')
    numOfSongs = int(data.get('num_of_songs'))
    playlistName = data.get('playlist_name')

    print(f"songURIs: {songURIs}")
    print(f"numOfSongs: {numOfSongs}")
    print(f"playlistName: {playlistName}")

    if not songURIs or not numOfSongs or not playlistName:
        print("Missing parameters")
        return jsonify({"error": "Missing parameters"}), 400

    result = recommend_songs.recommendBasedOnSeed(sp, songURIs, numOfSongs, playlistName)
    print(f"Recommendation result: {result}")
    return jsonify(result)


@app.route('/sort-songs')
def sort_songs():
    # Call the backend to sort songs
    return render_template('sort_songs.html')


@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    # Clear the Spotify OAuth cache
    user_authentication.clear_cache()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
