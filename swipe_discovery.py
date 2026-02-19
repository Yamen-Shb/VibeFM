import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

LASTFM_API_KEY = os.environ.get("LAST_FM_API_KEY")
LASTFM_BASE_URL = "http://ws.audioscrobbler.com/2.0/"
DEEZER_SEARCH_URL = "https://api.deezer.com/search"


def get_random_liked_seeds(sp, count=5):
    """
    Pick random liked songs to use as seeds.
    Falls back to top tracks if user has no liked songs.
    """
    results = sp.current_user_saved_tracks(limit=1, offset=0)
    total = results.get('total', 0)

    if total == 0:
        return _get_top_track_seeds(sp, count)

    sample_size = min(count, total)
    offsets = random.sample(range(total), sample_size)

    seeds = []
    for offset in offsets:
        result = sp.current_user_saved_tracks(limit=1, offset=offset)
        if result['items']:
            track = result['items'][0]['track']
            seeds.append({
                'id': track['id'],
                'uri': track['uri'],
                'name': track['name'],
                'artist': track['artists'][0]['name']
            })

    return seeds


def _get_top_track_seeds(sp, count=5):
    """
    Fallback seed source: user's top tracks.
    """
    results = sp.current_user_top_tracks(limit=count, time_range='medium_term')
    seeds = []
    for track in results.get('items', []):
        seeds.append({
            'id': track['id'],
            'uri': track['uri'],
            'name': track['name'],
            'artist': track['artists'][0]['name']
        })
    return seeds


def get_similar_tracks_lastfm(seed_tracks, tracks_per_seed=20):
    """
    Fetch similar tracks from Last.fm for multiple seed tracks.
    Returns deduplicated list of dicts with track name, artist name.
    """
    all_similar = []
    seen = set()

    for seed in seed_tracks:
        params = {
            "method": "track.getsimilar",
            "artist": seed['artist'],
            "track": seed['name'],
            "api_key": LASTFM_API_KEY,
            "format": "json",
            "limit": tracks_per_seed
        }

        try:
            response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
            data = response.json()

            if 'similartracks' in data and 'track' in data['similartracks']:
                for track in data['similartracks']['track']:
                    key = (track['name'].lower(), track['artist']['name'].lower())
                    if key not in seen:
                        seen.add(key)
                        all_similar.append({
                            'name': track['name'],
                            'artist': track['artist']['name'],
                            'lastfm_url': track.get('url', ''),
                            'playcount': int(track.get('playcount', 0)),
                            'match': float(track.get('match', 0)),
                        })
        except (requests.RequestException, KeyError, ValueError):
            continue

    return all_similar


def get_similar_tracks_for_seed(seed, tracks_per_seed=20):
    """
    Fetch similar tracks from Last.fm for a single seed track.
    Returns a list of track dicts.
    """
    params = {
        "method": "track.getsimilar",
        "artist": seed['artist'],
        "track": seed['name'],
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": tracks_per_seed
    }

    results = []
    try:
        response = requests.get(LASTFM_BASE_URL, params=params, timeout=10)
        data = response.json()

        if 'similartracks' in data and 'track' in data['similartracks']:
            for track in data['similartracks']['track']:
                results.append({
                    'name': track['name'],
                    'artist': track['artist']['name'],
                    'lastfm_url': track.get('url', ''),
                    'playcount': int(track.get('playcount', 0)),
                    'match': float(track.get('match', 0)),
                })
    except (requests.RequestException, KeyError, ValueError):
        pass

    return results


def enrich_with_album_art(tracks, batch_size=5):
    """
    Fetch album art for tracks using Last.fm track.getInfo.
    The getSimilar endpoint returns generic placeholder images,
    so we need getInfo for real album artwork.
    Processes in batches to avoid being too slow.
    """
    for track in tracks:
        params = {
            "method": "track.getInfo",
            "artist": track['artist'],
            "track": track['name'],
            "api_key": LASTFM_API_KEY,
            "format": "json",
        }

        try:
            response = requests.get(LASTFM_BASE_URL, params=params, timeout=5)
            data = response.json()

            if 'track' in data:
                info = data['track']
                # Get album art if available
                album_art = None
                album_name = None
                if 'album' in info and 'image' in info['album']:
                    images = info['album']['image']
                    # Prefer extralarge or large
                    for img in reversed(images):
                        if img['#text']:
                            album_art = img['#text']
                            break
                    album_name = info['album'].get('title', '')

                track['album_art'] = album_art
                track['album'] = album_name or ''
            else:
                track['album_art'] = None
                track['album'] = ''
        except (requests.RequestException, KeyError, ValueError):
            track['album_art'] = None
            track['album'] = ''

    return tracks


def enrich_with_deezer(tracks):
    """
    Enrich tracks with album art and 30-second preview URLs from Deezer.
    Much faster than Last.fm track.getInfo since Deezer search returns
    album art + preview in a single call per track. No API key needed.
    """
    for track in tracks:
        try:
            query = f"{track['name']} {track['artist']}"
            response = requests.get(
                DEEZER_SEARCH_URL,
                params={"q": query, "limit": 1},
                timeout=5
            )
            data = response.json()

            if data.get('data') and len(data['data']) > 0:
                result = data['data'][0]
                track['album_art'] = (
                    result.get('album', {}).get('cover_big')
                    or result.get('album', {}).get('cover_medium')
                )
                track['album'] = result.get('album', {}).get('title', '')
                track['preview_url'] = result.get('preview') or None
            else:
                track['album_art'] = None
                track['album'] = ''
                track['preview_url'] = None
        except (requests.RequestException, KeyError, ValueError):
            track['album_art'] = None
            track['album'] = ''
            track['preview_url'] = None

    return tracks


def resolve_track_to_spotify(sp, track_name, artist_name):
    """
    Resolve a single Last.fm track to a Spotify URI.
    Called only when the user swipes right (likes a track).
    
    Returns:
        dict with 'uri' and 'id' if found, or None
    """
    try:
        query = f"track:{track_name} artist:{artist_name}"
        results = sp.search(q=query, type='track', limit=1)

        if results['tracks']['items']:
            track = results['tracks']['items'][0]
            return {
                'id': track['id'],
                'uri': track['uri'],
                'name': track['name'],
                'artist': ', '.join(a['name'] for a in track['artists']),
            }
    except Exception:
        pass

    return None


def generate_swipe_queue(sp, seed_tracks=None, seed_uris=None, total_tracks=50):
    """
    Generate a shuffled queue of tracks for the swipe feature.
    Returns Last.fm track data (no Spotify resolution needed upfront).
    
    Returns:
        Tuple of (queue list, seeds used list)
    """
    # If URIs provided, resolve them to name/artist
    if seed_uris and not seed_tracks:
        seed_tracks = []
        for uri in seed_uris[:5]:
            track_id = uri.split(":")[-1]
            try:
                track = sp.track(track_id)
                seed_tracks.append({
                    'id': track['id'],
                    'uri': track['uri'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name']
                })
            except Exception:
                continue

    # If no seeds provided, pick random liked songs (falls back to top tracks)
    if not seed_tracks:
        seed_tracks = get_random_liked_seeds(sp, count=5)

    if not seed_tracks:
        return [], []

    tracks_per_seed = (total_tracks // len(seed_tracks)) + 3

    # Fetch similar from Last.fm
    similar_tracks = get_similar_tracks_lastfm(seed_tracks, tracks_per_seed)

    if not similar_tracks:
        return [], seed_tracks

    # Shuffle
    random.shuffle(similar_tracks)
    similar_tracks = similar_tracks[:total_tracks]

    # Enrich with album art + preview from Deezer
    enriched = enrich_with_deezer(similar_tracks)

    # Build queue — assign unique IDs for frontend tracking
    queue = []
    for i, track in enumerate(enriched):
        queue.append({
            'queue_id': i,  # Frontend identifier (not a Spotify ID)
            'name': track['name'],
            'artist': track['artist'],
            'album': track.get('album', ''),
            'album_art': track.get('album_art'),
            'preview_url': track.get('preview_url'),
            'lastfm_url': track.get('lastfm_url', ''),
        })

    return queue, seed_tracks


def generate_swipe_queue_streaming(sp, seed_tracks=None, seed_uris=None, total_tracks=50):
    """
    Generator that yields small batches of tracks progressively.
    First batch is yielded quickly (~5 tracks) so the UI can start immediately.
    Remaining tracks are enriched via Deezer and yielded in small batches.
    """
    # If URIs provided, resolve them to name/artist
    if seed_uris and not seed_tracks:
        seed_tracks = []
        for uri in seed_uris[:5]:
            track_id = uri.split(":")[-1]
            try:
                track = sp.track(track_id)
                seed_tracks.append({
                    'id': track['id'],
                    'uri': track['uri'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name']
                })
            except Exception:
                continue

    if not seed_tracks:
        seed_tracks = get_random_liked_seeds(sp, count=5)

    if not seed_tracks:
        yield {"batch": [], "seeds_used": [], "done": True}
        return

    tracks_per_seed = (total_tracks // len(seed_tracks)) + 3

    # Phase 1: Gather all similar tracks from Last.fm (fast, no enrichment yet)
    all_similar = []
    seen = set()
    for seed in seed_tracks:
        similar = get_similar_tracks_for_seed(seed, tracks_per_seed)
        for track in similar:
            key = (track['name'].lower(), track['artist'].lower())
            if key not in seen:
                seen.add(key)
                all_similar.append(track)

    # Shuffle all tracks together for variety
    random.shuffle(all_similar)
    all_similar = all_similar[:total_tracks]

    if not all_similar:
        yield {"batch": [], "seeds_used": seed_tracks, "done": True}
        return

    # Phase 2: Enrich via Deezer and yield in small batches
    FIRST_BATCH_SIZE = 5
    BATCH_SIZE = 10
    queue_id = 0

    # First small batch — gets UI going fast
    first_chunk = all_similar[:FIRST_BATCH_SIZE]
    rest = all_similar[FIRST_BATCH_SIZE:]

    enriched = enrich_with_deezer(first_chunk)
    batch = []
    for track in enriched:
        if track.get('preview_url') is None:
            continue  # Skip tracks without previews to improve UX
        
        batch.append({
            'queue_id': queue_id,
            'name': track['name'],
            'artist': track['artist'],
            'album': track.get('album', ''),
            'album_art': track.get('album_art'),
            'preview_url': track.get('preview_url'),
            'lastfm_url': track.get('lastfm_url', ''),
        })
        queue_id += 1

    yield {
        "batch": batch,
        "seeds_used": seed_tracks,
        "done": len(rest) == 0,
    }

    # Remaining batches
    for i in range(0, len(rest), BATCH_SIZE):
        chunk = rest[i:i + BATCH_SIZE]
        enriched = enrich_with_deezer(chunk)

        batch = []
        for track in enriched:
            if track.get('preview_url') is None:
                continue  # Skip tracks without previews to improve UX

            batch.append({
                'queue_id': queue_id,
                'name': track['name'],
                'artist': track['artist'],
                'album': track.get('album', ''),
                'album_art': track.get('album_art'),
                'preview_url': track.get('preview_url'),
                'lastfm_url': track.get('lastfm_url', ''),
            })
            queue_id += 1

        done = (i + BATCH_SIZE) >= len(rest)

        yield {
            "batch": batch,
            "seeds_used": seed_tracks,
            "done": done,
        }
