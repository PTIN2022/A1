#!/bin/bash

sudo apt-get -y install libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev

sudo apt-get -y install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev

sudo apt-get -y install libxvidcore-dev libx264-dev

sudo apt-get -y install qt4-dev-tools 

sudo apt-get -y install libatlas-base-dev


#Se instala una version opencv anterior a la 4, esta segun muchos manuales puede dar problemas con la rasp.
pip3 install opencv-python==3.4.17.63
pip3 install --upgrade opencv-python==3.4.17.63
#Algunos paquetes de tensorflow igualmente son necesarios
sudo pip3 install tensorflow

#SI ALGUNA COSA NO SE INSTALA, NO PREOCUPARSE, PUEDE ESTAR OBSOLETO, PERO ESTOS SON LOS REQUERIMIENTOS QUE NOS PROPORCIONA TFLITE.
