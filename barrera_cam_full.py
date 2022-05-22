# Import packages
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
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
from json import JSONDecodeError
from os import path
from datetime import datetime

import cv2  # librearia opencv, lectura y filtros de imagen
# import easyocr  # Lectura de texto en imagenes
import pytesseract
import imutils  # Mas herramientas
import numpy as np  # Herramienta que facilita el trato de sus valores.
import paho.mqtt.client as mqtt
from matplotlib import pyplot as plt  # plot de la foto
from picamera import PiCamera

####TOPIC DEL BROKER AL QUE SE SUSCRIBE LA CAM####
idEstacion = 8
topic = f"gesys/estacion/{idEstacion}/lista_admitidos"
####MATRICULA DETECTADA A ENVIAR AL EDGE####
matricula = ""
####VALIDACIÓN DE LA MATRICULA EN EL EDGE####
validezEdge = ""

# callback despues de establecer connexion
def on_connect(client, userdata, flags, rc):
    #   QUALITY OF SERVICE que deseamos (0, 1 o 2 de menor a mayor calidad)
    qosClient = 0       #   qos 0 pq hemos creado al cliente con clean session
    print('(%s)' % client._client_id.decode("utf-8"), 'connected to broker')
    client.subscribe(topic, qosClient)
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
        validezEdge = msgPayloadJSON["valido"]     #   aquí obtenemos si la matricula enviada es valida o no (0 o 1)
        client.disconnect()
    except JSONDecodeError:
        print("No es un json")

# función para enviar al edge la matricula detectada
def publish(client):
     time.sleep(1)
     MQTT_MSG = json.dumps({"matricula":matricula, "id_estacio":idEstacion});
     #msgSent = f"messages: {matricula}"
     result = client.publish(topic, MQTT_MSG)
     # result: [0, 1]
     status = result[0]
     if status == 0:
         print(f"Send `{MQTT_MSG}` to topic `{topic}`")
     else:
         print(f"Failed to send message to topic {topic}")

#!/usr/bin/env python
def mosquito():
    # creamos suscriptor
    client = mqtt.Client(client_id='PiCam', clean_session=True)

    # assignamos callback para cuando el cliente establezca conexion con el broker
    client.on_connect = on_connect
    # assignamos callback para cuando el cliente reciba un mensaje del broker
    client.on_message = on_message

    # establecemos connexion
    client.connect(host="test.mosquitto.org", port=1883)
    # publicamos mensaje del cliente al broker
    publish(client)
    #print("Waiting to recive message from broker...")
    client.loop_forever()
    #print("Data recieved, conection with broker closed!")
    time.sleep(1)


def tensorflow():
    global matricula
    
    # Define and parse input arguments

    parser = argparse.ArgumentParser()
    parser.add_argument('--modeldir', help='Folder the .tflite file is located in',
                        required=True)
    parser.add_argument('--graph', help='Name of the .tflite file, if different than detect.tflite',
                        default='detect.tflite')
    parser.add_argument('--labels', help='Name of the labelmap file, if different than labelmap.txt',
                        default='labelmap.txt')
    parser.add_argument('--threshold', help='Minimum confidence threshold for displaying detected objects',
                        default=0.5)
    parser.add_argument('--image', help='Name of the single image to perform detection on. To run detection on multiple images, use --imagedir',
                        default=None)
    parser.add_argument('--imagedir', help='Name of the folder containing images to perform detection on. Folder must contain only images.',
                        default=None)
    parser.add_argument('--edgetpu', help='Use Coral Edge TPU Accelerator to speed up detection',
                        action='store_true')

    args = parser.parse_args()

    MODEL_NAME = args.modeldir
    GRAPH_NAME = args.graph
    LABELMAP_NAME = args.labels
    min_conf_threshold = float(args.threshold)
    use_TPU = args.edgetpu

    # Parse input image name and directory.
    IM_NAME = args.image
    IM_DIR = args.imagedir

    # If both an image AND a folder are specified, throw an error
    if (IM_NAME and IM_DIR):
        print('Error! Please only use the --image argument or the --imagedir argument, not both. Issue "python TFLite_detection_image.py -h" for help.')
        sys.exit()

    # If neither an image or a folder are specified, default to using 'test1.jpg' for image name
    if (not IM_NAME and not IM_DIR):
        IM_NAME = 'picture.jpg'

    # Import TensorFlow libraries
    # If tflite_runtime is installed, import interpreter from tflite_runtime, else import from regular tensorflow
    # If using Coral Edge TPU, import the load_delegate library
    pkg = importlib.util.find_spec('tflite_runtime')
    if pkg:
        from tflite_runtime.interpreter import Interpreter
        if use_TPU:
            from tflite_runtime.interpreter import load_delegate
    else:
        from tensorflow.lite.python.interpreter import Interpreter
        if use_TPU:
            from tensorflow.lite.python.interpreter import load_delegate

    # If using Edge TPU, assign filename for Edge TPU model
    if use_TPU:
        # If user has specified the name of the .tflite file, use that name, otherwise use default 'edgetpu.tflite'
        if (GRAPH_NAME == 'detect.tflite'):
            GRAPH_NAME = 'edgetpu.tflite'

    # Get path to current working directory
    CWD_PATH = os.getcwd()

    # Define path to images and grab all image filenames
    if IM_DIR:
        PATH_TO_IMAGES = os.path.join(CWD_PATH, IM_DIR)
        images = glob.glob(PATH_TO_IMAGES + '/*')

    elif IM_NAME:
        PATH_TO_IMAGES = os.path.join(CWD_PATH, IM_NAME)
        images = glob.glob(PATH_TO_IMAGES)

    # Path to .tflite file, which contains the model that is used for object detection
    PATH_TO_CKPT = os.path.join(CWD_PATH, MODEL_NAME, GRAPH_NAME)

    # Path to label map file
    PATH_TO_LABELS = os.path.join(CWD_PATH, MODEL_NAME, LABELMAP_NAME)

    # Load the label map
    with open(PATH_TO_LABELS, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    # Have to do a weird fix for label map if using the COCO "starter model" from
    # https://www.tensorflow.org/lite/models/object_detection/overview
    # First label is '???', which has to be removed.
    if labels[0] == '???':
        del(labels[0])

    # Load the Tensorflow Lite model.
    # If using Edge TPU, use special load_delegate argument
    if use_TPU:
        interpreter = Interpreter(model_path=PATH_TO_CKPT,
                                  experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
        print(PATH_TO_CKPT)
    else:
        interpreter = Interpreter(model_path=PATH_TO_CKPT)

    interpreter.allocate_tensors()

    # Get model details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    floating_model = (input_details[0]['dtype'] == np.float32)

    input_mean = 127.5
    input_std = 127.5

    # Check output layer name to determine if this model was created with TF2 or TF1,
    # because outputs are ordered differently for TF2 and TF1 models
    outname = output_details[0]['name']

    if ('StatefulPartitionedCall' in outname):  # This is a TF2 model
        boxes_idx, classes_idx, scores_idx = 1, 3, 0
    else:  # This is a TF1 model
        boxes_idx, classes_idx, scores_idx = 0, 1, 2

    # Loop over every image and perform detection
    for image_path in images:

        # Load image and resize to expected shape [1xHxWx3]
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        imH, imW, _ = image.shape
        image_resized = cv2.resize(image_rgb, (width, height))
        input_data = np.expand_dims(image_resized, axis=0)

        # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
        if floating_model:
            input_data = (np.float32(input_data) - input_mean) / input_std

        # Perform the actual detection by running the model with the image as input
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()

        # Retrieve detection results
        boxes = interpreter.get_tensor(output_details[boxes_idx]['index'])[0]  # Bounding box coordinates of detected objects
        classes = interpreter.get_tensor(output_details[classes_idx]['index'])[0]  # Class index of detected objects
        scores = interpreter.get_tensor(output_details[scores_idx]['index'])[0]  # Confidence of detected objects
        
        # Loop over all detections and draw detection box if confidence is above minimum threshold
        for i in range(len(scores)):
            if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0)):

                # Get bounding box coordinates and draw box
                # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
                ymin = int(max(1, (boxes[i][0] * imH)))
                xmin = int(max(1, (boxes[i][1] * imW)))
                ymax = int(min(imH, (boxes[i][2] * imH)))
                xmax = int(min(imW, (boxes[i][3] * imW)))
                print(ymin, xmin, ymax, xmax)
                xmin = int(xmin+((xmax-xmin)*8.1)/100)
                # 132 259 174 458
                cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)

                porcentajefiabilidad = int(scores[i]*100)
                print(f'FIABILIDAD {porcentajefiabilidad}')
                if porcentajefiabilidad > 50:
                    cropped_image = image[ymin:ymax, xmin:xmax]
                    # plt.imshow(cropped_image) # No se que demonios es esto
                    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)  # Gris
                    #cv2.imwrite(f'gray.jpg', gray)
                    _, bt = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
                    #bnt = cv2.bitwise_not(bt)
                    cv2.imwrite(f'bt.jpg', bt)

                    matricula = pytesseract.image_to_string(bt, config='--psm 7')
                    matricula = ''.join(filter(str.isalnum, matricula))
                    # if len(result) > 7:
                    #     if result[0] == 'A':
                    #         result = result[1:]

                    print(f'PLACA: {matricula}')

                    cv2.imwrite(f'cropped.jpg', cropped_image)

        # All the results have been drawn on the image, now display the image
        cv2.imshow('Object detector', image)
        time.sleep(2)

        # Press any key to continue to next image, or press 'q' to quit
        # if cv2.waitKey(0) == ord('q'):
        #     break

    # Clean up
    cv2.destroyAllWindows()
    


def proximidad():
    return True     #eliminar
    # AQUI VA LO DEL SENSOR DE PROXIMIDAD
    GPIO.setmode(GPIO.BOARD)

    # pins
    TRIG = 16
    ECHO = 18

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
            
            print ("Distance:" + str( round(distance, 2) ) + " cm.")
            
            if distance <= 30.0:
                return True

    except KeyboardInterrupt: 
        print("Cleaning up!")
        GPIO.cleanup()

def barrier():
    # set GPIO numbering mode
    GPIO.setmode(GPIO.BOARD)

    # Set pin 11 as output, and set servo1 as pin 11 as PWM
    GPIO.setup(11,GPIO.OUT)
    servo1 = GPIO.PWM(11,50) # Note 11 is pin, 50 = 50Hz pulse 

    # startt PWM running, but with value of 0 ( pulse off )
    servo1.start(0)
    #print ("Coche con matrícula _____ detectado")
    time.sleep(1)

    print ("Subiendo barrera")
    servo1.ChangeDutyCycle(7)
    #print("Coche con matrícula _____ pasando...")
    time.sleep(7)
    print("Ya ha pasado")

    # turn back to 0 degrees, barrier down
    print ("Bajando barrera")
    servo1.ChangeDutyCycle(2)
    time.sleep(0.5)
    servo1.ChangeDutyCycle(0)

    # Clean things up at the end
    servo1.stop()
    GPIO.cleanup()
    print ("Ta' luego Maricarmen")

def fotillo():
    #camera = PiCamera()
    #camera.start_preview()
    #time.sleep(2)
    #camera.stop_preview()
    webCam = cv2.VideoCapture("http://192.168.1.36:8080/video")
    s,frame = webCam.read()
    cv2.imwrite('picture.jpg', frame)


if __name__ == "__main__":
    #   Siempre a la espera de algún vehículo
    while True:
        print('PROXIMIDAD')
        if proximidad():            #   Detecta vehículo en frente de la camara
            print('FOTILLO')
            fotillo()               #   La camara hace una foto
            print('TENSORFLOW')
            tensorflow()            #   A partir de la foto se busca la matricula
            print('MOSQUITO')
            mosquito()              #   Se envía la matricula al broker para que se valide en el edge
            if validezEdge == "0":
                barrier()           #   Si la matricula es valida, se abre la barrera
            else:
                print("Matricula no valida")
        time.sleep(5)  # Sleep entre iteracion y iteracion de
        input()  # PAUSA PARA DEBUG
