import spotipy

def printGenres(sp):
    genres = [g.lower() for g in sp.recommendation_genre_seeds()['genres']]
    print(genres)