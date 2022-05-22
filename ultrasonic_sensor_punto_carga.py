import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

# pines
TRIG = 23
ECHO = 24

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
        
        # en cms 
        distance = (end - start) * 17000
        
        if distance <= 30.0:
            # enviamos un 1 al edge
            print("Plaza ocupada")
        else:
            # enviamos un 0 al edge 
            print("Plaza libre")
        
        # sleep de 10 minutos para enviarle la ocupación al edge cada 10 mins
        #sleep(600)
        # sleep de 10 segundos para debugar
        sleep(10)
        

except KeyboardInterrupt: 
    GPIO.cleanup()
