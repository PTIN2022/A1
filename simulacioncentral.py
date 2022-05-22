import logging
import threading
import time
from random import random
from random import seed
from random import randint
from datetime import datetime

seed(1)
averias = {0: 'ok',
           1: 'enchufe',
           2: 'voltaje',
           3: 'pantalla',
           4: 'c.interno'
           }

listaadmitidos = ['7820RPG', '7335ZWO']  # SE CONSIGUE A PARTIR DEL EDGE
listamatriculas = ['5710UBM', '7335ZWO', '4840PFQ', '3250TBG', '6311PPA', '2585VNK', '5786GFB', '7820RPG']  # SIMULACION DE MATRICULAS DE COCHES


def cargacoche():
    time.sleep(20)


def thread_function(name, kwh):
    print(f'Thread {name} ininciado!')
    averiado = False
    while True:
        # seed(1)

        delay = randint(5, 30)  # Mirar que rango de tiempo cunde
        time.sleep(delay)
        if not averiado:
            porcentaje = random()
            if porcentaje <= 0.05:  # Llega coche

                matricula = listamatriculas[randint(0, 7)]

                print(f'[+] Coche con matricula {matricula} en cargador {name}!')

                if matricula in listaadmitidos:  # MIRAR SI ESTA ADMITIDO EL COCHE
                    print(f'[+] Coche cargando en cargador {name}!')

                    # OCUPADO
                    print('{"cargador": ' + str(name) + ', "matricula":"' + str(matricula) + '"}')
                    cargacoche()
                    # ESTADISTICAS
                    now = datetime.now()
                    # dd/mm/YY H:M:S
                    dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
                    print(
                        '{"cargador": ' + str(name) + ', "kwh": ' + str(kwh) + ', "fecha": "' + str(dt_string) + '", "matricula": "' + str(matricula) + '"}')
                    # DESOCUPADO
                    print('{"cargador": ' + str(name) + ' }')
                else:
                    print(f'Coche no admitido en la plaza {name}!')  # INDICA QUE EL NFC SE HA LEIDO Y NO LE CORRESPONDE ESA PLAZA
            elif porcentaje <= 0.10 and porcentaje > 0.05:  # Averia
                condicionaveria = randint(1, 4)
                print(
                    f'Averia en el cargador {name} con averia {averias[condicionaveria]}')
                print('{"cargador": ' + str(name) +
                      ', "averia": ' + str(condicionaveria) + '}')
                averiado = True
        else:
            print(f'[!] Cargador {name} con averia {averias[condicionaveria]}')
            time.sleep(30)  # SIMULACION DE QUE ALGUIEN ARREGLA LA AVERIA
            print(f'Cargador {name} arreglado {averias[0]}')
            print('{"cargador": ' + str(name) +
                  ', "averia": ' + str(0) + '}')


# TODO HACER QUE EN UN MOMENTO SE ARREGLE LA AVERIA, TIMER PARA QUE AL CABO DE X SEGUNDOS SE ARREGLE SOLO?
if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    threads = list()
    for index in range(32):
        logging.info("Main: create and start thread %d.", index)
        kwh = 7.4
        if index < 4:  # CARGA RAPIDA
            kwh = 66

        x = threading.Thread(target=thread_function, args=(index, kwh,))
        threads.append(x)
        x.start()

    # for index, thread in enumerate(threads):
    #    logging.info("Main    : before joining thread %d.", index)
    #    thread.join()
    #    logging.info("Main    : thread %d done", index)
