from martypy import Marty
import time


def detect_green_card():
    """
    Detect if Marty steps on a green card and display the reading
    """
    try:
        # Connect to Marty
        my_marty = Marty("usb", "COM3")

        # Define threshold range for green card (needs adjustment based on actual testing)
        GREEN_THRESHOLD_MIN = 200  # Minimum reading for green card
        GREEN_THRESHOLD_MAX = 400  # Maximum reading for green card

        print("Starting green card detection...")
        print("Please place the green card under Marty's left foot")
        print("Press Ctrl+C to stop detection\n")

        detection_count = 0

        while True:
            try:
                # Get left foot ground sensor reading
                sensor_reading = my_marty.get_ground_sensor_reading("left")

                # Check if within green threshold range
                if GREEN_THRESHOLD_MIN <= sensor_reading <= GREEN_THRESHOLD_MAX:
                    detection_count += 1
                    print(f"🎉 Green card detected! Sensor reading: {sensor_reading} (Detection #{detection_count})")

                    # Make Marty speak for confirmation
                    my_marty.speak("Green card detected!")

                    # Brief pause to avoid repeated detection
                    time.sleep(2)
                else:
                    print(f"Current sensor reading: {sensor_reading} - No green card detected")

                time.sleep(0.5)  # Detection interval

            except KeyboardInterrupt:
                print("\nDetection stopped")
                break
            except Exception as e:
                print(f"Error during detection: {e}")
                time.sleep(1)

    except Exception as e:
        print(f"Failed to connect to Marty: {e}")

    finally:
        # Ensure proper connection closure
        try:
            my_marty.close()
            print("Marty connection closed")
        except:
            pass


def calibrate_green_threshold():
    """
    Calibrate the threshold for green card
    """
    try:
        my_marty = Marty("usb", "COM3")

        print("Green card calibration mode")
        print("Please place the green card under Marty's left foot and hold for 3 seconds...")
        input("Press Enter to start calibration when ready...")

        readings = []
        print("Measuring green card readings...")

        start_time = time.time()
        while time.time() - start_time < 3:
            reading = my_marty.get_ground_sensor_reading("left")
            readings.append(reading)
            print(f"Current reading: {reading}")
            time.sleep(0.2)

        if readings:
            avg_reading = sum(readings) / len(readings)
            min_reading = min(readings)
            max_reading = max(readings)

            print(f"\nCalibration results:")
            print(f"Average reading: {avg_reading:.2f}")
            print(f"Minimum reading: {min_reading}")
            print(f"Maximum reading: {max_reading}")
            print(f"Recommended threshold range: {int(min_reading * 0.9)} - {int(max_reading * 1.1)}")

            # Update thresholds
            global GREEN_THRESHOLD_MIN, GREEN_THRESHOLD_MAX
            GREEN_THRESHOLD_MIN = int(min_reading * 0.9)
            GREEN_THRESHOLD_MAX = int(max_reading * 1.1)

            print(f"Updated threshold: {GREEN_THRESHOLD_MIN} - {GREEN_THRESHOLD_MAX}")

        my_marty.close()

    except Exception as e:
        print(f"Calibration failed: {e}")


def simple_green_detection():
    """
    Simple single green card detection
    """
    try:
        my_marty = Marty("usb", "COM3")

        # Default threshold (needs adjustment based on actual situation)
        GREEN_THRESHOLD_MIN = 200
        GREEN_THRESHOLD_MAX = 400

        # Get sensor reading
        reading = my_marty.get_ground_sensor_reading("left")

        print(f"Sensor reading: {reading}")

        # Determine if it's green
        if GREEN_THRESHOLD_MIN <= reading <= GREEN_THRESHOLD_MAX:
            print("✅ Green card detected!")
            my_marty.speak("I see green!")
            return True, reading
        else:
            print("❌ No green card detected")
            return False, reading

    except Exception as e:
        print(f"Detection failed: {e}")
        return False, None
    finally:
        try:
            my_marty.close()
        except:
            pass


# Usage example
if __name__ == "__main__":
    print("Select detection mode:")
    print("1. Continuous detection mode")
    print("2. Single detection")
    print("3. Calibrate green threshold")

    choice = input("Please select (1-3): ")

    if choice == "1":
        detect_green_card()
    elif choice == "2":
        result, reading = simple_green_detection()
        if result:
            print(f"Successfully detected green card, reading: {reading}")
        else:
            print(f"No green card detected, reading: {reading}")
    elif choice == "3":
        calibrate_green_threshold()
    else:
        print("Invalid selection")