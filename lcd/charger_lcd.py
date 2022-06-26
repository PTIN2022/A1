#! /usr/bin/env python

# Import necessary libraries for communication and display use
import drivers
from time import sleep

# Load the driver and set it to "display"
# If you use something from the driver library use the "display." prefix first
display = drivers.Lcd()
receivedNum = 12
chargerNum = 16

# Main body of code
try:
    # Sentences can only be 16 characters long!
    print("Writing to display")
    if receivedNum != chargerNum :
        display.lcd_display_string("Plaza equivocada",1)                # Write line of text to first line of display
        display.lcd_display_string("vaya al num "+str(chargerNum),2)    # Write line of text to second line of display
        sleep(2)                                                        # Give time for the message to be read
    else:
        display.lcd_display_string("Bienvenido!",1)
        display.lcd_display_string("Cargando...",2)
        sleep(2)

    display.lcd_clear()                                                 # Clear the display of any data
    sleep(2)                                                            # Give time for the message to be read

except KeyboardInterrupt:
    # If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
    print("Cleaning up!")
    display.lcd_clear()
