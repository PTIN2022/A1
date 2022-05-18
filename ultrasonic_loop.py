import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

# pins
TRIG = 23
ECHO = 24

print ("Distance measurement in progress")

GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)

try:
    while True:
        GPIO.output(TRIG, False)
        print ("Waiting for sensor to settle")
        time.sleep(2)
        
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)
        
        while GPIO.input(ECHO)==0:
            start = time.time()
            
        while GPIO.input(ECHO)==1:
            end = time.time()
            
        # ( end - start ) * 170 ---> en metros
        # para cms 170*100=17000
        distance = (end - start) * 17000
        
        if distance <= 30.0:
            # activamos cámara
            # recortamos matricula de la foto
            # enviamos foto
        
        print ("Distance:" + str( distance ) + " cm.")

except KeyboardInterrupt: 
    print("Cleaning up!")
    GPIO.cleanup()
