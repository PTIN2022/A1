# importamos las librerias necesarias
import RPi.GPIO as GPIO
import time

# set GPIO numbering mode
GPIO.setmode(GPIO.BOARD)

# Set pin 11 as output, and set servo1 as pin 11 as PWM
GPIO.setup(11,GPIO.OUT)
servo1 = GPIO.PWM(11,50) # Note 11 is pin, 50 = 50Hz pulse 

# startt PWM running, but with value of 0 ( pulse off )
servo1.start(0)
print ("Waiting for 2 seconds")
time.sleep(2)

# Turn barrier 90 degrees, barrier up
print ("Turning back to 90 degrees for 2 seconds")
servo1.ChangeDutyCycle(7)
print("Coche con matricula _____ pasando...")
time.sleep(15)
print("Ya ha pasado")

# turn back to 0 degrees, barrier down
print ("Turning back to 0 degrees")
servo1.ChangeDutyCycle(2)
time.sleep(0.5)
servo1.ChangeDutyCycle(0)

# Clean things up at the end
servo1.stop()
GPIO.cleanup()
print ("Goodbye")
