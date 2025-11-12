import martypy
import time
import threading
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import speech_recognition as sr
import google.genai
import random
import webbrowser
import sys
import select

# --- Connection Types ---
USB = 'usb'
WIFI = 'wifi'

# --- Constants ---
RED = 'Red'
GREEN = 'Green'
TIMEOUT = 'Timeout'

# --- Simplified Marty Connection (Set your connection type and port here) ---
# NOTE: Replace 'COM3' with your actual port or IP if using WIFI.
MARTY_CONNECTION = martypy.Marty(USB, 'COM3', blocking=True)


class MartyStudyAssistant:
    def __init__(self):
        # Initialize Marty Study Assistant and its configurations.
        self.marty = MARTY_CONNECTION
        print("Marty connection setup complete.")

        # --- Speech Recognition Setup ---
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        print("Speech Recognition setup complete.")

        # --- Gemini API Setup (FIXED with Hardcoded Key) ---
        try:
            # 🚨 WARNING: Hardcoding keys is insecure. This is for classroom demo purposes only.
            API_KEY = "AIzaSyBoqhH-tZLPGenZtDjWOPN7zJBFH6KzZ-k"
            # Pass the key directly to the Client initializer
            self.gemini_client = google.genai.Client(api_key=API_KEY)
            self.gemini_model = 'gemini-2.5-flash'
            print("Gemini API Client configured successfully (using hardcoded key).")
        except Exception as e:
            self.gemini_client = None
            print(f"Gemini API configuration failed: {e}")

        # --- SPOTIPY SETUP (RE-IMPLEMENTED for Stability) ---
        self.spotify_client = self._initialize_spotify_client()
        if self.spotify_client:
            print("Spotify client initialized successfully using cached token.")
        else:
            print("Spotify client failed to initialize. Music functionality will be disabled.")

        # --- UPDATED: High-Quality, Large Spotify Playlist URIs (Not URLs!) ---
        # We need the URI (spotify:playlist:...) for the API to work, not the full URL.
        # These are official Spotify playlists with many hours of music.
        self.SPOTIFY_PLAYLISTS = {
            'lofi': 'spotify:playlist:6zCID88oNjNv9zx6puDHKj',
            'jazz': 'spotify:playlist:4lFMHfo4EC2yAk30Rwz5U7',
            'classical': 'spotify:playlist:1jcltKkVNCwr9UP0T1UWgU',
            'ambient': 'spotify:playlist:1kqBP6eE24L0agNpnTIKtc',
            'calm': 'spotify:playlist:6OpvhaJmmbdhqjplBKUGeJ'
        }
        print("Spotify playlist URIs loaded.")

        # Optimized time configuration
        self.time_config = {
            'voice_selection_timeout': 10,  # <-- MODIFIED: Changed from 5 to 10 seconds
            'preparation': 20,
            'study_session': 25,
            'rest_session': 5,
        }

        if self.marty:
            print("Marty connected successfully!")
        else:
            print("Marty connection failed or was not fully set up outside the class.")

    def _initialize_spotify_client(self):
        """Initializes the Spotify client using your API credentials and creates a local token cache."""
        try:
            client_id = "a8a3a043933f425488667bd51cb69f68"
            client_secret = "bfcd14a8e3d247eaae927180c088d123"
            redirect_uri = "http://127.0.0.1:8888/callback"

            scope = (
                "user-read-playback-state,"
                "user-modify-playback-state,"
                "user-read-currently-playing"
            )

            print("[Spotify] Initializing client using direct API credentials...")

            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                cache_path=".cache-marty"
            )

            sp = spotipy.Spotify(auth_manager=auth_manager)

            current_user = sp.current_user()
            print(f"[Spotify] Authenticated as: {current_user['display_name']} ({current_user['id']})")

            return sp

        except spotipy.oauth2.SpotifyOauthError as e:
            print("❌ Spotify OAuth authentication failed. Please check your credentials or redirect URI.")
            print(f"Error details: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error during Spotify client setup: {e}")
            return None

    def speak(self, text):
        # Make Marty speak, with a substantial delay.
        print(f"Marty says: {text}")
        try:
            if self.marty:
                self.marty.speak(text)
                time.sleep(1.5)
        except Exception as e:
            print(f"Marty speak failed: {e}")

    # --- Gemini API Processing Function (NLU) - Enhanced Prompt ---
    def get_gemini_nlu_result(self, text):
        """Uses Gemini API to parse the recognized text into structured JSON."""
        if not self.gemini_client:
            print("[Gemini NLU] Client not available. Cannot process intent.")
            return None

        prompt = f"""
        You are a smart study assistant specializing in natural language understanding.
        Your task is to analyze the user's input text, determine the specific intent, and extract the required entity value.

        **Instructions:**
        1. **Strict Output:** Output the result strictly in a single JSON block. Do not include any extra text, explanations, or Markdown tags.
        2. **Unknowns:** If the intent or entity value cannot be clearly identified, use the value "unknown_intent" or null, respectively.
        3. **Fuzzy Matching:** Be robust. Recognize synonyms, related words, and slight mispronunciations for the entities and map them to the canonical values.

        **Canonical Intent and Entity Mapping:**
        * **Intent: select_subject**
            * Entity: subject
            * Canonical Values: 'science' (e.g., for "I want to study chemistry", "science time"), 'math' (e.g., for "maths", "algebra", "mathematics"), 'language' (e.g., for "English lesson", "French").
        * **Intent: express_mood**
            * Entity: mood
            * Canonical Values: 'happy' (e.g., for "good", "great", "awesome", "nice", "wonderful", "amazing"), 'stressed' (e.g., for "sad", "tired", "anxious", "overwhelmed", "bad").
        * **Intent: select_music**
            * Entity: music
            * Canonical Values: 'lofi', 'jazz', 'classical', 'ambient', 'calm'.
        * **Intent: confirm_accompaniment**
            * Entity: choice
            * Canonical Values: 'stay' (e.g., for "yes", "stick around", "stay please"), 'leave' (e.g., for "no", "go away", "leave now").

        **User Input to Process:** {text}

        **JSON Schema (Must be strictly followed):**
        {{
          "intent": "string",
          "entity_name": "string or null",
          "entity_value": "string or null"
        }}
        """

        try:
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt
            )
            json_text = response.text.strip()
            # Compatibility handling for Markdown code fences
            if json_text.startswith("```json"):
                json_text = json_text.strip("```json").strip("```").strip()
            result = json.loads(json_text)
            print(f"[Gemini NLU] Result: {result}")
            return result

        except Exception as e:
            print(f"[Gemini NLU] API failed or JSON parsing error: {e}. Raw response: {response.text}")
            return None

    def wait_for_voice_selection(self, timeout=10, expected_intent=None):
        """Wait for a verbal response, use Gemini NLU to extract intent and entity. Pauses music first."""
        # 🚀 MODIFICATION 1: Pause music before listening
        if self.spotify_client:
            print("[Spotify] Pausing music for voice selection...")
            self.stop_spotify_music()  # Pause music
            time.sleep(0.5)  # Give some time for API response

        self.speak("I am listening now...")
        selected_value = TIMEOUT

        try:
            with self.microphone as source:
                # Noise calibration is now explicitly 2.0 seconds
                self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
                print("[Voice] Listening...")
                # Timeout and phrase limit are 10 seconds
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)

            print("[Voice] Analyzing speech...")
            # Use Google Speech Recognition
            text = self.recognizer.recognize_google(audio, language='en-US')
            self.speak(f"I heard: {text}")

            api_result = self.get_gemini_nlu_result(text)
            if not api_result or api_result.get('intent') == 'unknown_intent':
                self.speak("I couldn't clearly understand your intention.")
            else:
                intent_name = api_result.get('intent')
                entity_value = api_result.get('entity_value')
                print(f"[API] Intent: {intent_name}, Entity Value: {entity_value}")

                if intent_name != expected_intent:
                    self.speak("I understood something, but not what I asked for at this moment.")
                elif entity_value:
                    self.speak(f"Detected choice: {entity_value}.")
                    selected_value = entity_value
                else:
                    self.speak("I understood the task, but the specific choice was unclear.")

        except sr.WaitTimeoutError:
            print("[Voice] Timeout reached. No speech detected.")
        except sr.UnknownValueError:
            self.speak("Sorry, I could not understand the audio.")
            print("[Voice] Google Speech Recognition could not understand audio")
        except Exception as e:
            print(f"[Voice] An unexpected error occurred: {e}")

        return selected_value

    def execute_marty_action(self, action_name):
        # (Marty actions logic remains unchanged)
        if not self.marty:
            print(f"Marty not connected, cannot execute action: {action_name}")
            return "Marty not available"

        action_name = action_name.strip().lower()
        try:
            result = ""
            if action_name == 'dance':
                self.marty.dance()
            elif action_name == 'wave':
                self.marty.wave(side='left')
                time.sleep(1)
                self.marty.wave(side='right')
            elif action_name == 'celebrate':
                self.marty.celebrate()
            elif action_name == 'walk_forward':
                self.marty.walk(num_steps=10, start_foot='auto', turn=0, step_length=30, move_time=1500)
            elif action_name == 'stop':
                self.marty.stop()
            elif action_name == 'get_ready':
                self.marty.get_ready()
            elif action_name == 'eyes_excited':
                self.marty.eyes(pose='excited')
            elif action_name == 'eyes_normal':
                self.marty.eyes(pose='normal')
            else:
                result = f"Unknown action: {action_name}"

            if action_name not in ['get_ready', 'eyes_excited', 'eyes_normal', 'stop']:
                self.marty.get_ready()
            return result
        except Exception as e:
            print(f"Action execution failed: {e}")
            return "Action execution failed"

    def ask_for_accompaniment(self):
        """Ask user if Marty should stay or leave. Music is paused by wait_for_voice_selection."""
        self.speak("Would you like me to stay and keep you company?")
        self.speak("Please say 'Stay' to keep me here, or 'Leave' to ask me to walk away.")

        # Music is automatically paused inside wait_for_voice_selection
        selected_option = self.wait_for_voice_selection(
            timeout=self.time_config['voice_selection_timeout'],
            expected_intent='confirm_accompaniment'
        )

        # 🚀 MODIFICATION 1: Music is NOT resumed here. It is resumed in initial_setup_and_study
        if selected_option == 'stay':
            self.speak("Great! I'll be quiet and keep you company. Good luck with your study!")
            self.execute_marty_action('eyes_excited')

        elif selected_option == 'leave':
            self.speak("Understood. You need some quiet space.")
            # Music remains paused for quiet study space (handled by wait_for_voice_selection pause)
            try:
                if self.marty:
                    self.speak("I am turning around now...")
                    for _ in range(5):
                        self.marty.walk(num_steps=1, turn=30, step_length=0, move_time=1500)
                    self.speak("Stepping away to give you space...")
                    self.marty.walk(num_steps=10, step_length=25, move_time=2000)
                    self.speak("I'll be nearby if you need anything!")
                    for _ in range(5):
                        self.marty.walk(num_steps=1, turn=-30, step_length=0, move_time=1500)
                    self.execute_marty_action('get_ready')
            except Exception as e:
                print(f"Walk away sequence failed: {e}")
        else:
            self.speak("No selection detected. I will stay here by default.")
            self.execute_marty_action('eyes_excited')
            self.execute_marty_action('get_ready')

        return selected_option

    # --- MODIFIED: play_spotify_music (NOW USES ACCURATE TRACK COUNT FOR RANDOM OFFSET) ---
    def play_spotify_music(self, playlist_key):
        """Play a Spotify playlist from a random track using the authorized client."""
        if not self.spotify_client:
            self.speak("Spotify client is not connected, I cannot play music.")
            return

        uri = self.SPOTIFY_PLAYLISTS.get(playlist_key)
        if not uri:
            self.speak(f"I couldn't find the requested playlist URI for {playlist_key}.")
            return

        try:
            playlist_id = uri.split(":")[-1]

            playlist_info = self.spotify_client.playlist(playlist_id, fields="tracks.total")
            total_tracks = playlist_info.get("tracks", {}).get("total", 0)

            if total_tracks == 0:
                self.speak("The selected playlist appears to be empty.")
                print(f"[Spotify] Playlist '{playlist_key}' has 0 tracks.")
                return

            random_offset = random.randint(0, total_tracks - 1)
            print(f"[Spotify] Total tracks: {total_tracks}, starting at random offset: {random_offset}")

            devices = self.spotify_client.devices()
            active_device = None
            for d in devices.get("devices", []):
                if d.get("is_active"):
                    active_device = d["id"]
                    break

            if not active_device:
                self.speak("Please open your Spotify app or web player first, then try again.")
                print("⚠️ No active Spotify device found. Open your Spotify app or web player and retry.")
                return

            self.spotify_client.start_playback(
                device_id=active_device,
                context_uri=uri,
                offset={"position": random_offset}
            )

            self.spotify_client.shuffle(True)

            self.speak(f"Playing the {playlist_key.capitalize()} playlist from a random song.")
            self.speak("Shuffle mode is enabled. Make sure your Spotify app stays open.")

        except spotipy.SpotifyException as e:
            if "No active device" in str(e):
                self.speak("No active Spotify device detected. Please open your Spotify app and try again.")
                print("[Spotify] Error: No active device available.")
            else:
                self.speak(f"Spotify command failed: {e}")
                print(f"[Spotify] API error: {e}")
        except Exception as e:
            self.speak("An unexpected error occurred while trying to play music.")
            print(f"[Spotify] General playback error: {e}")

    # --- MODIFIED: stop_spotify_music (NOW USES API FOR PAUSE) ---
    def stop_spotify_music(self):
        if not self.spotify_client:
            return

        try:
            self.spotify_client.pause_playback()
            print("[Spotify] Playback paused via API.")
        except Exception as e:
            print(f"[Spotify] API pause failed: {e}")

    def ask_music_preference(self, is_study=True):
        if not is_study:
            self.speak("Now, let's play some soothing ambient music for your rest session.")
            self.play_spotify_music('ambient')
            return

        self.speak("Now, let's select some background music for your study session.")
        self.speak("Say 'Lo-fi', 'Jazz', 'Classical', or 'Ambient'.")
        self.speak(f"You have {self.time_config['voice_selection_timeout']} seconds to speak your choice.")

        # Music is automatically paused inside wait_for_voice_selection
        selected_genre_key = self.wait_for_voice_selection(
            timeout=self.time_config['voice_selection_timeout'],
            expected_intent='select_music'
        )

        # After selection, music is played/replayed immediately
        if selected_genre_key in self.SPOTIFY_PLAYLISTS:
            self.speak(f"{selected_genre_key.capitalize()} detected. Playing playlist.")
            self.play_spotify_music(selected_genre_key)
        else:
            self.speak("No selection detected, playing default Lo-fi study music.")
            self.play_spotify_music('lofi')

    def mood_selection(self):
        self.speak("Please tell me how you are feeling today: Say 'Happy' or 'Stressed'.")
        self.speak(f"Speak your mood in {self.time_config['voice_selection_timeout']} seconds.")

        # Music is automatically paused inside wait_for_voice_selection
        selected_mood = self.wait_for_voice_selection(
            timeout=self.time_config['voice_selection_timeout'],
            expected_intent='express_mood'
        )

        # ⚠️ NOTE: Since music was paused, if the user chose 'stressed', play_spotify_music('calm') will handle restart.
        # If user chose 'happy' or TIMEOUT, music is left paused and resumed by initial_setup_and_study's music selection.
        if selected_mood == 'happy':
            self.speak("You are in a good mood! Positive energy is great for learning!")
            # 修正的动作：使用正确的martypy API
            try:
                if self.marty:
                    self.marty.arms(150, 150, 1000)  # 高举双臂150度
                    self.marty.eyes("excited")  # 高兴的眼睛
                    self.marty.disco_color_eyepicker(colours="#00cbff", add_on="LEDeye")  # 眼睛亮灯
                    time.sleep(1)
                    self.marty.dance()  # 跳舞
                    time.sleep(1)
                    self.marty.get_ready()  # 重置为准备状态
            except Exception as e:
                print(f"Happy mood action sequence failed: {e}")
            # Music remains paused for next selection (ask_music_preference)
        elif selected_mood == 'stressed':
            self.speak("You seem stressed or tired. Let's start with some calming music for you.")
            # 修正的动作：使用正确的martypy API
            try:
                if self.marty:
                    self.marty.eyes("wide")  # 伤心的眼睛
                    time.sleep(2)
                    self.marty.get_ready()  # 重置为准备状态
            except Exception as e:
                print(f"Stressed mood action sequence failed: {e}")
            self.execute_marty_action('wave')
            self.play_spotify_music('calm')  # This plays music
            self.speak("I opened a calming music playlist for you. Take a deep breath, and relax.")
            time.sleep(5)
            self.speak("Now, let's start fresh with our study session.")
            self.stop_spotify_music()  # Pause the 'calm' music so ask_music_preference can start the next track
        else:
            self.speak("No selection detected, I assume you are ready to learn!")
            self.execute_marty_action('wave')
            # Music remains paused for next selection (ask_music_preference)

    def subject_selection(self):
        self.speak("What subject would you like to study? Say 'Science', 'Math', or 'Language'.")
        self.speak(f"Please speak your subject choice in {self.time_config['voice_selection_timeout']} seconds.")

        # Music is automatically paused inside wait_for_voice_selection
        selected_subject = self.wait_for_voice_selection(
            timeout=self.time_config['voice_selection_timeout'],
            expected_intent='select_subject'
        )

        if selected_subject == 'science':
            self.speak("Science detected. Excellent choice!")
            return 'science'
        elif selected_subject == 'math':
            self.speak("Math detected. You can do it!")
            return 'math'
        elif selected_subject == 'language':
            self.speak("Language detected. Wonderful!")
            return 'language'
        else:
            self.speak("No selection detected, proceeding with general studies.")
            return 'general'

    def start_timer(self, duration_seconds, activity_name, interrupt_word='stop'):
        self.speak(f"Starting the {activity_name} for {duration_seconds // 60} minutes.")
        self.speak(f"Say the word '{interrupt_word}' at any time to stop the activity.")

        stop_event = threading.Event()

        def timer_thread():
            end_time = time.time() + duration_seconds
            while time.time() < end_time and not stop_event.is_set():
                time.sleep(1)
            if not stop_event.is_set():
                self.speak(f"{activity_name} completed! Well done!")

        def voice_monitor():
            while not stop_event.is_set():
                print(f"[Voice Monitor] Waiting for '{interrupt_word}'...")
                try:
                    with self.microphone as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio = self.recognizer.listen(source, timeout=1.0, phrase_time_limit=1.0)
                        text = self.recognizer.recognize_google(audio, language='en-US').lower()
                        print(f"[Voice Monitor] Detected: {text}")
                        if interrupt_word.lower() in text:
                            stop_event.set()
                            self.speak(f"Detected the word '{interrupt_word}', activity stopped as requested.")
                            break

                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    print(f"[Voice Monitor] Request error: {e}")
                except Exception as e:
                    print(f"[Voice Monitor] Error: {e}")
                    pass
                time.sleep(0.5)

        timer = threading.Thread(target=timer_thread)
        voice = threading.Thread(target=voice_monitor)

        timer.start()
        voice.start()

        timer.join()

        if voice.is_alive():
            stop_event.set()
            voice.join(timeout=2)

    def learning_timer(self, duration_minutes=25):
        self.start_timer(
            duration_seconds=duration_minutes * 60,
            activity_name=f"{duration_minutes} minute study session"
        )

    def rest_timer(self, duration_minutes=5):
        self.speak("Now, let's start our quick break!")
        self.ask_music_preference(is_study=False)
        self.start_timer(
            duration_seconds=duration_minutes * 60,
            activity_name=f"{duration_minutes} minute break",
            interrupt_word='resume'
        )

    def celebration_sequence(self):
        self.speak("Congratulations on completing your study session!")
        self.execute_marty_action('celebrate')
        time.sleep(2)
        self.execute_marty_action('eyes_excited')
        self.speak("You did an excellent job today!")

    def initial_setup_and_study(self):
        """Handles initial setup, selections, and starts the first timer block."""
        self.speak("Please prepare your study materials.")
        self.speak(f"You have {self.time_config['preparation']} seconds to get ready.")
        time.sleep(self.time_config['preparation'])
        self.speak("Preparation time is over! Let's begin our learning journey.")

        # 1. Subject selection (Music paused inside)
        self.subject_selection()

        # 2. Accompaniment check (Music paused inside wait_for_voice_selection)
        accompaniment_choice = self.ask_for_accompaniment()

        # 3. Music selection and play (Music played here)
        self.ask_music_preference(is_study=True)

        # 4. Resume music only if user didn't choose to leave
        if accompaniment_choice != 'leave':
            if self.spotify_client:
                try:
                    self.spotify_client.start_playback()
                    print("[Spotify] Resuming playback for study session.")
                except Exception as e:
                    print(f"Spotify resume failed: {e}")
        else:
            self.stop_spotify_music()
            print("[Spotify] Keeping music paused as user chose 'leave'.")

        # 5. Start first study session
        self.speak(f"Starting the first study segment ({self.time_config['study_session']} minutes).")
        self.learning_timer(self.time_config['study_session'])

    def start_study_session(self):
        if not self.marty:
            print("Marty not connected, cannot start study session")
            return

        try:
            # Open Spotify web player at the beginning
            print("Opening Spotify web player...")
            webbrowser.open("https://open.spotify.com")
            time.sleep(2)  # Give time for browser to open

            self.execute_marty_action('get_ready')
            time.sleep(0.5)
            self.speak("Hello! I'm Marty, your personal study assistant!")
            self.speak("I am moving closer to you.")
            self.execute_marty_action('walk_forward')
            self.execute_marty_action('get_ready')
            time.sleep(1)
            self.execute_marty_action('wave')

            # 3. Mood selection (Music paused and handled internally)
            self.mood_selection()

            # 4. Subject, Accompaniment, Music, and Study Segment 1
            self.initial_setup_and_study()

            # 5. Break time
            self.speak("First study segment finished! Time for a quick break!")
            self.rest_timer(self.time_config['rest_session'])

            # 6. One more study segment after the break
            self.speak("Break time is over! Starting next study segment.")
            self.ask_music_preference(is_study=True)
            self.speak("Let's return to focused study.")
            self.learning_timer(self.time_config['study_session'])

            # 7. Ends it off with a well done and a dance
            self.celebration_sequence()

            # 新添加的最终心情询问环节
            self.speak("Now that we've finished our study session, how are you feeling now?")
            self.speak("Please tell me if you're feeling 'Happy' or 'Stressed'.")

            final_mood = self.wait_for_voice_selection(
                timeout=self.time_config['voice_selection_timeout'],
                expected_intent='express_mood'
            )

            if final_mood == 'happy':
                self.speak("I'm so glad you're feeling happy! You did an amazing job today!")
                self.execute_marty_action('dance')
            elif final_mood == 'stressed':
                self.speak(
                    "I understand you're still feeling stressed. Remember, every small step counts and you made great progress today!")
                self.execute_marty_action('dance')
            else:
                self.speak("I hope you're feeling good about your accomplishments today!")
                self.execute_marty_action('dance')

            self.stop_spotify_music()
            self.speak("Study session completed! Well done! I'm proud of your focus and effort!")

        except KeyboardInterrupt:
            self.speak("Session interrupted by user")
            self.stop_spotify_music()
        except Exception as e:
            print(f"Session error: {e}")
            self.stop_spotify_music()
        finally:
            self.cleanup()

    def cleanup(self):
        try:
            if self.marty:
                self.marty.stop()
                print("Marty stopped")
                self.marty.close()
        except Exception as e:
            error_message = str(e)
            if "WinError 6" in error_message or "Handle is invalid" in error_message:
                print("Ignored harmless WinError 6 during final cleanup (connection already terminated by OS).")
            else:
                print(f"Cleanup failed but proceeding to exit: {e}")
            pass


# Usage example
if __name__ == '__main__':
    assistant = MartyStudyAssistant()
    assistant.start_study_session()