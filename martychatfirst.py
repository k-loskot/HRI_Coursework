pip install martypy SpeechRecognition pyttsx3 pyaudio
from martypy import Marty
import time
import string
import speech_recognition as sr
import pygame


marty = Marty("wifi", "192.168.0.53")

marty.hello()

recognizer = sr.Recognizer()

def listen_for_replies():
	with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio).lower()
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Sorry, I didn’t catch that.")
            return None
        except sr.RequestError:
            print("Speech recognition service error.")
            return None
		
def countdown(h, m, s):
    total_seconds = h * 3600 + m * 60 + s
 
    while total_seconds > 0:
        timer = datetime.timedelta(seconds = total_seconds)
        print(timer, end="\r")
        time.sleep(1)
        total_seconds -= 1
 
countdown(int(h), int(m), int(s))

#music
pygame.mixer.init()
pygame.mixer.music.load("/Users/abhiramreddy/Downloads/firstsong.mp3")

marty.speak("Heyy, how are you feeling today?")
response = listen_for_replies().lower()
responsekeywords = response.translate(str.maketrans('', '', string.punctuation)).split()

if "good" in responsekeywords or "great" in responsekeywords or "amazing" in responsekeywords:
	if "not" in responsekeywords:
		marty.speak("Oh, that doesnt sound too good, maybe a great study session would boost your mood!")
		marty.speak("What would you like to study today?")
		studysubject = listen_for_replies().lower()

	else:
		marty.speak("Thats great, what would you like to study today?")
		studysubject = listen_for_replies().lower()

else:
	marty.speak("Oh, that doesnt sound too good, maybe a great study session would boost your mood")
	marty.speak("What would you like to study today")
	studysubject = listen_for_replies().lower()


studysubjectkeywords = studysubject.translate(str.maketrans('', '', string.punctuation)).split()

if "english" in studysubjectkeywords:
	
	marty.speak("Wonderful! I think english would require your full concentration so music might not be a great idea.")

	marty.speak("Would you like me to set a timer?")
	timerconfirmation = listen_for_replies().lower()
	timerconfirmationkeywords = timerconfirmation.translate(str.maketrans('', '', string.punctuation)).split()
	
	if 'yes' in timerconfirmationkeywords:
		marty.speak("I think the best way to study english is a 1 hour session with a 5 min break in the middle and a 5 min break at the end. Let me get it started for you!")
		countdown(0,25,0)
		marty.speak("Great job! You're halfway done!, time for a 5 min break")
		countdown(0,5,0)
		marty.speak("Break's over! Lets get back to studying")
		countdown(0,25,0)
		marty.speak("Your study session is now done, take a 5 min break and get ready for the rest of your day!")
		countdown(0,5,0)
		marty.speak("Break's done too! Have a great day!")
	else:
		marty.speak("Oh! No worries, happy studying!")

elif 'maths' in studysubjectkeywords:

	marty.speak("Wonderful! While you are studying maths, would you love some edm's to help you?")
	musicconfirmation = listen_for_replies().lower()
	musicconfirmationkeywords = musicconfirmation.translate(str.maketrans('', '', string.punctuation)).split()

	if "yes" in musicconfirmationkeywords:
		marty.speak("Perfect, some music coming up for you!")
		pygame.mixer.music.play(-1)
	else:
		marty.speak("No worries, silence can help you concentrate!")

	marty.speak("Would you like me to set a timer?")
	timerconfirmation = listen_for_replies().lower()
	timerconfirmationkeywords = timerconfirmation.translate(str.maketrans('', '', string.punctuation)).split()

	if 'yes' in timerconfirmationkeywords:
		marty.speak("I think the best way to study maths is through the pomodoro technique where the sessions is divided into 25 mins mini segments with a 5 min break between each. Let me get it started for you!")
		countdown(0,25,0)
		marty.speak("The first 20 mins are done, take a 3 min break to help you focus on the next 2 segments.")
		countdown(0,5,0)
		marty.speak("Break done! back to studying!")
		countdown(0,25,0)
		marty.speak("You only have 1 more segment after this break! Good going!")
		countdown(0,5,0)
		marty.speak("Break done! back to studying!")
		countdown(0,25,0)
		marty.speak("You're all done for the day!")
	else:
		marty.speak("Oh! No worries, happy studying!")





