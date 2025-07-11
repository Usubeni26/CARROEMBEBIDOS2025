#Importamos las librerias
from machine import Pin, PWM
import math


#Definimos la función
def main():
    codo = PWM(Pin(16)) #GPIO16
    codo.freq(50) 
    hombro = PWM(Pin(17)) #GPIO17
    hombro.freq(50)
    base =PWM(Pin(18)) #GPIO18
    base.freq(50)
    
    """Limites de los ángulos del codo: 20° a 90°; hombro: 0 a 90°; base: -90 a 90°."""
    
    #Solicitud de ángulos (PROPUESTA):
    """angulo0 = anguloBase; angulo1 = anguloHombro; angulo2 = anguloCodo"""
    
    while True:
        
        #Se pide por consola los ángulos
        anguloHombro = float(input('anguloHombro: '))
        anguloCodo = float(input('anguloCodo: '))
        anguloBase = float(input('anguloBase: '))
        
#         Corrección de ángulos
        if anguloHombro == 0:
            anguloCodo = -anguloCodo+90
#             
        if 0 < anguloHombro < 90:
            anguloCodo = abs(anguloCodo -anguloHombro)
#         
        #Definición de la ecuación para cada servo
        cododuty = int(11666*anguloCodo+500000)
        hombroduty = int(-11111*anguloHombro+1550000)
        baseduty = int(-9717*anguloBase+1532862)
        
#         baseduty=int(anguloBase)
        base.duty_ns(baseduty)
#         print(baseduty)
#         cododuty=int(anguloCodo)
#         hombroduty=int(anguloHombro)
        codo.duty_ns(cododuty)
        hombro.duty_ns(hombroduty)
        #cododuty= cododuty/1000000
        #print(cododuty,' ms')
        #hombroduty= hombroduty/1000000
        #print(hombroduty,' ms')
        
if __name__ == '__main__':
    main()

