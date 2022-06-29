import random
import json
import os
import os.path
import time
from json import JSONDecodeError

####MATRICULA DEL COCHE A ENVIAR AL EDGE####
matricula = "2450GDF"
limite = ""
####TOPIC DEL BROKER AL QUE SE SUSCRIBE LA BAT####
idEstacion = 8
topic_pub = f"gesys/edge/vehiculo"
topic_sub = f"gesys/vehiculo/{matricula}/cargaMaxima"



# callback despues de establecer connexion
def on_connect(client, userdata, flags, rc):
    #   QUALITY OF SERVICE que deseamos (0, 1 o 2 de menor a mayor calidad)
    qosClient = 2       
    print('(%s)' % client._client_id.decode("utf-8"), 'connected to broker')
    client.subscribe(topic_sub, qosClient)
    pass


# callback del mensaje recibido
def on_message(client, userdata, message):
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
        limite = msgPayloadJSON["battery"]     #   aquí obtenemos el porcentaje hasta donde se carga el coche
        client.disconnect()
    except JSONDecodeError:
        print("No es un json")

# función para enviar al edge la matricula detectada
def publish(client):
     time.sleep(1)
     MQTT_MSG = json.dumps({"battery":bateria, "matricula":matricula});
     #msgSent = f"messages: {matricula}"
     result = client.publish(topic_pub, MQTT_MSG)
     # result: [0, 1]
     status = result[0]
     if status == 0:
         print(f"Send `{MQTT_MSG}` to topic `{topic_pub}`")
     else:
         print(f"Failed to send message to topic {topic_pub}")

#!/usr/bin/env python
def mosquito(data):
    # creamos suscriptor
    client = mqtt.Client(client_id='PiCam', clean_session=True)

    # assignamos callback para cuando el cliente establezca conexion con el broker
    client.on_connect = on_connect
    # assignamos callback para cuando el cliente reciba un mensaje del broker
    client.on_message = on_message

    # establecemos connexion
    client.connect(host="test.mosquitto.org", port=1883)
    # publicamos mensaje del cliente al broker
    if data == 'limite':
        publish(client)
    elif data == 'bateri':
        publish(client)
        client.disconnect()
    #print("Waiting to recive message from broker...")
    client.loop_forever()
    #print("Data recieved, conection with broker closed!")
    time.sleep(1)

bateria = 99
km = 400


def clear(): return os.system('cls' if os.name in ('nt', 'dos') else 'clear')  # Limpiar terminal

def printa(bateria, tempo, km):
    print(f'\n\t[{bateria}%] [' + '❚' * bateria + ' ' * (100-bateria) + ']')  # Mostrar bateria
    print(f'\n\tTiempo restante de batería: {tempo} segundos')    #mostrar tiempo restante
    print(f'\n\tKilómetros de autonomía restantes: {km} km')   #mostrar autonomía en km restante

def printad(bateria, tempo):
    print(f'\n\t[{bateria}%] [' + '❚' * bateria + ' ' * (100-bateria) + ']')  # Mostrar bateria
    print(f'\n\tTiempo restante de carga: {tempo} segundos')    #mostrar tiempo restante

def descarga(tiempod):
    global bateria
    tempo = bateria*tiempod #tiempo restante descarga
    global km
    if bateria > 0:  # Si la bateria es mayor a 0 descargar bateria
        while bateria > 0 and tempo > 0:  # Descargar siempre que la bateria y el tempo sea mayor a 0 
            try:
                # Cortar descarga de bateria cuando se presiona la tecla q
                if keyboard.is_pressed('q'):
                    break
                else:
                    printa(bateria, tempo, km)
                    time.sleep(tiempod)  # Esperar tiempo designado
                    clear()
                    bateria -= 1
                    tempo -= tiempod
                    km -= 4
            except Exception as e:
                pass
    printa(bateria, tempo, km)
    


def carga_x(tiempoc):
    global bateria
    global km
    global limite
    if bateria < 99:   # Si la bateria es menor a 99 cargar bateria
        mosquito('limite_max')
        tempo = limite*tiempoc  #tiempo restante de la carga
        #Cargar siempre que la batería sea menor a la suma de la
        #cantidad a cargar y la batería actual y menor que 100
        while bateria < limite and bateria < 99 and tempo > 0:  
            try:
                printad(bateria, tempo)
                mosquito('bateri')
                time.sleep(tiempoc) # Esperar tiempo designado
                clear()
                bateria += 1
                tempo -= tiempoc
                km += 4
            except Exception as e:
                pass
    else:
        print('\t Batería ya cargada')


if __name__ == "__main__":
    tiempod = 3  # Tiempo total descarga = 300 min/100 = 1% cada 3 min = 180s modulo 60 = 3 segundos
    tiempoc = 1  # Tiempo total carga = 100 min/100 = 1% cada 1 min = 60s modulo 60 = 1 segundo
    bateria = 50
    tempo = 0
    while True:
        comando = int(input('\1: Cargar y 2: Descargar'))
        clear()

        if comando == 1:
            carga_x(tiempoc)  # Carga bateria completa
            printad(bateria, tempo)

        elif comando == 2:
            descarga(tiempod)  # Descargar bateria
            

        else:
            print('Comando Erroneo')

        
        print(f'\n\tBateria al {bateria}%')
