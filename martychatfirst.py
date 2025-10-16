pip install martypy SpeechRecognition pyttsx3 pyaudio
from martypy import Marty
import time
import string
import speech_recognition as sr

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
	else:
		marty.speak("Oh! No worries, happy studying!")

elif 'maths' in studysubjectkeywords:

	marty.speak("Wonderful! While you are studying maths, would you love some edm's to help you?")
	musicconfirmation = listen_for_replies().lower()
	musicconfirmationkeywords = musicconfirmation.translate(str.maketrans('', '', string.punctuation)).split()

	if "yes" in musicconfirmationkeywords:
		marty.speak("Perfect, some music coming up for you!")
	else:
		marty.speak("No worries, silence can help you concentrate!")

	marty.speak("Would you like me to set a timer?")
	timerconfirmation = listen_for_replies().lower()
	timerconfirmationkeywords = timerconfirmation.translate(str.maketrans('', '', string.punctuation)).split()

	if 'yes' in timerconfirmationkeywords:
		marty.speak("I think the best way to study maths is a 1 hour session with it broken down into 20 mins mini sessions with a 3 min break between each. Let me get it started for you!")
	else:
		marty.speak("Oh! No worries, happy studying!")





