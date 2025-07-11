import network
import machine
import time
import uasyncio as asyncio
import _thread
from motor_controller import MotorController
from robot_arm_controller import BrazoRobotico
from my_oled_lib import MyOLED

# --- Configuración OLED ---
OLED_SDA_PIN = 2
OLED_SCL_PIN = 3
oled = MyOLED(sda_pin=OLED_SDA_PIN, scl_pin=OLED_SCL_PIN)

# --- Configuración WiFi ---
SSID = 'USUBENI'
PASSWORD = 'Usubeni26'

# --- Inicialización del controlador de motores y brazo ---
carro = MotorController()
brazo = BrazoRobotico()

# --- Utilidad: mostrar en OLED ---
def mostrar_mensaje_oled(linea1, linea2="", linea3="", linea4=""):
    try:
        oled.clear()
        oled.write_text(linea1, 0, 0)
        oled.write_text(linea2, 0, 10)
        oled.write_text(linea3, 0, 20)
        oled.write_text(linea4, 0, 30)
        time.sleep(0.1)
    except Exception as e:
        print("Error en OLED:", e)

# --- Conexión WiFi ---
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    mostrar_mensaje_oled("Conectando a WiFi", SSID)

    wlan.connect(SSID, PASSWORD)
    max_intentos = 20
    while not wlan.isconnected() and max_intentos > 0:
        mostrar_mensaje_oled("Conectando...", f"Intento: {21 - max_intentos}/20")
        time.sleep(0.5)
        max_intentos -= 1

    if not wlan.isconnected():
        mostrar_mensaje_oled("Error WiFi!", "No conectado")
        print("No se pudo conectar al WiFi.")
        return None

    ip = wlan.ifconfig()[0]
    mostrar_mensaje_oled("Conectado!", "IP:", ip, "Listo para comandos")
    print("Conectado. IP:", ip)
    return ip

# --- Parser de parámetros tipo query ---
def parse_query_string(query):
    params = {}
    for part in query.split('&'):
        if '=' in part:
            key, value = part.split('=', 1)
            params[key] = value
    return params

# --- Manejo del cliente web (comandos) ---
async def handle_client(reader, writer):
    try:
        request_line = await reader.readline()
        if not request_line:
            await writer.aclose()
            return

        method, path, _ = request_line.decode().split()
        print("Solicitud recibida:", path)

        if path.startswith("/motor"):
            if "?" in path:
                _, query = path.split("?", 1)
                params = parse_query_string(query)
                direction = params.get("dir", "")

                mostrar_mensaje_oled("Motor:", direction)

                if direction == "forward":
                    carro.avanzar_continuo()
                elif direction == "backward":
                    carro.retroceder_continuo()
                elif direction == "left":
                    carro.girar_izquierda_continuo()
                elif direction == "right":
                    carro.girar_derecha_continuo()
                elif direction == "stop":
                    carro.detener()
                else:
                    print("Dirección inválida:", direction)

        elif path.startswith("/brazo"):
            if "?" in path:
                _, query = path.split("?", 1)
                params = parse_query_string(query)
                accion = params.get("accion", "")

                mostrar_mensaje_oled("Brazo:", accion)

                def mover_brazo_posicion(angulos):
                    try:
                        brazo.mover_brazo(angulos, tiempo_segundos=2.2)
                    except Exception as e:
                        print("Error al mover brazo:", e)

                if accion == "alzar":
                    _thread.start_new_thread(mover_brazo_posicion, ([15, 90, 90],))
                elif accion == "recoger":
                    _thread.start_new_thread(mover_brazo_posicion, ([15, 0, 90],))
                else:
                    print("Acción de brazo no válida:", accion)

        await writer.awrite("HTTP/1.0 200 OK\r\nContent-Type: text/plain\r\n\r\nOK")

    except Exception as e:
        print("Error en handle_client:", e)
    finally:
        await writer.aclose()

# --- Inicialización del servidor web ---
async def iniciar_servidor_web():
    mostrar_mensaje_oled("Servidor:", "Escuchando en", "puerto 8080")
    print("Iniciando servidor en puerto 8080...")
    server = await asyncio.start_server(handle_client, "0.0.0.0", 8080)
    while True:
        await asyncio.sleep(1)

# --- Programa principal ---
if __name__ == "__main__":
    try:
        ip = conectar_wifi()
        if ip:
            asyncio.run(iniciar_servidor_web())
        else:
            print("Reiniciando por error WiFi...")
            time.sleep(2)
            machine.reset()
    except Exception as e:
        print("Error crítico:", e)
        mostrar_mensaje_oled("ERROR", str(e)[:16], "Reiniciando...")
        time.sleep(3)
        machine.reset()
