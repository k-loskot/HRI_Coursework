#When initially running it may open a website link with an connection error and may prompt you
#in the code to enter URL. Copy and paste the URL of that website into the terminal, it should continue running the code
#if not, run the code again and it should work fine


import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import webbrowser

#Credentials
clientID = 'd2694f42b7394d6a88930e28b5d27179'
clientSecret = 'd529beaac9d64743a5c6c072c1f2b6bc'

# Use Client Credentials for public data access
auth_manager = SpotifyClientCredentials(client_id=clientID, client_secret=clientSecret)
spotifyObject = spotipy.Spotify(auth_manager=auth_manager)



while True:
    #Asks user questions
    print("Welcome to Spotify Search")
    print("0 - Exit the console")
    print("1 - Search for a Song")
    user_input = int(input("Enter Your Choice: "))
    if user_input == 1:
        #Asks for song name
        search_song = input("Enter the song name: ")
        #Fetches request 
        results = spotifyObject.search(search_song, 1, 0, "track")
        #Gets all necessary information
        songs_dict = results['tracks']
        song_items = songs_dict['items']
        song = song_items[0]['external_urls']['spotify']
        
        # Gets the track ID to fetch audio features
        track_id = song_items[0]['id']
        print("Track ID: " + track_id)
        track_name = song_items[0]['name']
        print("Track Name: " + track_name)
        artist_name = song_items[0]['artists'][0]['name']
        print("Artist Name: " + artist_name)
        ########################################IGNORE################################
        # # Get audio features including tempo (not possible due to account limitations)
        # audio_features = spotifyObject.audio_features(track_id)[0]
        # tempo = audio_features['tempo']
        
        # print(f"\nTrack: {track_name}")
        # print(f"Artist: {artist_name}")
        # print(f"Tempo: {tempo} BPM")
        ##########################################################################################
        
        #Runs request (will open application on your device)
        webbrowser.open(song)
        print('Song has opened in your browser.\n')
    #Exit option/invalid input
    elif user_input == 0:
        print("Good Bye, Have a great day!")
        break
    else:
        print("Please enter valid user-input.")