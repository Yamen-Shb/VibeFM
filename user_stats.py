import spotify_utils

# Get the user's top tracks
def topTracks(sp):
    validInput = True

    while validInput:
        userInput = input("Please enter the number of tracks you want to rank (up to top 50): ")
        numberOfTracks = int(userInput)

        # check validity of 50 being max
        if numberOfTracks > 50:
            print("Can only rank the top 50. Sorry!")
        elif numberOfTracks < 0:
            print("That's not a valid input. Try again.")
        else:
            # optimize, I need some sort of drop down list
            timeRangeInput = input(
                "Please enter the range of time you want to sort your music from (4 weeks/6 months/all time): ")

            results = sp.current_user_top_tracks(limit=numberOfTracks, time_range=timeRangeInput)
            topTracksToPrint = []

            if 'items' in results and results['items']:
                topTracksToPrint.extend(results['items'])

            for index, track in enumerate(topTracksToPrint):
                print(
                    f"Top track {index + 1}: {track['name']} "
                    f"by {', '.join(artist['name'] for artist in track['artists'])}")

            validInput = False


def topArtists(sp):
    invalidInput = True

    while invalidInput:
        userInput = input("Please enter the number of artists you want to rank (up to top 50): ")
        numberOfArtists = int(userInput)

        # check validity of 50 being max
        if numberOfArtists > 50:
            print("Can only rank the top 50. Sorry!")
        elif numberOfArtists < 0:
            print("That's not a valid input. Try again.")
        else:
            # optimize, I need some sort of drop down list
            timeRangeInput = input(
                "Please enter the range of time you want to sort your music from (4 weeks/6 months/all time): ")

            results = sp.current_user_top_artists(limit=numberOfArtists, time_range=timeRangeInput)
            topArtistsToPrint = []

            if 'items' in results and results['items']:
                topArtistsToPrint.extend(results['items'])

            for index, artist in enumerate(topArtistsToPrint):
                print(f"{index + 1}: {artist['name']}")

            invalidInput = False
