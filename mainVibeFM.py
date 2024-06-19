import os
from dotenv import load_dotenv
import spotipy
from flask import Flask, render_template, request, redirect, session
import user_authentication

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


@app.route('/top-artists')
def top_artists():
    # Call the backend to get top artists
    return render_template('top_artists.html')


@app.route('/generate-songs')
def generate_songs():
    # Call the backend to generate songs
    return render_template('generate_songs.html')


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

#def main():
#    import cProfile
#    import pstats
#    with cProfile.Profile() as pr:
#        recommend_songs.recommendBasedOnSeed(sp, username)
#    stats = pstats.Stats(pr)
#    stats.sort_stats(pstats.SortKey.TIME)
#    stats.print_stats()

#if __name__ == '__main__':
#    main()
