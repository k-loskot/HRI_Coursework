from martypy import Marty
import time


def robust_connect(connection_type, address, max_retries=5):
    for i in range(max_retries):
        try:
            print(f"Connection attempt {i + 1}/{max_retries}...")
            marty = Marty(connection_type, address)
            print("Testing basic communication...")
            battery = marty.get_battery_remaining()
            print(f"Battery level: {battery}%")
            print("Connection successful!")
            return marty
        except Exception as e:
            print(f"Connection failed: {e}")
            if i < max_retries - 1:
                wait_time = (i + 1) * 2
                print(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
    print("All connection attempts failed")
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
    print(f"Command {command} failed after all retries")
    return False


def get_actual_methods(marty):
    available_methods = ['dance', 'enable_motors', 'get_battery_remaining', 'hello', 'stop', 'walk']
    additional_checks = ['say', 'kick', 'eyes', 'lean']
    for method in additional_checks:
        if hasattr(marty, method):
            available_methods.append(method)
    print("Available methods:", sorted(available_methods))
    return available_methods


def basic_movement_test(marty):
    print("\n=== Basic Movement Test ===")
    if execute_with_retry(marty, 'hello'):
        time.sleep(3)
    if execute_with_retry(marty, 'walk', 2):
        time.sleep(2)
    if execute_with_retry(marty, 'dance'):
        time.sleep(5)
    if hasattr(marty, 'kick'):
        print("Testing kick action...")
        if execute_with_retry(marty, 'kick', 'left'):
            time.sleep(2)
    if hasattr(marty, 'eyes'):
        print("Testing eye action...")
        if execute_with_retry(marty, 'eyes', 50):
            time.sleep(1)
        if execute_with_retry(marty, 'eyes', 0):
            time.sleep(1)


def simple_walk_sequence(marty, steps=8):
    print(f"\n=== Simple Walk Test ({steps} steps) ===")
    if hasattr(marty, 'enable_motors'):
        execute_with_retry(marty, 'enable_motors')
    try:
        for i in range(steps):
            print(f"Walking {i + 1}/{steps}")
            if execute_with_retry(marty, 'walk', 1):
                time.sleep(0.5)
            else:
                break
            if (i + 1) % 3 == 0:
                try:
                    battery = marty.get_battery_remaining()
                    print(f"Battery level: {battery}%")
                except:
                    pass
    except KeyboardInterrupt:
        print("Manually stopped")
    except Exception as e:
        print(f"Walking error: {e}")
    finally:
        execute_with_retry(marty, 'stop')


def advanced_movement_test(marty):
    print("\n=== Advanced Movement Test ===")
    print("Attempting parameterized walking...")
    if execute_with_retry(marty, 'walk', 2, step_length=30, move_time=2000):
        time.sleep(2)
    try:
        marty.walk(2, turn=20)
        time.sleep(2)
    except Exception as e:
        print(f"Walking with turn parameter failed: {e}")
        try:
            if hasattr(marty, 'circles'):
                marty.circles(1, 'left')
                time.sleep(2)
        except:
            print("No turning methods available")


def main():
    print("Marty Robot Optimization Test Program")
    print("=" * 40)
    my_marty = robust_connect("usb", "/dev/ttyUSB0")
    if not my_marty:
        print("\n Troubleshooting suggestions:")
        print("1. Check if Marty is fully powered on")
        print("2. Replug USB cable")
        print("3. Restart Marty")
        return
    available_methods = get_actual_methods(my_marty)
    basic_movement_test(my_marty)
    simple_walk_sequence(my_marty, steps=6)
    advanced_movement_test(my_marty)
    print("\n Test completed!")
    try:
        my_marty.close()
    except:
        pass


if __name__ == "__main__":
    main()
