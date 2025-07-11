from machine import Pin, PWM
import time

# Constantes de calibración
VELOCIDAD_BASE = 38000
AJUSTE_MOTOR_A = 0.75
AJUSTE_MOTOR_B = 1.00

# Configuración de pines
PIN_ENA = 10
PIN_IN1 = 11
PIN_IN2 = 12
PIN_ENB = 13
PIN_IN3 = 14
PIN_IN4 = 15

class MotorController:
    def __init__(self):
        # Configuración motor izquierdo (A)
        self.ena = PWM(Pin(PIN_ENA))
        self.in1 = Pin(PIN_IN1, Pin.OUT)
        self.in2 = Pin(PIN_IN2, Pin.OUT)
        
        # Configuración motor derecho (B)
        self.enb = PWM(Pin(PIN_ENB))
        self.in3 = Pin(PIN_IN3, Pin.OUT)
        self.in4 = Pin(PIN_IN4, Pin.OUT)
        
        # Frecuencia PWM
        self.ena.freq(1000)
        self.enb.freq(1000)
        
        # Aplicar calibración
        self.velocidad_a = int(VELOCIDAD_BASE * AJUSTE_MOTOR_A)
        self.velocidad_b = int(VELOCIDAD_BASE * AJUSTE_MOTOR_B)
        self.ena.duty_u16(self.velocidad_a)
        self.enb.duty_u16(self.velocidad_b)
    
    def _set_motors(self, dir_a, dir_b):
        # Motor A
        self.in1.value(1 if dir_a == 'forward' else 0)
        self.in2.value(1 if dir_a == 'backward' else 0)
        
        # Motor B
        self.in3.value(1 if dir_b == 'forward' else 0)
        self.in4.value(1 if dir_b == 'backward' else 0)
        
        # Detener si no hay dirección
        if dir_a == 'stop':
            self.in1.value(0)
            self.in2.value(0)
        if dir_b == 'stop':
            self.in3.value(0)
            self.in4.value(0)
    
    def _ajustar_velocidad(self, ajuste_temp_a=1.0, ajuste_temp_b=1.0):
        self.ena.duty_u16(int(self.velocidad_a * ajuste_temp_a))
        self.enb.duty_u16(int(self.velocidad_b * ajuste_temp_b))

    # --- Métodos internos de movimiento ---
    def avanzar_continuo(self):
        self._ajustar_velocidad()
        self._set_motors('forward', 'forward')

    def retroceder_continuo(self):
        self._ajustar_velocidad(ajuste_temp_a=1.5,ajuste_temp_b=1.0)
        self._set_motors('backward', 'backward')

    def girar_izquierda_continuo(self):
        self._ajustar_velocidad(ajuste_temp_a=1.5)
        self._set_motors('backward', 'forward')

    def girar_derecha_continuo(self):
        self._ajustar_velocidad(ajuste_temp_a=1.5)
        self._set_motors('forward', 'backward')

    def detener(self):
        self._set_motors('stop', 'stop')
        self._ajustar_velocidad()

    # --- Alias esperados por el servidor Flask ---
    def forward(self): self.avanzar_continuo()
    def backward(self): self.retroceder_continuo()
    def left(self): self.girar_izquierda_continuo()
    def right(self): self.girar_derecha_continuo()
    def stop(self): self.detener()
