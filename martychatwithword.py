from martypy import Marty
import time
import string


def robust_connect(connection_type, address, max_retries=5):
    for i in range(max_retries):
        try:
            print(f"Connection attempt {i + 1}/{max_retries}...")
            marty = Marty(connection_type, address)
            print("Testing basic communication...")
            battery = marty.get_battery_remaining()
            print(f"Battery level: {battery}%")
            print("✅ Marty connected successfully!")
            return marty
        except Exception as e:
            print(f"Connection failed: {e}")
            if i < max_retries - 1:
                wait_time = (i + 1) * 2
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
    print("❌ All connection attempts failed")
    return None


def execute_with_retry(marty, command, *args, max_retries=3, **kwargs):
    for i in range(max_retries):
        try:
            getattr(marty, command)(*args, **kwargs)
            return True
        except Exception as e:
            print(f"Command {command} failed on attempt {i + 1}: {e}")
            if i < max_retries - 1:
                time.sleep(1)
    print(f"❌ Command {command} failed after all retries")
    return False


def safe_speak(marty, text):
    if hasattr(marty, 'speak'):
        return execute_with_retry(marty, 'speak', text)
    else:
        print(f"Marty says: {text}")
        return True


def text_input(prompt, options=None):
    print(f"\n{prompt}")
    if options:
        print("Options: " + " / ".join(options))

    while True:
        user_input = input("Please enter: ").strip().lower()
        if not user_input:
            print("Please enter a valid response")
            continue

        if options:
            for option in options:
                if option.lower() in user_input or user_input in option.lower():
                    return option
            print(f"Please choose from: {', '.join(options)}")
        else:
            return user_input


def extract_keywords(text):
    if not text:
        return []
    return text.translate(str.maketrans('', '', string.punctuation)).split()


def study_session_flow(marty):
    print("\n" + "=" * 50)
    print("Marty Study Assistant - Text Mode")
    print("=" * 50)

    safe_speak(marty, "Hello, welcome to Marty Study Assistant!")

    mood = text_input("How are you feeling today?", ["Great", "Good", "Okay", "Tired", "Not good"])

    if mood in ["Great", "Good"]:
        safe_speak(marty, "That's wonderful! Let's keep this positive energy!")
    elif mood in ["Okay", "Tired"]:
        safe_speak(marty, "Maybe studying will help you feel more energized!")
    else:
        safe_speak(marty, "Studying is a great way to improve your mood!")

    subject = text_input("What subject would you like to study today?",
                         ["English", "Math", "Programming", "Science", "Other"])

    if subject == "English":
        handle_english_session(marty)
    elif subject == "Math":
        handle_math_session(marty)
    elif subject == "Programming":
        handle_programming_session(marty)
    elif subject == "Science":
        handle_science_session(marty)
    else:
        handle_generic_session(marty, subject)


def handle_english_session(marty):
    safe_speak(marty, "Excellent choice! English is a great subject to study!")

    study_type = text_input("What type of English study would you like to do?",
                            ["Reading", "Listening", "Vocabulary", "Speaking"])

    safe_speak(marty, f"Starting {study_type} practice!")

    set_timer = text_input("Would you like to set a study timer?", ["Yes", "No"])

    if set_timer == "Yes":
        timer_type = text_input("Choose timer type", ["Standard", "Pomodoro"])

        if timer_type == "Standard":
            safe_speak(marty, "English study timer started! Recommended: 45 minutes study, 10 minutes break.")
            start_standard_timer(marty, "English")
        else:
            safe_speak(marty, "Pomodoro technique started! 25 minutes study, 5 minutes break.")
            start_pomodoro_timer(marty, "English")
    else:
        safe_speak(marty, "Okay, free study mode it is!")


def handle_math_session(marty):
    safe_speak(marty, "Math is great for training your mind!")

    math_topic = text_input("What math topic would you like to study?",
                            ["Algebra", "Geometry", "Calculus", "Statistics", "Arithmetic"])

    safe_speak(marty, f"{math_topic} is an interesting topic!")

    music = text_input("Would you like background music while studying?", ["Yes", "No"])

    if music == "Yes":
        music_type = text_input("Choose music type", ["Classical", "Ambient", "Instrumental"])
        safe_speak(marty, f"Playing {music_type} to help you focus!")
    else:
        safe_speak(marty, "Quiet environment is also great for math thinking!")

    set_timer = text_input("Would you like to set a math study timer?", ["Yes", "No"])

    if set_timer == "Yes":
        safe_speak(marty, "Math study timer started! Recommended: 20 minutes study, 3 minutes break.")
        start_math_timer(marty)
    else:
        safe_speak(marty, "Okay, study at your own pace!")


def handle_programming_session(marty):
    safe_speak(marty, "Programming is a skill for creating the future!")

    language = text_input("What programming language would you like to learn?",
                          ["Python", "Java", "JavaScript", "C++", "Other"])

    safe_speak(marty, f"{language} is a powerful programming language!")

    project_type = text_input("What type of project would you like to work on?",
                              ["Web Development", "Data Analysis", "AI", "Game Development", "Learning Basics"])

    safe_speak(marty, f"Starting {project_type} project!")
    start_programming_timer(marty)


def handle_science_session(marty):
    safe_speak(marty, "Science helps us explore the mysteries of the world!")

    science_field = text_input("Which science field interests you?",
                               ["Physics", "Chemistry", "Biology", "Astronomy", "Earth Science"])

    safe_speak(marty, f"{science_field} is full of fascinating discoveries!")
    start_science_timer(marty)


def handle_generic_session(marty, subject):
    safe_speak(marty, f"{subject} is a valuable field of study!")

    set_timer = text_input("Would you like to set a study timer?", ["Yes", "No"])

    if set_timer == "Yes":
        safe_speak(marty, f"{subject} study timer started! Recommended: 50 minutes study, 10 minutes break.")
        start_standard_timer(marty, subject)
    else:
        safe_speak(marty, "Happy studying!")


def start_standard_timer(marty, subject):
    print(f"\n⏰ {subject} standard study timer started!")
    print("Recommended: 50 minutes study → 10 minutes break")
    execute_with_retry(marty, 'hello')
    time.sleep(1)


def start_pomodoro_timer(marty, subject):
    print(f"\n🍅 {subject} Pomodoro technique started!")
    print("Pattern: 25 minutes study → 5 minutes break × 4 → 15 minutes long break")
    execute_with_retry(marty, 'hello')
    time.sleep(1)


def start_math_timer(marty):
    print(f"\n📐 Math chunking study timer started!")
    print("Pattern: 20 minutes study → 3 minutes break × 3 → 10 minutes long break")
    execute_with_retry(marty, 'hello')
    time.sleep(1)


def start_programming_timer(marty):
    print(f"\n💻 Programming deep work timer started!")
    print("Pattern: 90 minutes deep work → 20 minutes break")
    execute_with_retry(marty, 'hello')
    time.sleep(1)


def start_science_timer(marty):
    print(f"\n🔬 Science exploration timer started!")
    print("Pattern: 40 minutes study → 10 minutes break → 40 minutes practice")
    execute_with_retry(marty, 'hello')
    time.sleep(1)


def main():
    print("Marty Study Assistant starting...")

    marty = robust_connect("usb", "/dev/ttyUSB0")

    if not marty:
        print("Unable to connect to Marty, program exiting.")
        return

    try:
        execute_with_retry(marty, 'hello')
        time.sleep(2)

        study_session_flow(marty)

        safe_speak(marty, "Study plan is all set! Happy learning!")
        execute_with_retry(marty, 'dance')

        print("\n🎉 Study session completed!")
        print("Marty has set up your study plan, time to focus on learning!")

    except Exception as e:
        print(f"Program execution error: {e}")
    finally:
        try:
            marty.close()
            print("Connection closed")
        except:
            pass


if __name__ == "__main__":
    main()