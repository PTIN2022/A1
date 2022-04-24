import cv2 #librearia opencv, lectura y filtros de imagen
from matplotlib import pyplot as plt #plot de la foto
import numpy as np # Herramienta que facilita el trato de sus valores.
import imutils #Mas herramientas
import easyocr #Lectura de texto en imagenes
import paho.mqtt.client as mqtt
import threading
import os.path
from os import path
import json
from json import JSONDecodeError
import time
import shutil

####LISTA DE COCHES ADMITIDOS####
llistaAdmesos = []


# callback despues de establecer connexion
def on_connect(client, userdata, flags, rc):
    print('(%s)' % client._client_id.decode("utf-8"), 'connected to broker')
    client.subscribe("gesys/estacion/12/lista_admitidos")
    pass

# callback del mensaje recibido
def on_message(client, userdata, message):
    global llistaAdmesos
    print('------------------------------')
    print('Data received!')
    print('topic: %s' % message.topic)
    print('payload: %s' % message.payload.decode("utf-8"))
    print('qos: %d' % message.qos)
    print('------------------------------')
    try:
        msg = json.loads(message.payload.decode("utf-8"))
        print(msg)
        if "matr_list" in msg:
            # actualizamos la lista de las matriculas admitidas con lo que nos llegue del broker
            llistaAdmesos = msg["matr_list"]
            # este print es para debuggar
            print(llistaAdmesos)
            
    except JSONDecodeError:
        print("No es un json")

# función para obtener la string con la matrícula del vehiculo de la imágen
def detectar_matricula( img_path ):
    ###Lectura de imagen###
    img = cv2.imread(img_path)

    ####Filtros####
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)#Gris
    bilFilter = cv2.bilateralFilter(gray,11,17,17) #Reduccion de distorciones(Noise)              
    edges = cv2.Canny(gray,30,200) #Se queda con bordes

    ####Tema de contornos####
    contAux = cv2.findContours(edges.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)#Encontrar contornos, aproximacion simple
    contours = imutils.grab_contours(contAux)#Basicamente simplifica lo obtenido de lo anterior
    contours = sorted(contours,key=cv2.contourArea,reverse=True)[:15] # Nos quedamos con los 15 primeros de manera ordenada(algo subjetivo)

    ####Analisis de los diferentes contornos
    recortado = None
    location = None
    for c in contours:
        approx = cv2.approxPolyDP(c,10,True) #Aproximar polinomios(cuadrado, rectangulo,...)
        x,y,w,h = cv2.boundingRect(approx) #valores del polinomio aproxumado

        if len(approx) ==4 :
            aspect_ratio = float(w)/h
            if aspect_ratio > 1.5:#Es un valor que posem com a minim de aspectratio para considerarlo como rectangulo
                location = approx

        if location is None: #4 lados pero no rectangulo, lo ignoramos
            continue
        else:
            #Mascara de matricula, es decir, quedara resaltada la zona de la matricula, el resto, sera negro.
            mask = np.zeros(gray.shape, np.uint8)
            auxmasked = cv2.drawContours(mask, [location], 0,255, -1)
            auxmasked = cv2.bitwise_and(img, img, mask=mask)

            #Recorte de la matricula
            (x,y) = np.where(mask==255)
            (x1, y1) = (np.min(x), np.min(y))
            (x2, y2) = (np.max(x), np.max(y))
            recortado = gray[x1:x2+1, y1:y2+1] #Combinacion de min y max, da la zona a recortar

            #Lectura del texto
            reader = easyocr.Reader(['es'])
            result = ""
            result = reader.readtext(recortado)
            
            #Comprobamos que efectivamente es un rectangulo con texto
            if len(result) > 0:
                matr_detectada =  result[-1][1] #Es donde esta lo leido
                matr_detectada = matr_detectada.replace(" ","") #Nos cargamos los espacios vacios(comodidad)
                return matr_detectada
                
            else:
               continue

# thread para la detección de la matrícula
def thread_detectar_matricula():
    # definimos la variable de la lista de matriculas admitidas como global
    global llistaAdmesos
    while True:
        f = "./meh.jpg"
        if path.isfile(f):
            matricula = detectar_matricula(f)
            # renombramos la imagen meh.jpg a f1.jpg
            shutil.move(f, "f1.jpg")
            # estos prints son para debuggar
            print ( matricula )
            print (llistaAdmesos)
            
            for x in llistaAdmesos:
                # si la matrícula está en la lista abrimos
                if x == matricula:
                    print("Abriendo barrera...")
                    print("Vehículo con matricula "+matricula+" pasando")
                    # el tiempo de pasar de un coche por la barrera
                    # podriamos seguir leyendo la camara, ver si el coche esta, etc
                    time.sleep(5)
                    print("Ya ha pasado.")
                    print("Cerrando barrera...")
        time.sleep(2)

# arranca thread            
x = threading.Thread(target=thread_detectar_matricula)
x.start()
        
# creamos suscriptor
client = mqtt.Client(client_id='Cloud', clean_session=False)

# definimos funciones a realizar despues de establecer connexion y recepcion de mensajes
client.on_connect = on_connect
client.on_message = on_message

# establecemos connexion
client.connect(host="test.mosquitto.org", port=1883)
client.loop_forever()


