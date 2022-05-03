#!/bin/bash

#   se ejecuta a a partir de scriptEthernet.sh
#   USAGE: ./auxAlertas.sh interfaceName cronAviso cronGrua
#   p.e.   ./auxAlertas.sh enp0s8 5 10

function plazaOcupada(){
    actualSec=`date +%S`
    finalSec=`expr $actualSec + $1`
    finalSec=`expr $finalSec % 60`
    if [ $finalSec -lt 10 ]; then
        finalSec="0"$finalSec
    fi
    while [[ "$actualSec" != "$finalSec" ]]; do
        state=$(cat /sys/class/net/$interfaceName/operstate)
        if [[ "$state" != "up" ]]; then                         #   (*)AQUÍ FALTARÍA AÑADIR LA DETECCIÓN POR INFRARROJO
            echo "Buen viaje :)"
            exit
        fi
        actualSec=`date +%S`
    done
}

interfaceName=$1
cronoAviso=$2
cronoGrua=$3

echo "Recarga completada, ya puede retirar su vehículo"

plazaOcupada $cronoAviso

#   Si no ha desconectado y retirado(*) el vehículo se muestra un aviso
state=$(cat /sys/class/net/$interfaceName/operstate)
if [[ "$state" == "up" ]]; then                                 #   (*)AQUÍ FALTARÍA AÑADIR LA DETECCIÓN POR INFRARROJO
    echo "Tiene" $cronoGrua "segundos para desconectar su vehículo y desocupar la plaza o llamaremos a la grua"
    plazaOcupada $cronoGrua

    #  Si no ha desconectado y retirado el vehículo se muestra un aviso de que se incautará el vehículo
    state=$(cat /sys/class/net/$interfaceName/operstate)
    if [[ "$state" == "up" ]]; then                             #   (*)AQUÍ FALTARÍA AÑADIR LA DETECCIÓN POR INFRARROJO
        echo "Vehículo incautado, llamando a la grua"
        sleep 2
        #   while [[ grua no se ha llevado vehículo ]]; do      #   (*)AQUÍ FALTARÍA AÑADIR LA DETECCIÓN POR INFRARROJO
        #       esperar
        #   done
        echo "La grua se ha llevado el vehículo? 'si' para confirmar"
        read plazaLibre
        while [[ $plazaLibre != "si" ]]; do
            read plazaLibre
        done
    fi
fi