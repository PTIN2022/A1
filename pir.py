# librerias
#from picamera import PiCamera
#import libCamera
from time import sleep
import time
from datetime import datetime

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM) # nos permite elegir el puerto

# parametros de la camara
#P=PiCamera()
#P.resolution= (1024,768)
#P.start_preview()

# definimos el puerto GPIO23 ( de la rasp ) como un puerto de entrada
GPIO.setup(23, GPIO.IN) 

# loop if movement
while True: 
    # si entra algo por el puerto GPIO23
    if GPIO.input(23):
        print("Motion...")
        # camera warm-up time
        time.sleep(1)
        #P.capture('motion.jpg') # se genera la captura de la imagen
        time.sleep(4) # 4 segs mientras se captura la imagen y la graba donde tenga que guardarla
        # gestión de la imágen de la matrícula
        # enviamos la matrícula
