from martypy import Marty
import time

# Connect to your Marty (replace with robots IP)
marty = Marty("wifi", "192.168.0.42")

# Marty waves hello
marty.hello()             

# Marty walks 2 steps forward
marty.walk(2)             

# Marty turns left 90 degrees
marty.turn(-90)      

# Marty performs a pre-programmed dance
marty.dance()          

# Marty Speaks
marty.say("Hello, world!")


#WALK TO COLOUR SEQUENCE

#Warms up robot for movement
marty.enable_motors()

print("Start walking...") 

try:
    while True:
        # Movement and pause to scan
        marty.walk(2)
        time.sleep(0.5)

        # Read color sensor (I dont know which one we have)
        color_left = marty.get_color_sensor("left")
        color_right = marty.get_color_sensor("right")

        print(f"Left: {color_left}, Right: {color_right}")

        # Check for red 
        if color_left == "red" or color_right == "red":
            print("Red detected. Stopping.")
            marty.stop()
            break

#Manual control 
except KeyboardInterrupt:
    print("Stopped manually.")
    marty.stop()

#Rests robot and prevents movement
marty.disable_motors()