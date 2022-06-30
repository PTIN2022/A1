import re
from matplotlib import pyplot as plt  # plot de la foto
import paho.mqtt.client as mqtt
import numpy as np  # Herramienta que facilita el trato de sus valores.
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
from picamera import PiCamera
import imutils  # Mas herramientas
import pytesseract
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
Import necessary libraries for communication and display use
import drivers

# Load the driver and set it to "display"
# If you use something from the driver library use the "display." prefix first
display = drivers.Lcd()

GPIO.setwarnings(False)
# import easyocr  # Lectura de texto en imagenes
reader = SimpleMFRC522()    # Reader NFC

#### DATOS FIJOS ####
idPuntoCarga = 29  #   Identificador de este punto de carga

#### DATOS A ENVIAR AL EDGE ####
averia = 0
matriculaNFC = "2450GDF"
firstTime = True

#### DATOS A RECIBIR DEL EDGE ####
puntoCargaCoche = ""
cargaLimiteCoche = 100
bateriaCoche = 0
first_time_batt = None

#   Pub Topics
topicPubAveria = f"gesys/edge/puntoCarga/averia"                #   eniva la averia del punto de carga
topicPubConsumo = f"gesys/edge/puntoCarga/consumo"              #   envia el consumo del punto de carga
topicPubMatrVehiculo = f"gesys/edge/puntoCarga/vehiculo"        #   envia la matricula del vehiculo detectado con NFC (para validar que esta donde le toca)

#   Sub Topics
topicSubPuntoValido = f"gesys/puntoCarga/{idPuntoCarga}"        #   recibe a que punto de carga debe de ir el vehiculo detectado con NFC
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

def proximidad():
    GPIO.output(TRIG, False)
    print("Waiting for sensor to settle")
    time.sleep(2)
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    while GPIO.input(ECHO) == 0:
        start = time.time()
    while GPIO.input(ECHO) == 1:
        end = time.time()
    # Distancia en cms
    distance = (end - start) * 17000
    return distance <= 30.0

#   callback despues de establecer connexion
def on_connect(client, userdata, flags, rc):
    #   QUALITY OF SERVICE que deseamos (0, 1 o 2 de menor a mayor calidad)
    qosClient = 2
    print('(%s)' % client._client_id.decode("utf-8"), 'connected to broker')
    client.subscribe(topicSubPuntoValido, qosClient)
    client.subscribe(topicSubBateria, qosClient)
    print("Subscribed to all topics")
    pass

#   callback del mensaje recibido
def on_message(client, userdata, message):
    global puntoCargaCoche
    global cargaLimiteCoche
    global bateriaCoche
    global first_time_batt
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
            bateriaCoche = msgPayloadJSON["battery"]
            if first_time_batt == None:
                first_time_batt = bateriaCoche
        #client.disconnect()
    except JSONDecodeError:
        print("No es un json")

#   Publicar datos al broker
def publish(client, topic):
    global firstTime
    global averia
    if topic == topicPubAveria:
        if firstTime:
            MQTT_MSG = json.dumps({"averia": 0, "idPuntoCarga": idPuntoCarga})
            firstTime = False
            
        else:
            MQTT_MSG = json.dumps({"averia": averia, "idPuntoCarga": idPuntoCarga})
            result = client.publish(topic, MQTT_MSG)
            if result[0] == 0:
                print(f"Enviado {MQTT_MSG} al topic: {topic}")
            else:
                print(f"Error al enviar mensaje al topic: {topic}")
            
            time.sleep(30)
            
            print("Punto de carga arreglado")
            MQTT_MSG = json.dumps({"averia": 0, "idPuntoCarga": idPuntoCarga})
            time.sleep(0.5)

    elif topic == topicPubConsumo:
        consumo = (bateriaCoche - first_time_batt ) 
        MQTT_MSG = json.dumps({"kwh": consumo, "idPuntoCarga": idPuntoCarga, "matricula": matriculaNFC})

    elif topic == topicPubMatrVehiculo:
        MQTT_MSG = json.dumps({"matricula": matriculaNFC, "idPuntoCarga": idPuntoCarga})
    
    result = client.publish(topic, MQTT_MSG)           
    # result: [0, 1]
    if result[0] == 0:
        print(f"Enviado {MQTT_MSG} al topic: {topic}")
    else:
        print(f"Error al enviar mensaje al topic: {topic}")



def mosquito(data):
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
        #client.disconnect()
    elif data == "averia":
        # publicamos mensaje de averia
        publish(client, topicPubAveria)
        time.sleep(1)
        #client.disconnect()
    
# creamos suscriptor
client = mqtt.Client(client_id='PuntoCarga', clean_session=True)
# assignamos callback para cuando el cliente establezca conexion con el broker
client.on_connect = on_connect
# assignamos callback para cuando el cliente reciba un mensaje del broker
client.on_message = on_message
# establecemos connexion
client.connect(host="craaxkvm.epsevg.upc.es", port=23702)
client.loop_start()

if __name__ == "__main__":
    # Insertar main aqui
    while True:
        if bateriaCoche == cargaLimiteCoche:
            print("Coche cargado completamente!!!")
            print("Quita tu coche")
            display.lcd_display_string("Coche cargado!!", 1) # Write line of text to first line of display
            display.lcd_display_string("Retire su coche", 2) # Write line of text to second line of display
            time.sleep(5)
            continue
        #if True:
        if proximidad():
            print('Listo para leer!')
            matriculaNFC = nfc()
            #matriculaNFC = "2450GDF"
            mosquito("matricula")
            time.sleep(2)
            if idPuntoCarga == puntoCargaCoche:
                print("Writing to display")
                print("Bienvenido! :)")
                display.lcd_display_string("Bienvenido! :)", 1) # PANTALLA LCD
                time.sleep(2) # Tiempo para leer mensaje
                
                #   simulacion carga
                while bateriaCoche != cargaLimiteCoche:
                    display.lcd_display_string("Bateria: {}".format(bateriaCoche), 2) # PANTALLA LCD
                    time.sleep(5)

                mosquito("consumo")
                
                #   Obtenemos el estado(averia o no) del punto de carga de forma simulada
                listaAverias = [0, 1, 2, 3, 4]
                averia = random.choices(listaAverias, weights=(100, 0.1, 0.1, 0.1, 0.1), k=1)[0]    #   Es poco probable que falle :>
                if averia != 0:
                    mosquito("averia")
            else:
                print("Writing to display")
                print("Plaza equivocada")
                print("vaya al num "+str(puntoCargaCoche))
                #time.sleep(2)
                display.lcd_display_string("Plaza equivocada", 1)                    # Write line of text to first line of display
                display.lcd_display_string("vaya al num "+str(puntoCargaCoche), 2)   # Write line of text to second line of display
                time.sleep(2)

            display.lcd_clear()