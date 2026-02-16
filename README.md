# 🎵 VibeFM

A full-stack web application that connects to the Spotify API to give users insight into their listening habits and intelligently organize their music library by genre.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.3-lightgrey)
![Spotipy](https://img.shields.io/badge/Spotipy-2.24.0-green)
![Deployed on](https://img.shields.io/badge/Deployed%20on-Vercel-black)

---

## 📖 Overview

VibeFM lets Spotify users:

- **View Top Tracks** — See your 50 most-listened-to tracks across three time windows (4 weeks, 6 months, 1 year).
- **View Top Artists** — Discover your 50 most-listened-to artists across the same time ranges.
- **Sort Songs by Genre** — Scan your Liked Songs or any saved playlist, filter tracks by a target genre, and automatically create a new Spotify playlist containing only the matching songs.

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Spotify Integration** | [Spotipy](https://spotipy.readthedocs.io/) (Python wrapper for the Spotify Web API) |
| **Authentication** | OAuth 2.0 Authorization Code Flow via Spotify |
| **Deployment** | Vercel (Serverless Python) |
| **Environment Management** | python-dotenv |

## 🏗 Architecture

```
VibeFM/
├── mainVibeFM.py            # Flask application entry point & route definitions
├── user_authentication.py   # Spotify OAuth 2.0 flow (auth URL, token exchange, cache)
├── user_stats.py            # Fetches top tracks and top artists from Spotify API
├── playlist_manager.py      # Playlist creation, track fetching, genre-based sorting
├── spotify_utils.py         # Utility functions (playlist lookup, song search)
├── templates/               # Jinja2 HTML templates
│   ├── index.html           # Landing / login page
│   ├── dashboard.html       # Main dashboard
│   ├── top_tracks.html      # Top tracks view
│   ├── top_artists.html     # Top artists view
│   └── sort_songs.html      # Sort songs form & results
├── static/
│   ├── styles/              # CSS (login_styles.css, main_styles.css)
│   └── scripts/             # Client-side JS (top_tracks.js, top_artists.js, sort_songs.js)
├── requirements.txt
├── vercel.json              # Vercel deployment configuration
└── .env                     # Environment variables (not committed)
```

## 🔐 Spotify API Integration

### Authentication

VibeFM uses the **OAuth 2.0 Authorization Code Flow**:

1. The user clicks "Log in with Spotify" and is redirected to Spotify's authorization page.
2. After granting permissions, Spotify redirects back with an authorization code.
3. The server exchanges the code for an access token and refresh token.
4. Tokens are stored in the Flask session for subsequent API calls.

Session-specific cache files (stored in `/tmp`) ensure that concurrent users don't share token state — an important consideration for serverless environments like Vercel.

### Scopes Requested

| Scope | Purpose |
|---|---|
| `user-top-read` | Retrieve top tracks and artists |
| `user-library-read` | Access liked/saved songs |
| `playlist-read-private` | List user's private playlists |
| `playlist-modify-public` / `playlist-modify-private` | Create and populate new playlists |
| `user-read-playback-state` / `user-read-currently-playing` | Reserved for future playback features |
| `user-read-recently-played` | Reserved for future listening history features |

### Genre-Based Sorting Algorithm

The Sort Songs feature works as follows:

1. Fetches tracks from the user's Liked Songs or a selected playlist.
2. For each track, resolves the artist(s) and retrieves their associated genres from the Spotify API.
3. Artist genre data is cached in-memory to minimize redundant API calls.
4. Tracks whose artist genres match the user-specified target genre (case-insensitive substring match) are collected.
5. A new playlist is created on the user's Spotify account and populated with matching tracks (batched in groups of 100 per Spotify's API limit).

## ⚠️ Known API Deprecations & Limitations

### Spotify API Deprecations

- **Audio Features & Audio Analysis endpoints** — Spotify deprecated these endpoints (November 2024). VibeFM does not currently rely on them, but any future feature that requires track-level audio attributes (tempo, energy, danceability, etc.) would be affected. Genre sorting relies on *artist-level* genres instead, which remains supported.

### Current Limitations

- **Genre data is artist-level, not track-level.** Spotify does not assign genres directly to individual tracks. VibeFM infers a track's genre from its artist(s), which can be imprecise for artists who span multiple genres.
- **No background token refresh flow.** Tokens are refreshed via re-authentication to keep the implementation simple and explicit for a portfolio context.
- **Rate limiting.** The genre-sorting feature makes one API call per unique artist. For large libraries, this can approach Spotify's rate limits. The in-memory artist cache mitigates this, but a persistent cache (e.g., Redis) would be more robust.
- **Serverless session storage.** Flask sessions are stored client-side in signed cookies. In a production environment, a server-side session store (e.g., Redis, database) would be more secure and scalable.
- **No pagination beyond 50 for top tracks/artists.** The Spotify API caps `current_user_top_tracks` and `current_user_top_artists` at 50 items, which is the current hard limit.
- **Sort Songs does not stream progress to the client.** The sorting operation runs synchronously on the server; for very large playlists, the HTTP request may time out on Vercel's serverless platform (10-second function limit on the free tier).

## 🎨 Design Decisions

- **Vanilla JavaScript over a frontend framework.** The application's UI is relatively straightforward (tab switching, form submission, dynamic list rendering). Using vanilla JS keeps the bundle size at zero and avoids build-step complexity, which is appropriate for the project's scope.
- **Server-rendered templates with AJAX data loading.** Page shells are rendered via Jinja2 on the server, while dynamic content (tracks, artists, playlists) is fetched asynchronously via `fetch()` calls to JSON API endpoints. This provides a responsive feel without the overhead of a full SPA.
- **Modular Python backend.** Business logic is separated into focused modules (`user_stats`, `playlist_manager`, `spotify_utils`, `user_authentication`), keeping `mainVibeFM.py` as a thin routing layer.
- **Spotify-inspired UI.** The dark theme, green accent color (#1db954), and card-based layout intentionally mirror Spotify's visual language to create a familiar experience for users.
- **Vercel deployment.** Chosen for zero-config Python serverless hosting with automatic HTTPS and global CDN for static assets.

## 🚀 Getting Started

### Prerequisites

- Python 3.x
- A [Spotify Developer](https://developer.spotify.com/dashboard) application (Client ID, Client Secret, Redirect URI)

### Setup

```bash
# Clone the repository
git clone https://github.com/<your-username>/VibeFM.git
cd VibeFM

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file with your Spotify credentials
cat <<EOF > .env
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:5000/callback
SECRET_KEY=$(python -c "import os; print(os.urandom(24).hex())")
EOF

# Run the development server
python mainVibeFM.py
```

Navigate to `http://localhost:5000` and log in with your Spotify account.

## 📄 License

This project is for educational and portfolio purposes.
