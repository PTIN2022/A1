import json
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
from json import JSONDecodeError

GPIO.setmode(GPIO.BCM)

#### TOPIC DEL BROKER AL QUE SE SUSCRIBE NFC ####
idPuntoCarga = '2'
topicSub = f"gesys/edge/puntoCarga/{idPuntoCarga}"
topicPub = f"gesys/edge/puntoCarga/vehiculo"
matricula = "4950KZK"
validezEdge = ""

# Pines
TRIG = 23
ECHO = 24

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

reader = SimpleMFRC522()


# callback despues de establecer connexion
def on_connect(client, userdata, flags, rc):
    #   QUALITY OF SERVICE que deseamos (0, 1 o 2 de menor a mayor calidad)
    qosClient = 2  # qos 0 pq hemos creado al cliente con clean session
    print('(%s)' % client._client_id.decode("utf-8"), 'connected to broker')
    client.subscribe(topicSub, qosClient)
    pass


# callback del mensaje recibido
def on_message(client, userdata, message):
    global validezEdge
    #   message es el mensaje que se recibe del broker
    msgTopic = message.topic
    msgPayload = message.payload.decode("utf-8")
    msgQOS = message.qos
    print('------------------------------')
    print('Data received!')
    print('topic: %s' % msgTopic)
    print('payload: %s' % msgPayload)
    print('qos: %d' % msgQOS)
    print('------------------------------')
    try:
        msgPayloadJSON = json.loads(msgPayload)
        validezEdge = msgPayloadJSON["idPuntoCarga"]  # Aquí obtenemos en que cargador deberia estar el vehiculo
        client.disconnect()
    except JSONDecodeError:
        print("No es un json")

# función para enviar al edge la matricula detectada


def publish(client):
    time.sleep(1)
    mqtt_msg = json.dumps({"idPuntoCarga": idPuntoCarga, "matricula": matricula})
    result = client.publish(topicPub, mqtt_msg, qos=2)
    status = result[0]
    if status == 0:
        print(f"Send {mqtt_msg} to topic {topicPub}")
    else:
        print(f"Failed to send message to topic {topicPub}")

#!/usr/bin/env python


def mosquito():
    # creamos suscriptor
    client = mqtt.Client(client_id='PiCam', clean_session=True)

    # assignamos callback para cuando el cliente establezca conexion con el broker
    client.on_connect = on_connect
    # assignamos callback para cuando el cliente reciba un mensaje del broker
    client.on_message = on_message

    # establecemos connexion
    client.connect(host="craaxkvm.epsevg.upc.es", port=23702)
    # client.connect(host="test.mosquitto.org", port=1883)

    publish(client)
    client.loop_start()

    time.sleep(10)  # espera 15 segundos del edge, vacio legal que no sabemos que pasa.
    try:
        client.disconnect()
    except:
        print("Error en el disconnect")


# def main():


if __name__ == "__main__":
    try:
        while True:
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
            if distance <= 30.0:
                print("Plaza ocupada")
                try:
                    print('Listo para leer!')
                    id, text = reader.read()
                    print(id)
                    print(text)
                    textojson = json.loads(text)
                    matricula = textojson["matricula"]
                    potencia = textojson["potencia"]
                    print(f'Matricula: {matricula}, Potencia: {potencia}')
                    mosquito()
                    if validezEdge != idPuntoCarga:
                        print(f'Coche en cargador incorrecto [{idPuntoCarga}], por favor cargar en cargador número: [{validezEdge}]')
                    else:
                        print('Coche en cargador correcto, cargando...')
                    break
                except Exception as e:
                    print(e)
            else:
                print("Plaza libre")
            time.sleep(10)
    except KeyboardInterrupt:
        GPIO.cleanup()
