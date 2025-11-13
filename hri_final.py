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

# Connection types for Marty robot
USB = 'usb'
WIFI = 'wifi'

# Color constants for status indicators
RED = 'Red'
GREEN = 'Green'

# Timeout constant for voice recognition
TIMEOUT = 'Timeout'

# Marty robot connection instance
MARTY_CONNECTION = martypy.Marty(USB, 'COM3', blocking=True)


class MartyStudyAssistant:
    """
    A smart study assistant using Marty robot with voice recognition,
    music playback, and study session management capabilities.
    """

    def __init__(self):
        """
        Initialize the Marty Study Assistant with all required components:
        - Marty robot connection
        - Speech recognition system
        - Gemini AI for natural language processing
        - Spotify client for music playback
        - Study session timing configuration
        """
        # Initializing Marty robot connection
        self.marty = MARTY_CONNECTION
        print("Marty connection setup complete.")

        # Configuring speech recognition system
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        print("Speech Recognition setup complete.")

        # Initializing Gemini AI client for natural language understanding
        try:
            API_KEY = "AIzaSyBoqhH-tZLPGenZtDjWOPN7zJBFH6KzZ-k"
            self.gemini_client = google.genai.Client(api_key=API_KEY)
            self.gemini_model = 'gemini-2.5-flash'
            print("Gemini API Client configured successfully.")
        except Exception as e:
            self.gemini_client = None
            print(f"Gemini API configuration failed: {e}")

        # Initializing Spotify client for music functionality
        self.spotify_client = self._initialize_spotify_client()
        if self.spotify_client:
            print("Spotify client initialized successfully.")
        else:
            print("Spotify client failed to initialize.")

        # Defining Spotify playlist URIs for different music genres
        self.SPOTIFY_PLAYLISTS = {
            'lofi': 'spotify:playlist:6zCID88oNjNv9zx6puDHKj',
            'jazz': 'spotify:playlist:4lFMHfo4EC2yAk30Rwz5U7',
            'classical': 'spotify:playlist:1jcltKkVNCwr9UP0T1UWgU',
            'ambient': 'spotify:playlist:1kqBP6eE24L0agNpnTIKtc',
            'calm': 'spotify:playlist:6OpvhaJmmbdhqjplBKUGeJ'
        }
        print("Spotify playlist URIs loaded.")

        # Configuring timing parameters for study sessions
        self.time_config = {
            'voice_selection_timeout': 10,
            'preparation': 20,
            'study_session': 25,
            'rest_session': 5,
        }

        # Verifying Marty connection status
        if self.marty:
            print("Marty connected successfully!")
        else:
            print("Marty connection failed.")

    # =============================================================================
    # DISCARDED FEATURE: COLOR DETECTION USING GROUND SENSORS
    # =============================================================================

    # def detect_card_color(self):
    #     """
    #     [DISCARDED FEATURE] Color detection using ground sensors
    #     This function was planned to detect colored cards for interactive study sessions
    #     but was abandoned due to inconsistent sensor readings in different lighting conditions
    #     """
    #     try:
    #         # Get sensor reading from Marty's ground sensors
    #         sensor_value = self.marty.get_ground_sensor_reading("left")
    #         print(f"[Color Detection] Sensor reading: {sensor_value}")
    #
    #         # Define threshold ranges for color detection
    #         GREEN_THRESHOLD_MIN = 200
    #         GREEN_THRESHOLD_MAX = 400
    #         RED_THRESHOLD_MIN = 100
    #         RED_THRESHOLD_MAX = 199
    #
    #         # Determine color based on sensor value
    #         if GREEN_THRESHOLD_MIN <= sensor_value <= GREEN_THRESHOLD_MAX:
    #             return 'Green'
    #         elif RED_THRESHOLD_MIN <= sensor_value <= RED_THRESHOLD_MAX:
    #             return 'Red'
    #         else:
    #             return 'Unknown'
    #
    #     except Exception as e:
    #         print(f"[Color Detection] Error: {e}")
    #         return 'Error'

    # Initializing Spotify client with OAuth authentication
    def _initialize_spotify_client(self):
        """
        Initialize Spotify client using OAuth authentication.
        Creates a local token cache for persistent authentication.

        Returns:
            spotipy.Spotify: Authenticated Spotify client instance or None if failed
        """
        try:
            # Spotify API credentials
            client_id = "a8a3a043933f425488667bd51cb69f68"
            client_secret = "bfcd14a8e3d247eaae927180c088d123"
            redirect_uri = "http://127.0.0.1:8888/callback"

            # Define required Spotify permissions
            scope = (
                "user-read-playback-state,"
                "user-modify-playback-state,"
                "user-read-currently-playing"
            )

            print("[Spotify] Initializing client using direct API credentials...")

            # Create OAuth manager with token caching
            auth_manager = SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                cache_path=".cache-marty"
            )

            # Create authenticated Spotify client
            sp = spotipy.Spotify(auth_manager=auth_manager)

            # Verify authentication by fetching current user
            current_user = sp.current_user()
            print(f"[Spotify] Authenticated as: {current_user['display_name']}")

            return sp

        except spotipy.oauth2.SpotifyOauthError as e:
            print("❌ Spotify OAuth authentication failed.")
            print(f"Error details: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error during Spotify client setup: {e}")
            return None

    # Making Marty speak the provided text
    def speak(self, text):
        """
        Make Marty speak the provided text with appropriate timing.

        Args:
            text (str): The text for Marty to speak
        """
        print(f"Marty says: {text}")
        try:
            if self.marty:
                self.marty.speak(text)
                time.sleep(1.5)
        except Exception as e:
            print(f"Marty speak failed: {e}")

    # Processing text with Gemini AI for natural language understanding
    def get_gemini_nlu_result(self, text):
        """
        Process natural language text using Gemini AI to extract structured intent and entities.

        Args:
            text (str): User's spoken text to analyze

        Returns:
            dict: Parsed intent and entity information in JSON format
        """
        if not self.gemini_client:
            print("[Gemini NLU] Client not available.")
            return None

        # Define prompt for Gemini AI to extract structured information
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
            # Send request to Gemini AI
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt
            )

            # Parse and clean response
            json_text = response.text.strip()
            if json_text.startswith("```json"):
                json_text = json_text.strip("```json").strip("```").strip()

            # Convert to dictionary
            result = json.loads(json_text)
            print(f"[Gemini NLU] Result: {result}")
            return result

        except Exception as e:
            print(f"[Gemini NLU] API failed or JSON parsing error: {e}")
            return None

    # Waiting for and processing voice input from user
    def wait_for_voice_selection(self, timeout=10, expected_intent=None):
        """
        Listen for voice input, process it with speech recognition and NLU.
        Automatically pauses music during listening.

        Args:
            timeout (int): Maximum time to wait for voice input
            expected_intent (str): The specific intent expected in this context

        Returns:
            str: Detected entity value or TIMEOUT constant
        """
        # Pause music before listening for clear audio capture
        if self.spotify_client:
            print("[Spotify] Pausing music for voice selection...")
            self.stop_spotify_music()
            time.sleep(0.5)

        self.speak("I am listening now...")
        selected_value = TIMEOUT

        try:
            # Capture audio from microphone
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
                print("[Voice] Listening...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=timeout)

            # Convert speech to text
            print("[Voice] Analyzing speech...")
            text = self.recognizer.recognize_google(audio, language='en-US')
            self.speak(f"I heard: {text}")

            # Process text with Gemini AI
            api_result = self.get_gemini_nlu_result(text)
            if not api_result or api_result.get('intent') == 'unknown_intent':
                self.speak("I couldn't clearly understand your intention.")
            else:
                intent_name = api_result.get('intent')
                entity_value = api_result.get('entity_value')
                print(f"[API] Intent: {intent_name}, Entity Value: {entity_value}")

                # Validate intent matches expected context
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

    # Carrying out the specified Marty action
    def execute_marty_action(self, action_name):
        """
        Execute predefined physical actions with Marty robot.

        Args:
            action_name (str): Name of the action to perform

        Returns:
            str: Result message indicating success or failure
        """
        if not self.marty:
            print(f"Marty not connected, cannot execute action: {action_name}")
            return "Marty not available"

        action_name = action_name.strip().lower()
        try:
            result = ""

            # Map action names to Marty robot movements
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

            # Reset to ready position after movement actions
            if action_name not in ['get_ready', 'eyes_excited', 'eyes_normal', 'stop']:
                self.marty.get_ready()

            return result

        except Exception as e:
            print(f"Action execution failed: {e}")
            return "Action execution failed"

    # Asking user if they want Marty to stay or leave
    def ask_for_accompaniment(self):
        """
        Ask user if they want Marty to stay or leave during study session.
        Handles robot movement based on user choice.

        Returns:
            str: User's choice ('stay', 'leave', or timeout default)
        """
        self.speak("Would you like me to stay and keep you company?")
        self.speak("Please say 'Stay' to keep me here, or 'Leave' to ask me to walk away.")

        # Listen for user's choice
        selected_option = self.wait_for_voice_selection(
            timeout=self.time_config['voice_selection_timeout'],
            expected_intent='confirm_accompaniment'
        )

        # Handle user's choice
        if selected_option == 'stay':
            self.speak("Great! I'll be quiet and keep you company. Good luck with your study!")
            self.execute_marty_action('eyes_excited')

        elif selected_option == 'leave':
            self.speak("Understood. You need some quiet space.")
            # Execute walking away sequence
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

    # Playing a Spotify playlist from a random track
    def play_spotify_music(self, playlist_key):
        """
        Play a Spotify playlist starting from a random track.

        Args:
            playlist_key (str): Key identifying the playlist in SPOTIFY_PLAYLISTS
        """
        if not self.spotify_client:
            self.speak("Spotify client is not connected, I cannot play music.")
            return

        # Get playlist URI from predefined list
        uri = self.SPOTIFY_PLAYLISTS.get(playlist_key)
        if not uri:
            self.speak(f"I couldn't find the requested playlist URI for {playlist_key}.")
            return

        try:
            # Extract playlist ID from URI
            playlist_id = uri.split(":")[-1]

            # Get total number of tracks in playlist
            playlist_info = self.spotify_client.playlist(playlist_id, fields="tracks.total")
            total_tracks = playlist_info.get("tracks", {}).get("total", 0)

            if total_tracks == 0:
                self.speak("The selected playlist appears to be empty.")
                return

            # Select random starting position
            random_offset = random.randint(0, total_tracks - 1)
            print(f"[Spotify] Total tracks: {total_tracks}, starting at random offset: {random_offset}")

            # Find active Spotify device
            devices = self.spotify_client.devices()
            active_device = None
            for d in devices.get("devices", []):
                if d.get("is_active"):
                    active_device = d["id"]
                    break

            if not active_device:
                self.speak("Please open your Spotify app or web player first, then try again.")
                return

            # Start playback with random offset and shuffle
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
            else:
                self.speak(f"Spotify command failed: {e}")
        except Exception as e:
            self.speak("An unexpected error occurred while trying to play music.")
            print(f"[Spotify] General playback error: {e}")

    # Pausing currently playing Spotify music
    def stop_spotify_music(self):
        """Pause currently playing Spotify music."""
        if not self.spotify_client:
            return

        try:
            self.spotify_client.pause_playback()
            print("[Spotify] Playback paused via API.")
        except Exception as e:
            print(f"[Spotify] API pause failed: {e}")

    # Asking user for music preference and playing selected playlist
    def ask_music_preference(self, is_study=True):
        """
        Ask user for music preference and play selected playlist.

        Args:
            is_study (bool): True for study music, False for rest/ambient music
        """
        if not is_study:
            self.speak("Now, let's play some soothing ambient music for your rest session.")
            self.play_spotify_music('ambient')
            return

        self.speak("Now, let's select some background music for your study session.")
        self.speak("Say 'Lo-fi', 'Jazz', 'Classical', or 'Ambient'.")
        self.speak(f"You have {self.time_config['voice_selection_timeout']} seconds to speak your choice.")

        # Listen for music genre selection
        selected_genre_key = self.wait_for_voice_selection(
            timeout=self.time_config['voice_selection_timeout'],
            expected_intent='select_music'
        )

        # Play selected music or default
        if selected_genre_key in self.SPOTIFY_PLAYLISTS:
            self.speak(f"{selected_genre_key.capitalize()} detected. Playing playlist.")
            self.play_spotify_music(selected_genre_key)
        else:
            self.speak("No selection detected, playing default Lo-fi study music.")
            self.play_spotify_music('lofi')

    # Detecting user's current mood and responding appropriately
    def mood_selection(self):
        """
        Detect user's current mood and respond with appropriate actions and music.
        Adjusts robot behavior based on whether user is happy or stressed.
        """
        self.speak("Please tell me how you are feeling today: Say 'Happy' or 'Stressed'.")
        self.speak(f"Speak your mood in {self.time_config['voice_selection_timeout']} seconds.")

        # Listen for mood input
        selected_mood = self.wait_for_voice_selection(
            timeout=self.time_config['voice_selection_timeout'],
            expected_intent='express_mood'
        )

        # Handle different mood responses
        if selected_mood == 'happy':
            self.speak("You are in a good mood! Positive energy is great for learning!")
            # Execute happy mood actions
            try:
                if self.marty:
                    self.marty.arms(150, 150, 1000)
                    self.marty.eyes("excited")
                    self.marty.disco_color_eyepicker(colours="#00cbff", add_on="LEDeye")
                    time.sleep(1)
                    self.marty.dance()
                    time.sleep(1)
                    self.marty.get_ready()
            except Exception as e:
                print(f"Happy mood action sequence failed: {e}")

        elif selected_mood == 'stressed':
            self.speak("You seem stressed or tired. Let's start with some calming music for you.")
            # Execute calming actions for stressed mood
            try:
                if self.marty:
                    self.marty.eyes("wide")
                    time.sleep(2)
                    self.marty.get_ready()
            except Exception as e:
                print(f"Stressed mood action sequence failed: {e}")

            self.execute_marty_action('wave')
            self.play_spotify_music('calm')
            self.speak("I opened a calming music playlist for you. Take a deep breath, and relax.")
            time.sleep(5)
            self.speak("Now, let's start fresh with our study session.")
            self.stop_spotify_music()
        else:
            self.speak("No selection detected, I assume you are ready to learn!")
            self.execute_marty_action('wave')

    # Asking user to select study subject
    def subject_selection(self):
        """
        Ask user to select study subject and return their choice.

        Returns:
            str: Selected subject ('science', 'math', 'language', or 'general')
        """
        self.speak("What subject would you like to study? Say 'Science', 'Math', or 'Language'.")
        self.speak(f"Please speak your subject choice in {self.time_config['voice_selection_timeout']} seconds.")

        # Listen for subject selection
        selected_subject = self.wait_for_voice_selection(
            timeout=self.time_config['voice_selection_timeout'],
            expected_intent='select_subject'
        )

        # Handle subject selection responses
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

    # Starting a timed session with voice interrupt capability
    def start_timer(self, duration_seconds, activity_name, interrupt_word='stop'):
        """
        Start a timed session with voice interrupt capability.

        Args:
            duration_seconds (int): Duration of the timer in seconds
            activity_name (str): Name of the activity for voice feedback
            interrupt_word (str): Voice command to stop the timer early
        """
        self.speak(f"Starting the {activity_name} for {duration_seconds // 60} minutes.")
        self.speak(f"Say the word '{interrupt_word}' at any time to stop the activity.")

        # Event to signal timer stop
        stop_event = threading.Event()

        def timer_thread():
            """Background thread that counts down the timer duration."""
            end_time = time.time() + duration_seconds
            while time.time() < end_time and not stop_event.is_set():
                time.sleep(1)
            if not stop_event.is_set():
                self.speak(f"{activity_name} completed! Well done!")

        def voice_monitor():
            """Background thread that listens for interrupt commands."""
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
                time.sleep(0.5)

        # Start both timer and voice monitoring threads
        timer = threading.Thread(target=timer_thread)
        voice = threading.Thread(target=voice_monitor)

        timer.start()
        voice.start()

        # Wait for timer completion
        timer.join()

        # Stop voice monitoring if still running
        if voice.is_alive():
            stop_event.set()
            voice.join(timeout=2)

    # Starting a study session timer with default Pomodoro duration
    def learning_timer(self, duration_minutes=25):
        """
        Start a study session timer with default Pomodoro duration.

        Args:
            duration_minutes (int): Study session duration in minutes
        """
        self.start_timer(
            duration_seconds=duration_minutes * 60,
            activity_name=f"{duration_minutes} minute study session"
        )

    # Starting a rest session timer with ambient music
    def rest_timer(self, duration_minutes=5):
        """
        Start a rest session timer with ambient music.

        Args:
            duration_minutes (int): Rest session duration in minutes
        """
        self.speak("Now, let's start our quick break!")
        self.ask_music_preference(is_study=False)
        self.start_timer(
            duration_seconds=duration_minutes * 60,
            activity_name=f"{duration_minutes} minute break",
            interrupt_word='resume'
        )

    # Executing celebration actions after successful study completion
    def celebration_sequence(self):
        """Execute celebration actions after successful study completion."""
        self.speak("Congratulations on completing your study session!")
        self.execute_marty_action('celebrate')
        time.sleep(2)
        self.execute_marty_action('eyes_excited')
        self.speak("You did an excellent job today!")

    # Handling initial study setup and first study session
    def initial_setup_and_study(self):
        """
        Handle initial study setup including subject selection,
        accompaniment preference, music selection, and first study session.
        """
        self.speak("Please prepare your study materials.")
        self.speak(f"You have {self.time_config['preparation']} seconds to get ready.")
        time.sleep(self.time_config['preparation'])
        self.speak("Preparation time is over! Let's begin our learning journey.")

        # Step 1: Subject selection
        self.subject_selection()

        # Step 2: Accompaniment preference
        accompaniment_choice = self.ask_for_accompaniment()

        # Step 3: Music selection for study
        self.ask_music_preference(is_study=True)

        # Step 4: Resume music based on user choice
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

        # Step 5: Start first study session
        self.speak(f"Starting the first study segment ({self.time_config['study_session']} minutes).")
        self.learning_timer(self.time_config['study_session'])

    # Main study session workflow coordinating all components
    def start_study_session(self):
        """
        Main study session workflow that coordinates all components:
        - Robot initialization and greeting
        - Mood assessment
        - Study setup and sessions
        - Break management
        - Final celebration and feedback
        """
        if not self.marty:
            print("Marty not connected, cannot start study session")
            return

        try:
            # Open Spotify web player for user convenience
            print("Opening Spotify web player...")
            webbrowser.open("https://open.spotify.com")
            time.sleep(2)

            # Initial robot setup and greeting
            self.execute_marty_action('get_ready')
            time.sleep(0.5)
            self.speak("Hello! I'm Marty, your personal study assistant!")
            self.speak("I am moving closer to you.")
            self.execute_marty_action('walk_forward')
            self.execute_marty_action('get_ready')
            time.sleep(1)
            self.execute_marty_action('wave')

            # Mood assessment
            self.mood_selection()

            # Main study workflow
            self.initial_setup_and_study()

            # Break session
            self.speak("First study segment finished! Time for a quick break!")
            self.rest_timer(self.time_config['rest_session'])

            # Second study session
            self.speak("Break time is over! Starting next study segment.")
            self.ask_music_preference(is_study=True)
            self.speak("Let's return to focused study.")
            self.learning_timer(self.time_config['study_session'])

            # Celebration and final mood check
            self.celebration_sequence()

            # Final mood assessment
            self.speak("Now that we've finished our study session, how are you feeling now?")
            self.speak("Please tell me if you're feeling 'Happy' or 'Stressed'.")

            final_mood = self.wait_for_voice_selection(
                timeout=self.time_config['voice_selection_timeout'],
                expected_intent='express_mood'
            )

            # Respond to final mood
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

            # Cleanup and final message
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

    # Safely shutting down Marty robot connection
    def cleanup(self):
        """
        Safely shutdown Marty robot connection and perform cleanup.
        Handles connection termination errors gracefully.
        """
        try:
            if self.marty:
                self.marty.stop()
                print("Marty stopped")
                self.marty.close()
        except Exception as e:
            error_message = str(e)
            if "WinError 6" in error_message or "Handle is invalid" in error_message:
                print("Ignored harmless WinError 6 during final cleanup.")
            else:
                print(f"Cleanup failed but proceeding to exit: {e}")


# Main execution block
if __name__ == '__main__':
    # Create and start the study assistant session
    assistant = MartyStudyAssistant()
    assistant.start_study_session()