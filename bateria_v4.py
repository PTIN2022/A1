import time
import os
import keyboard

bateria = 100
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
    

def carga_limite(tiempoc):
    global bateria
    global km
    if bateria < 100:  # Si la bateria es menor a 100 cargar bateria
        limite = 0  # Limite hasta el cual cargar
        while limite < bateria:  # Mientras el limite sea menor que el porcentaje actual de bateria
            limite = int(input('\tPorcentaje hasta donde cargar: '))
            tempo = (limite-bateria)*tiempoc    #tiempo restante de la carga
            if bateria > limite:  # Si la bateria es mayor al limite que queremos llegar = Mal limite
                print('\t Indique un porcentaje válido')
            else:
                while bateria < limite and tempo > 0:  # Cargar siempre que la bateria sea menor que el limite al que llegar y el tempo no sea cero
                    try:
                        printad(bateria, tempo)
                        time.sleep(tiempoc)  # Esperar tiempo designado
                        clear()
                        bateria += 1
                        tempo -= tiempoc
                        km += 4
                    except Exception as e:
                        pass
    else:
        print('\t Batería ya cargada')


def carga_x(tiempoc):
    global bateria
    global km
    if bateria < 100:   # Si la bateria es menor a 100 cargar bateria
        limite = int(input('\tPorcentaje que quiere cargar: ')) #Indicamos cuanto porcentaje queremos cargar
        tempo = limite*tiempoc  #tiempo restante de la carga
        limite += bateria
        #Cargar siempre que la batería sea menor a la suma de la
        #cantidad a cargar y la batería actual y menor que 100
        while bateria < limite and bateria < 100 and tempo > 0:  
            try:
                printad(bateria, tempo)
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
    bateria = int(input('\tIndicar batería del coche: '))
    tempo = 0
    while True:
        comando = int(input('\n\t[1] Cargar hasta X%\n\t[2] Cargar X%\n\t[3] Descarga\n\n\t[1/2/3]: '))
        clear()
        if comando == 1:
            carga_limite(tiempoc)  # Carga hasta limite
            printad(bateria, tempo)

        elif comando == 2:
            carga_x(tiempoc)  # Carga bateria completa
            printad(bateria, tempo)

        elif comando == 3:
            descarga(tiempod)  # Descargar bateria
            

        else:
            print('Comando Erroneo')

        
        print(f'\n\tBateria al {bateria}%')
