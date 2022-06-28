from mfrc522 import SimpleMFRC522
import re
from picamera import PiCamera
from matplotlib import pyplot as plt  # plot de la foto
import paho.mqtt.client as mqtt
import numpy as np  # Herramienta que facilita el trato de sus valores.
import imutils  # Mas herramientas
import pytesseract
import cv2  # librearia opencv, lectura y filtros de imagen
from datetime import datetime
from os import path
from json import JSONDecodeError
import argparse
import glob
import importlib.util
import json
import os
import os.path
import shutil
import sys
import threading
import time
import random
import RPi.GPIO as GPIO
# Import necessary libraries for communication and display use
import drivers

# Load the driver and set it to "display"
# If you use something from the driver library use the "display." prefix first
display = drivers.Lcd()

GPIO.setwarnings(False)
# import easyocr  # Lectura de texto en imagenes
reader = SimpleMFRC522()    # Reader NFC

#### DATOS FIJOS ####
idPuntoCarga = "1"  #   Identificador de este punto de carga

#### DATOS A ENVIAR AL EDGE ####
averia = 0
consumo = 0
matriculaNFC = ""
firstTime = True

#### DATOS A RECIBIR DEL EDGE ####
puntoCargaCoche = ""
cargaLimiteCoche = "$"
bateriaCoche = ""

#   Pub Topics
topicPubAveria = f"gesys/edge/puntoCarga/averia"                #   eniva la averia del punto de carga
topicPubConsumo = f"gesys/edge/puntoCarga/consumo"              #   envia el consumo del punto de carga
topicPubMatrVehiculo = f"gesys/edge/puntoCarga/vehiculo"        #   envia la matricula del vehiculo detectado con NFC (para validar que esta donde le toca)

#   Sub Topics
topicSubPuntoValido = f"gesys/edge/puntoCarga/{idPuntoCarga}"   #   recibe a que punto de carga debe de ir el vehiculo detectado con NFC
topicSubBateria = f"gesys/vehiculo/{matriculaNFC}"              #   recibe el nivel de bateria actual del vehiculo y el lvl de bateria al que quiere llegar


def nfc():
    try:
        print('Listo para leer!')
        id, text = reader.read()
        print(id)
        print(text)
        return text

    except Exception as e:
        print(e)
        return e
    finally:
        GPIO.cleanup()

#   callback despues de establecer connexion
def on_connect(client, userdata, flags, rc):
    #   QUALITY OF SERVICE que deseamos (0, 1 o 2 de menor a mayor calidad)
    qosClient = 0  # qos 0 pq hemos creado al cliente con clean session
    print('(%s)' % client._client_id.decode("utf-8"), 'connected to broker')
    client.subscribe(topicSubPuntoValido, qosClient)
    client.subscribe(topicSubBateria, qosClient)
    print("Subscribed to all topics")
    pass

#   callback del mensaje recibido
def on_message(client, userdata, message):
    #   message es el mensaje que se recibe del broker
    msgTopic = message.topic
    msgPayload = message.payload.decode("utf-8")
    msgQOS = message.qos
    print('------------------------------')
    print('Datos recibidos!')
    print('topic: %s' % msgTopic)
    print('payload: %s' % msgPayload)
    print('qos: %d' % msgQOS)
    print('------------------------------')
    try:
        msgPayloadJSON = json.loads(msgPayload)
        # aquí obtenemos si la matricula enviada es valida o no (0 o 1)
        if msgTopic == topicSubPuntoValido:
            puntoCargaCoche = msgPayloadJSON["idPuntoCarga"]
            cargaLimiteCoche = msgPayloadJSON["cargaLimiteCoche"]
        elif msgTopic == topicSubBateria:
            bateriaCoche = msgPayloadJSON["percentilCoche"]
        client.disconnect()
    except JSONDecodeError:
        print("No es un json")

#   Publicar datos al broker
def publish(client, topic):
    if topic == topicPubAveria:
        if firstTime:
            MQTT_MSG = json.dumps({"averia": averia})   #   aqui averia=0 siemepre
            firstTime = False
            
        else:
            MQTT_MSG = json.dumps({"averia": averia})
            result = client.publish(topic, MQTT_MSG)
            if result[0] == 0:
                print(f"Enviado {MQTT_MSG} al topic: {topic}")
            else:
                print(f"Error al enviar mensaje al topic: {topic}")
            
            time.sleep(10)
            
            averia = 0
            print("Punto de carga arreglado")
            MQTT_MSG = json.dumps({"averia": averia})
            time.sleep(0.5)

    elif topic == topicPubConsumo:
        consumo = consumo + bateriaCoche
        MQTT_MSG = json.dumps({"consumo": consumo})

    elif topic == topicPubMatrVehiculo:
        MQTT_MSG = json.dumps({"matricula": matriculaNFC})
    
    result = client.publish(topic, MQTT_MSG)           
    # result: [0, 1]
    if result[0] == 0:
        print(f"Enviado {MQTT_MSG} al topic: {topic}")
    else:
        print(f"Error al enviar mensaje al topic: {topic}")

def mosquito(data):
    # creamos suscriptor
    client = mqtt.Client(client_id='PuntoCarga', clean_session=True)

    # assignamos callback para cuando el cliente establezca conexion con el broker
    client.on_connect = on_connect
    # assignamos callback para cuando el cliente reciba un mensaje del broker
    client.on_message = on_message

    # establecemos connexion
    client.connect(host="test.mosquitto.org", port=1883)

    #   La primera vez que se enciende el punto de carga se envia su estado de averia actual (siempre 0 al inico)
    if firstTime:
        publish(client, topicPubAveria)

    if data == "matricula":
        # publicamos mensaje de matricula detectada con NFC
        publish(client, topicPubMatrVehiculo)
    elif data == "consumo":
        # publicamos mensaje de consumo
        publish(client, topicPubConsumo)
        time.sleep(1)
        client.disconnect()
    elif data == "averia":
        # publicamos mensaje de averia
        publish(client, topicPubAveria)
        time.sleep(1)
        client.disconnect()
    
    client.loop_start()

    time.sleep(10)  # espera 10 segundos una respuesta del edge, si no la recibe se desconecta
    try:
        client.disconnect()
    except:
        print("Error en el disconnect")



if __name__ == "__main__":
    # Insertar main aqui
    while True:
        matriculaNFC = nfc()
        mosquito("matricula")
        if idPuntoCarga == puntoCargaCoche:
            print("Writing to display")
            display.lcd_display_string("Bienvenido!",1) # PANTALLA LCD
            #time.sleep(2)
            
            #   simulacion carga
            while bateriaCoche != cargaLimiteCoche:
                mosquito("")    #   espera a recibir el lvl de bateria actual del coche
            mosquito("consumo")
            
            #   Obtenemos el estado(averia o no) del punto de carga de forma simulada
            listaAverias = [0, 1, 2, 3, 4]
            averia = random.choices(listaAverias, weights=(100, 0.1, 0.1, 0.1, 0.1), k=1)[0]    #   Es poco probable que falle :>
            if averia != 0:
                mosquito("averia")
        else:
            print("Writing to display")
            display.lcd_display_string("Este no es su punto de carga", 1)                           # PANTALLA LCD
            display.lcd_display_string("Por favor dirigase al punto nº" + str(puntoCargaCoche), 2)  # PANTALLA LCD
            time.sleep(2)
        display.lcd_clear()