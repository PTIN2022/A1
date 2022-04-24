#!/bin/bash
export DISPLAY=:0.0

#   Obtenemos ruta de la carpeta actual
rutaActual=`find / -type d -name DetectConnectection 2>/dev/null`

#   Iniciamos script en una nueva terminal
if [[ $INITIALIZED == "" ]]; then
    export INITIALIZED="1"
    gnome-terminal -- sh -c "$rutaActual/./scriptEthernet.sh"
    exit
fi
#   Tiempo para mostrar aviso
cronoAviso=5
#   Tiempo para llamar a grua tras realizar el aviso
cronoGrua=10


#   Obtenemos el nombre de la interficie
interfaceName=$(ip a | grep state | cut -d' ' -f2 | grep e)
interfaceName=${interfaceName::-1}
echo "Nombre de la interfaz: "$interfaceName
clienteNum=1
while true; do
    #   Obtenemos el estado de la interficie -> [up, down, unknown]
    state=$(cat /sys/class/net/$interfaceName/operstate)
    while [[ "$state" != "up" ]]; do
        state=$(cat /sys/class/net/$interfaceName/operstate)
    done

    echo "Atendiendo a cliente nº "$clienteNum
    sleep 1
    #   Cuando el estado de la interficie sea up, quiere decir que hay un vehículo conectado
    #   de manera que el cliente puede iniciar su recarga en este punto de carga
    
    #   SCRIPT GESTIÓN RECARGA
    gnome-terminal -- sh -c "python3 $rutaActual/scriptBateria/simulacionBateria.py"
    
    enUso=$(ps aux | grep simulacionBateria | grep -v color= | grep -v grep)
    while [[ "$enUso" != "" ]]; do
        enUso=$(ps aux | grep simulacionBateria | grep -v color= | grep -v grep)
    done

    #   Una vez finalizada la recarga, el cliente tiene un margen de tiempo para desocupar
    #   la plaza, si este supera el margen entonces se hará uso del servicio de gruas
    
    #   SCRIPT GESTIÓN DESOCUPACIÓN PLAZA
    gnome-terminal -- sh -c "$rutaActual/./auxAlertas.sh $interfaceName $cronoAviso $cronoGrua"
    
    enUso=$(ps aux | grep auxAlertas | grep -v color= | grep -v grep)
    while [[ "$enUso" != "" ]]; do
        enUso=$(ps aux | grep auxAlertas | grep -v color= | grep -v grep)
    done
    clienteNum="$((clienteNum + 1))"
done
