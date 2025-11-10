import martypy
import time
import threading
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser
import sys
import random

# --- Connection Types (Defined for clarity) ---
USB = 'usb'
WIFI = 'wifi'

# --- Colors (Defined for clarity) ---
RED = 'Red'
GREEN = 'Green'
BLUE = 'Blue'
YELLOW = 'Yellow'
PURPLE = 'Purple'
TIMEOUT = 'Timeout'

# --- Simplified Marty Connection (Set your connection type and port here) ---
# NOTE: Replace 'COM3' with your actual port or IP if using WIFI.
# For USB on Windows, it might be 'COM3'. For WIFI, use 'wifi', ip_address='192.168.x.x'
MARTY_CONNECTION = martypy.Marty(USB, 'COM3', blocking=True)


class MartyStudyAssistant:
    def __init__(self):
        # Initialize Marty Study Assistant and its configurations.

        # Marty connection is simplified to one line outside the class
        self.marty = MARTY_CONNECTION
        print("Marty connection setup complete.")

        # --- Color Sensor Calibration Values (Updated per user request) ---
        self.COLOR_VALUES = {
            RED: 100,
            GREEN: 32,
            BLUE: 38,
            YELLOW: 110,
            PURPLE: 29
        }
        self.COLOR_TOLERANCE = 2

        # Spotify configuration
        self.spotify_client_id = 'a8a3a043933f425488667bd51cb69f68'
        self.spotify_client_secret = 'bfcd14a8e3d247eaae927180c088d123'
        self.spotify_redirect_uri = 'http://127.0.0.1:8888/callback'
        # Added scopes for playback control
        SPOTIPY_SCOPE = 'playlist-read-private user-read-playback-state user-modify-playback-state'

        # Initialize Spotify client
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=self.spotify_client_id,
                client_secret=self.spotify_client_secret,
                redirect_uri=self.spotify_redirect_uri,
                scope=SPOTIPY_SCOPE,
                # Force refresh token to ensure new scope takes effect
                cache_path=".spotipyoauthcache"
            ))
            print("Spotify client initialized successfully! Please check your browser for login.")
            self.spotify_available = True
        except Exception as e:
            print(f"Spotify client initialization failed: {e}")
            self.spotify_available = False

        # Optimized time configuration (Pomodoro inspired)
        self.time_config = {
            'color_selection': 5,
            'preparation': 20,
            'study_session': 25,
            'rest_session': 5,
        }

        if self.marty:
            print("Marty connected successfully!")
        else:
            print("Marty connection failed or was not fully set up outside the class.")

    def is_close(self, val, target, tolerance=None):
        # Check if a sensor value is close to a target value.
        if tolerance is None:
            tolerance = self.COLOR_TOLERANCE
        return (target - tolerance) <= val <= (target + tolerance)

    def speak(self, text):
        # Make Marty speak, with a substantial delay to prevent errors and control pace.
        print(f"Marty says: {text}")
        try:
            if self.marty:
                self.marty.speak(text)
                # CRITICAL FIX: Add a substantial delay (1.5 seconds) after speaking
                # to allow the audio to play and the temp.mp3 file to be released.
                time.sleep(1.5)
        except Exception as e:
            print(f"Marty speak failed: {e}")

    def get_color_sensor_color(self, sensor_name):
        # Get RAW color value from Marty's ground sensor with error handling
        try:
            if self.marty:
                return self.marty.get_ground_sensor_reading(sensor_name)
            else:
                return -1
        except Exception as e:
            print(f"Error reading color sensor {sensor_name}: {e}")
            return -1

    def wait_for_color_selection(self, timeout=5, valid_colors=None):
        # Wait for color selection with timeout - using integer ground sensor values
        if valid_colors is None:
            valid_colors = []

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Assume LeftColorSensor is used for color detection
                raw_value = self.get_color_sensor_color('LeftColorSensor')

                # Check against calibrated values
                if self.is_close(raw_value, self.COLOR_VALUES[RED]):
                    print(f"Red detected (Value: {raw_value})")
                    return RED
                elif self.is_close(raw_value, self.COLOR_VALUES[GREEN]):
                    print(f"Green detected (Value: {raw_value})")
                    return GREEN
                elif self.is_close(raw_value, self.COLOR_VALUES[BLUE]):
                    print(f"Blue detected (Value: {raw_value})")
                    return BLUE
                elif self.is_close(raw_value, self.COLOR_VALUES[YELLOW]):
                    print(f"Yellow detected (Value: {raw_value})")
                    return YELLOW
                elif self.is_close(raw_value, self.COLOR_VALUES[PURPLE]):
                    print(f"Purple detected (Value: {raw_value})")
                    return PURPLE

            except Exception as e:
                print(f"Error in color detection: {e}")

            time.sleep(0.3)

        return TIMEOUT

    def execute_marty_action(self, action_name):
        # Execute Marty action using CORRECT API format
        if not self.marty:
            print(f"Marty not connected, cannot execute action: {action_name}")
            return "Marty not available"

        action_name = action_name.strip().lower()

        try:
            result = ""
            if action_name == 'dance':
                self.marty.dance()
                result = "Dancing now!"
            elif action_name == 'wave':
                self.marty.wave(side='left')
                time.sleep(1)
                self.marty.wave(side='right')
                result = "Waving hello!"
            elif action_name == 'celebrate':
                self.marty.celebrate()
                result = "Celebrating!"
            elif action_name == 'walk_forward':
                # Walk steps set to 10
                self.marty.walk(num_steps=10, start_foot='auto', turn=0, step_length=30, move_time=1500)
                result = "Moving forward!"
            elif action_name == 'stop':
                self.marty.stop()
                result = "Stopped!"
            elif action_name == 'get_ready':
                self.marty.get_ready()
                result = "Ready!"
            elif action_name == 'eyes_excited':
                self.marty.eyes(pose='excited')
                result = "Eyes excited!"
            elif action_name == 'eyes_normal':
                self.marty.eyes(pose='normal')
                result = "Eyes normal!"
            else:
                result = f"Unknown action: {action_name}"

            # Initialization after action (only for major actions)
            if action_name not in ['get_ready', 'eyes_excited', 'eyes_normal', 'stop']:
                # Ensure Marty is straight after movement/celebration
                self.marty.get_ready()

            return result
        except Exception as e:
            print(f"Action execution failed: {e}")
            return "Action execution failed"

    # --- FINALIZED: Ask for accompaniment with safest turning movement ---
    def ask_for_accompaniment(self):
        # Asks if the user wants Marty's accompaniment during the study session.
        self.speak("Would you like me to stay and keep you company?")
        self.speak("Green card for YES, I will stay right here.")
        self.speak("Red card for NO, I will turn and walk back to give you space.")
        self.speak("Please show your choice in 5 seconds.")

        selected_color = self.wait_for_color_selection(
            timeout=5,
            valid_colors=[RED, GREEN]
        )

        if selected_color == GREEN:
            self.speak("Green detected. Great! I'll be quiet and keep you company. Good luck!")
            self.execute_marty_action('eyes_excited')
        elif selected_color == RED:
            self.speak("Red detected. Okay, I understand, you need some quiet space.")

            # --- Perform Smoother Turn and Walk Away ---
            try:
                if self.marty:
                    # 1. Turn 150 degrees slowly (5 steps of 30 degrees)
                    self.speak("I am turning around now...")
                    for _ in range(5):  # 5 steps * 30 degrees = 150 degrees
                        # Use small turn angle (30 degrees) and slow time
                        self.marty.walk(num_steps=1, turn=30, step_length=0, move_time=1500)

                    # 2. Walk FORWARD relative to its new face direction (walking away)
                    # Walk steps set to 10
                    self.speak("Stepping away to give you space...")
                    self.marty.walk(num_steps=10, step_length=25, move_time=2000)

                    # 3. Turn back to face the user (5 steps of -30 degrees = -150 degrees)
                    self.speak("I'll be nearby if you need anything!")
                    for _ in range(5):
                        self.marty.walk(num_steps=1, turn=-30, step_length=0, move_time=1500)

                    # 4. Initialize posture after moving
                    self.execute_marty_action('get_ready')

            except Exception as e:
                print(f"Walk away sequence failed: {e}")
        else:
            self.speak("No selection detected. I will stay here by default.")
            self.execute_marty_action('eyes_excited')
            self.execute_marty_action('get_ready')

    def play_spotify_music(self, genre):
        # Search for a Spotify playlist and attempt to start playback on the active device.
        if not self.spotify_available:
            self.speak("Spotify service is currently unavailable")
            return False

        self.speak(f"Searching for {genre} music and attempting to start playback automatically.")

        try:
            # 1. Search for a playlist by genre
            results = self.sp.search(q=f"{genre} study", type='playlist', limit=1)

            if not results or not results['playlists']['items']:
                self.speak("Could not find suitable playlist for this genre")
                return False

            playlist_name = results['playlists']['items'][0]['name']
            # 2. Get the Spotify URI (e.g., spotify:playlist:ID)
            playlist_uri = results['playlists']['items'][0]['uri']

            # 3. Use start_playback method to automatically start playing
            self.sp.start_playback(context_uri=playlist_uri)

            print(f"[Spotify] Starting playback of playlist: {playlist_name}")
            self.speak(
                f"I started playing the playlist: {playlist_name} automatically. Please check your Spotify device.")
            return True

        except Exception as e:
            # Fallback to opening the web player if API playback fails
            print(f"Spotify API playback failed: {e}. Opening Web Player instead.")
            self.speak("Automatic playback failed. Opening the Web Player. You will need to press play manually.")

            # Fallback: Open web link
            try:
                playlist_url = results['playlists']['items'][0]['external_urls']['spotify']
                webbrowser.open(playlist_url)
            except:
                self.speak("Error finding music")
                return False

            return False

    def stop_spotify_music(self):
        # Attempt to pause music via API (Premium user required)
        # NOTE: This is primarily used for the hard stop (RED card) and final cleanup.
        if not self.spotify_available:
            return False

        try:
            self.sp.pause_playback()
            self.speak("I have sent a pause command to your Spotify player. Please verify the music has stopped.")
            print("[Spotify] Pause playback command sent.")
            return True
        except Exception as e:
            self.speak("I cannot remotely stop the music. Please manually pause the music.")
            print(f"[Spotify] Music playback pause failed: {e}. Manual pause is required.")
            return False

    def ask_music_preference(self, is_study=True):
        # Ask for music preference - before the study session.
        if not is_study:
            # ***Music persistence: This new music will overwrite the previous one.***
            self.speak("Now, let's select soothing ambient music for your rest session.")
            self.play_spotify_music('soothing ambient')
            return

        self.speak("Now, let's select some background music for your study session.")
        self.speak("Red card for Lo-fi study music")
        self.speak("Green card for Jazz music")
        self.speak("Blue card for Classical music")
        self.speak("Yellow card for Ambient music")
        self.speak("You have 5 seconds to show your color choice.")

        selected_color = self.wait_for_color_selection(
            timeout=self.time_config['color_selection'],
            valid_colors=[RED, GREEN, BLUE, YELLOW]
        )

        # ***Music persistence: The new music will overwrite the existing one.***

        if selected_color == RED:
            self.speak("Red detected, playing Lo-fi music.")
            self.play_spotify_music('lofi study')
        elif selected_color == GREEN:
            self.speak("Green detected, playing Jazz music.")
            self.play_spotify_music('jazz')
        elif selected_color == BLUE:
            self.speak("Blue detected, playing Classical music.")
            self.play_spotify_music('classical')
        elif selected_color == YELLOW:
            self.speak("Yellow detected, playing Ambient music.")
            self.play_spotify_music('ambient')
        else:
            self.speak("No selection detected, playing default Lo-fi study music.")
            self.play_spotify_music('lofi study')

    def mood_selection(self):
        # Mood selection: Red for bad mood, Green for good mood
        self.speak("Please tell me how you are feeling today:")
        self.speak("Green card for Happy and Positive (Good Mood)")
        self.speak("Red card for Stressed or Tired (Bad Mood)")
        self.speak("Show your mood color in 5 seconds.")

        selected_color = self.wait_for_color_selection(
            timeout=self.time_config['color_selection'],
            valid_colors=[GREEN, RED]
        )

        if selected_color == GREEN:
            self.speak("Green detected, you are in a good mood! Positive energy is great for learning!")
            self.execute_marty_action('celebrate')
        elif selected_color == RED:
            self.speak("Red detected. You seem stressed or tired. Let's get some relaxing music for you.")
            self.execute_marty_action('wave')

            # Play calming music for a bad mood
            self.play_spotify_music('calm soothing piano')
            self.speak("I opened a calming music playlist for you. Take a deep breath and relax.")
            time.sleep(5)  # Pause for breath
            # ***MODIFICATION***: Removed stop_spotify_music() here to keep Spotify active.
            self.speak("Now, let's start fresh with our study session.")

        else:
            self.speak("No selection detected, I assume you are ready to learn!")
            self.execute_marty_action('wave')

    def subject_selection(self):
        # Subject selection
        self.speak("What subject would you like to study?")
        self.speak("Blue card for Science subjects")
        self.speak("Purple card for Mathematics")
        self.speak("Yellow card for Languages")
        self.speak("Please show your subject choice in 5 seconds.")

        selected_color = self.wait_for_color_selection(
            timeout=self.time_config['color_selection'],
            valid_colors=[BLUE, PURPLE, YELLOW]
        )

        if selected_color == BLUE:
            self.speak("Blue detected, Science subject selected. Excellent choice!")
            return 'science'
        elif selected_color == PURPLE:
            self.speak("Purple detected, Math subject selected. You can do it!")
            return 'math'
        elif selected_color == YELLOW:
            self.speak("Yellow detected, Language subject selected. Wonderful!")
            return 'language'
        else:
            self.speak("No selection detected, proceeding with general studies.")
            return 'general'

    def start_timer(self, duration_seconds, activity_name, interrupt_color=RED):
        # Generic timer function
        self.speak(f"Starting the {activity_name} for {duration_seconds // 60} minutes.")
        self.speak(f"Show the {interrupt_color} card at any time to stop the activity.")

        stop_event = threading.Event()

        def timer_thread():
            end_time = time.time() + duration_seconds
            while time.time() < end_time and not stop_event.is_set():
                time.sleep(1)
            if not stop_event.is_set():
                self.speak(f"{activity_name} completed! Well done!")

        def monitor_thread():
            while not stop_event.is_set():
                raw_value = self.get_color_sensor_color('LeftColorSensor')

                if self.is_close(raw_value, self.COLOR_VALUES[RED]):
                    stop_event.set()
                    self.speak("Red detected, activity stopped as requested.")
                    self.stop_spotify_music()  # Attempt to pause music for the hard stop
                    break
                time.sleep(0.5)

        timer = threading.Thread(target=timer_thread)
        monitor = threading.Thread(target=monitor_thread)

        timer.start()
        monitor.start()
        timer.join()
        if monitor.is_alive():
            monitor.join(timeout=1)

    def learning_timer(self, duration_minutes=25):
        # Study timer
        self.start_timer(
            duration_seconds=duration_minutes * 60,
            activity_name=f"{duration_minutes} minute study session"
        )

    def rest_timer(self, duration_minutes=5):
        # Rest timer (Music switch)

        # **Music persistence**: No need to stop previous music, the next play_spotify_music will overwrite it.
        # self.stop_spotify_music() # REMOVED

        self.speak("Now, let's start our quick break!")

        # Start rest music (This will overwrite the study music)
        self.ask_music_preference(is_study=False)

        self.start_timer(
            duration_seconds=duration_minutes * 60,
            activity_name=f"{duration_minutes} minute break"
        )

        # ***MODIFICATION***: Removed stop_spotify_music() here to keep Spotify active.

    def celebration_sequence(self):
        # Celebration sequence
        self.speak("Congratulations on completing your study session!")
        self.execute_marty_action('celebrate')
        time.sleep(2)
        self.execute_marty_action('eyes_excited')
        self.speak("You did an excellent job today!")

    # --- Setup stage reflecting the new flow ---
    def initial_setup_and_study(self):
        # Combined setup for subject, music, accompaniment, and first study segment.

        # Preparation time
        self.speak("Please prepare your study materials.")
        self.speak(f"You have {self.time_config['preparation']} seconds to get ready.")
        time.sleep(self.time_config['preparation'])

        self.speak("Preparation time is over! Let's begin our learning journey.")

        # 1. Subject selection
        self.subject_selection()

        # 2. Music selection and play (Study Music starts here)
        # Note: If mood_selection played music, this will overwrite it.
        self.ask_music_preference(is_study=True)

        # 3. Accompaniment check
        self.ask_for_accompaniment()

        # 4. Start first study session
        self.speak(f"Starting the first study segment ({self.time_config['study_session']} minutes).")
        self.learning_timer(self.time_config['study_session'])

    # --- CORE PIPELINE IMPLEMENTATION (Matching User's Demo Request) ---
    def start_study_session(self):
        # Start complete study session following the demo pipeline.
        if not self.marty:
            print("Marty not connected, cannot start study session")
            return

        try:
            # 1. Marty switches on and prepares
            self.execute_marty_action('get_ready')
            time.sleep(0.5)

            # 2. Moves towards us
            self.speak("Hello! I'm Marty, your personal study assistant!")
            self.speak("I am moving closer to you.")
            self.execute_marty_action('walk_forward')
            # Initialization after walk_forward
            self.execute_marty_action('get_ready')
            time.sleep(1)

            # 3. Greets and asks about mood (Plays calming music if mood is Red)
            self.execute_marty_action('wave')
            self.mood_selection()

            # 4. Subject, Music, Accompaniment, and Study Segment 1 (Music starts/overwrites here)
            self.initial_setup_and_study()

            # 5. Break time (Music switches to ambient)
            self.speak("First study segment finished! Time for a quick break!")
            self.rest_timer(self.time_config['rest_session'])

            # 6. One more study segment after the break
            # New study music starts here, overwriting the ambient rest music
            self.speak("Break time is over! Starting next study segment.")
            self.ask_music_preference(is_study=True)  # Re-select/start study music

            self.speak("Let's return to focused study.")
            self.learning_timer(self.time_config['study_session'])

            # 7. Ends it off with a well done and a dance
            self.celebration_sequence()

            # Final music stop and cleanup (Hard stop at the very end)
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
        # Clean up resources
        try:
            if self.marty:
                self.marty.stop()
                print("Marty stopped")
                self.marty.close()
        except Exception as e:
            print(f"Cleanup failed but proceeding to exit: {e}")
            pass


# Usage example
if __name__ == '__main__':
    # Initialize the assistant (uses the MARTY_CONNECTION defined above)
    assistant = MartyStudyAssistant()
    assistant.start_study_session()