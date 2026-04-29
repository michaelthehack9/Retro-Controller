from pynput.keyboard import Key, Controller
from copy import deepcopy
import argparse
import serial
import time
import json
import os

file_name = "keybinds.json"

profiles = {
    "default": {
        256: "w",
        128: "a",
        64: "s",
        32: "d",
        16: "KEY_SHIFT_L",
        8: "KEY_ENTER",
        4: "z",
        2: "x",
        1: "c"
    }}

profile = "default"

keyboard = Controller()

keysPressed = set()

SPECIAL_KEYS = {
    "KEY_ENTER": Key.enter,
    "KEY_SHIFT_L": Key.shift_l
}

def main():
    global profile

    args = get_arguments()

    loadKeybinds()
    
    if (args.profile and args.profile.lower() in profiles):
        profile = args.profile.lower()

    baud = args.baud
    port_name = args.port

    if args.autoconnect:
        connectToArduino(baud, port_name)
    else:
        menu(baud, port_name)
    
    saveKeybinds()

def menu(baud, port_name):
    running = True
    while running:
        print("Please select an option:\n")
        options = ("Exit", "Profile Menu", "Keybind Menu", "Connect To Controller")
        i = 0
        for option in options:
            numOfDashes = 2 * (len(options) - i + 1)
            print(f"{'-' * numOfDashes} {i + 1}) {option}")
            i += 1
        selection = input("--> ")
        clear_screen()
        if selection.isnumeric():
            match int(selection):
                case 1:
                    running = False
                case 2:
                    profileMenu()
                case 3:
                    keybindMenu()
                case 4:
                    connectToArduino(baud, port_name)

def profileMenu():
    global profile
    running = True

    while running:
        viewProfiles()
        selProfile = input(f"\nWhat profile would you like to load? {'(-3 to delete) ' if len(profiles) > 1 else ''}(-2 to create) (-1 to cancel): ")
        clear_screen()
        if selProfile == "-1":
            running = False
        elif selProfile == "-2":
            createProfile()
        elif selProfile == "-3" and len(profiles) > 1:
            deleteProfile()
        else:
            if selProfile.lower() in profiles:
                profile = selProfile.lower()
            else:
                print("Profile not found, please try again!\n")

def deleteProfile():
    nameChecking = True

    while nameChecking:
        viewProfiles()
        chosenProfile = input("\nWhat profile would you like to delete? (-1 to cancel): ").lower()
        clear_screen()
        
        global profiles

        if chosenProfile == "-1":
            nameChecking = False
        elif chosenProfile in profiles:
            confirmation = input(f"Are you sure you would like to delete {chosenProfile.upper()} from the profile list? (y or N): ")
            clear_screen()

            if confirmation.lower() == "y":

                del profiles[chosenProfile]

                global profile
                if profile not in profiles:
                    profile = next(iter(profiles))

                nameChecking = False

                print(f"{chosenProfile} has been deleted successfully!\n")

                saveKeybinds()
            else:
                print("Cancelling...\n")
        else:
            print("Please enter an existing profile name!\n")

def createProfile():
    nameChecking = True

    while nameChecking:
        viewProfiles()
        newProfile = input("\nWhat would you like to name the profile? (-1 to cancel): ").lower()
        clear_screen()

        if newProfile == "-1":
            nameChecking = False
        elif len(newProfile) > 0 and len(newProfile) <= 24:
            global profiles

            if newProfile in profiles:
                print("Please enter a name that doesn't already exist!\n")
            else:
                confirmation = input(f"Are you sure you would like to set the name of your new profile to {newProfile.upper()}? (y or N): ")
                clear_screen()

                if confirmation.lower() == "y":
                    global profile

                    profiles[newProfile] = deepcopy(profiles[profile])
                    profile = newProfile

                    nameChecking = False

                    print(f"{profile} has been created successfully!\n")
                
                    saveKeybinds()
                else:
                    print("Cancelling...\n")
        else:
            print("Please enter a name between 1-24 characters!\n")

def viewProfiles():
    print("Profiles:\n")
    for p in profiles:
        if (p == profile):
            print(f"{'-->':>3} {p.upper()}")
        else:
            print(f"{'':>3} {p.upper()}")

def loadKeybinds():
    if os.path.exists(file_name):
        with open(file_name, "r") as infile:
            data = json.load(infile)
        
        global profiles
        global profile

        profiles = data["profiles"]
        profile = data["last_profile"]

        for p in profiles:
            profileKeybinds = {}

            for button, key in profiles[p].items():
                profileKeybinds[int(button)] = key
            
            profiles[p] = profileKeybinds

def saveKeybinds():
    data = {"last_profile": profile, "profiles": profiles}

    with open(file_name, "w") as outfile:
        json.dump(data, outfile, indent=4)

def keybindMenu():
    running = True
    while running:
        viewKeybinds()
        invalidSwitch = True
        switch = ""
        while invalidSwitch:
            switch = input("\nEnter the switch you would like to change (-2 to reset to defaults) (-1 to cancel): ")
            if switch == "-1":
                invalidSwitch = False
                running = False
            elif switch.lower() in ("up", "left", "down", "right", "green", "yellow", "blue", "white", "red", "-2"):
                invalidSwitch = False
            else:
                clear_screen()
                print("Invalid selection please try again!\n")
                viewKeybinds()
        clear_screen()
        confirming = True
        while confirming and running:
            key = ""
            if switch.lower() == "-2":
                key = "-2"
            else:
                key = input(f"Enter the key you would like to set to the {switch} switch (-1 to cancel): ")
            
            if key == "-1":
                clear_screen()
                confirming = False
            elif (key.isalnum() and len(key) == 1) or key == "-2":
                clear_screen()
                if key == "-2":
                    confirm = input(f"Are you sure you would like to reset keybinds to factory defaults? (y or N): ")
                else:
                    confirm = input(f"Are you sure you would like to set the {switch} switch keybind to {key}? (y or N): ")
                clear_screen()
                if confirm.lower() == "y":
                    if key == "-2":
                        defaults = {"up": "w", "left": "a", "down": "s", "right": "d", "green": "KEY_SHIFT_L", "yellow": "KEY_ENTER", "blue": "z", "white": "x", "red": "c"}
                        for switchC in defaults:
                            setKeybind(switchC, defaults[switchC])
                        print("Successfully reset keybinds!\n")
                    else:
                        setKeybind(switch.lower(), key.lower())
                        print("Successfully set keybind!\n")
                    
                    saveKeybinds()
                else:
                    print("Cancelling!\n")
                
                confirming = False
            else:
                clear_screen()
                print("Invalid key, please try again!\n")

def setKeybind(strSwitch, key):
    switch = None
    
    match strSwitch:
        case "up":
            switch = 256
        case "left":
            switch = 128
        case "down":
            switch = 64
        case "right":
            switch = 32
        case "green":
            switch = 16
        case "yellow":
            switch = 8
        case "blue":
            switch = 4
        case "white":
            switch = 2
        case "red":
            switch = 1
    
    if switch is not None:
        profiles[profile][switch] = key

def viewKeybinds():
    for binding, value in profiles[profile].items():
        direction = None
        match binding:
            case 256:
                direction = "Up"
            case 128:
                direction = "Left"
            case 64:
                direction = "Down"
            case 32:
                direction = "Right"
            case 16:
                direction = "Green"
            case 8:
                direction = "Yellow"
            case 4:
                direction = "Blue"
            case 2:
                direction = "White"
            case 1:
                direction = "Red"
        
        print(f"{direction:>5} : {value}")

def getBinaryState(arduino):
    output = 0
    if arduino and arduino.is_open:
        lookingForPacket = True

        while arduino.in_waiting and lookingForPacket:
            startByte = arduino.read(1) # Get one byte from the arduino

            if startByte and startByte[0] == 0xFF:
                data = arduino.read(2) # Get two bytes from the arduino

                if len(data) == 2:
                    output = (data[0] << 1) | data[1] # Combine bytes into a singal integer
                
                lookingForPacket = False
    else:
        output = -1
    
    return(output)

def updateKey(key, keyPressed):
    keyUsed = SPECIAL_KEYS.get(key, key)

    if keyPressed and keyUsed not in keysPressed:
        keyboard.press(keyUsed) # type: ignore
        keysPressed.add(keyUsed)
    elif not keyPressed and keyUsed in keysPressed:
        keyboard.release(keyUsed) # type: ignore
        keysPressed.remove(keyUsed)

def connectToArduino(baud, port_name):
    try:
        connected = False
        while not connected:
            clear_screen()
            print("Searching for Arduino...\n\nCTRL+C to cancel")
            time.sleep(1)
            try:
                with serial.Serial(port_name, baud, timeout=1) as arduino:
                    connected = True
                    arduino.reset_input_buffer()
                    clear_screen()
                    print(f"Attempting to connect to {port_name}")
                    time.sleep(2)
                    clear_screen()
                    print(f"Successfully connected to {port_name}\n\nCTRL+C to disconnect\n\nKeybinds:")
                    viewKeybinds()

                    errorOccured = False
                    while not errorOccured:
                        if arduino.in_waiting >= 3:
                            joystickBinaryState = getBinaryState(arduino)
                            if joystickBinaryState != -1:
                                for item, value in profiles[profile].items():
                                    updateKey(value, bool(joystickBinaryState & item))
                            else:
                                errorOccured = True
                        else:
                            time.sleep(0.001)

            except serial.SerialException:
                for i in range(2, 0, -1):
                    clear_screen()
                    print(f"Could not find controller on {port_name}. Trying again in {i} seconds...\n\nCTRL+C to cancel")
                    time.sleep(1)

    except KeyboardInterrupt:
        clear_screen()
        if not connected:
            print("Canceled...")
        else:
            print("Disconnected...")

    finally:
        for key in list(keysPressed):
            keyboard.release(key)
        keysPressed.clear()

        input("\nPress Enter to continue...")
        clear_screen()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_arguments():
    parser = argparse.ArgumentParser(description="Controller Binary Reader")
    parser.add_argument("--autoconnect", action="store_true")
    parser.add_argument("--profile", type=str)
    parser.add_argument("--port", type=str, default="COM3")
    parser.add_argument("--baud", type=int, default=9600)

    return parser.parse_args()

main()