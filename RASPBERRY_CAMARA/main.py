# optimized_pico_stream.py (doble buffer seguro con velocidad mejorada + optimizaciones extra)

import machine
import time
import urequests as requests
import sys
import ujson
from machine import Pin, I2C, PWM, Timer
from ov7670_wrapper import *
import gc
import network
import uselect
import ubinascii
import _thread

image_sequence_number = 0
wifi_connection_attempts = 0
connection_status = False

stats = {
    'fps': 0,
    'capture_time': 0,
    'send_time': 0,
    'dropped_frames': 0,
    'total_frames': 0,
    'network_errors': 0,
    'successful_sends': 0,
    'memory_errors': 0
}

frame_ready = False
current_frame_data = None
send_in_progress = False

frame_buffer_a = None
frame_buffer_b = None
active_buffer = None
send_buffer = None

class Config:
    SSID = "USUBENI"
    PASSWORD = "Usubeni26"
    FLASH_SERVER_URL = "http://192.168.1.141:8000" #AJUSTAR SEGÚN SEA LA IP DEL SERVIDOR
    UPLOAD_ENDPOINT = "/upload_raw_image_flash/"
    WIFI_TIMEOUT = 8
    WIFI_MAX_RETRIES = 2
    WIFI_RETRY_DELAY = 1
    TARGET_FPS = 20 # VALOR NO MAYOR A 20 RECOMENDADO
    FRAME_INTERVAL = 1.0 / TARGET_FPS
    CAPTURE_TIMEOUT = 10
    SEND_TIMEOUT = 120
    ENABLE_AGGRESSIVE_GC = True
    GC_THRESHOLD = 512
    MIN_FREE_MEMORY = 8192
    JPEG_QUALITY = 50
    LED_PIN = "LED"
    MCLK_PIN = 9
    PCLK_PIN = 8
    DATA_PIN_BASE = 0
    VSYNC_PIN = 11
    HREF_PIN = 10
    RESET_PIN = 19
    SHUTDOWN_PIN = 18
    SDA_PIN = 20
    SCL_PIN = 21
    STATS_INTERVAL = 25
    GC_INTERVAL = 5

led_pin = Pin(Config.LED_PIN, Pin.OUT)
led_pin.value(0)

# CPU a 250 MHz
machine.freq(250_000_000)

temp_send_buffer = None

def setup_memory_optimizations():
    if Config.ENABLE_AGGRESSIVE_GC:
        gc.threshold(Config.GC_THRESHOLD)
    gc.collect()
    print(f"\uD83D\uDCBE Memoria libre inicial: {gc.mem_free()} bytes")

def create_double_buffer(width, height):
    global frame_buffer_a, frame_buffer_b, active_buffer, send_buffer, temp_send_buffer
    buffer_size = width * height * 2
    send_buffer_size = buffer_size + 4
    gc.collect()
    if gc.mem_free() < 2 * buffer_size + send_buffer_size + 10000:
        print("❌ Memoria insuficiente para doble buffer")
        return False
    frame_buffer_a = bytearray(buffer_size)
    frame_buffer_b = bytearray(buffer_size)
    active_buffer = frame_buffer_a
    send_buffer = frame_buffer_b
    temp_send_buffer = bytearray(send_buffer_size)
    return True

def swap_buffers():
    global active_buffer, send_buffer
    active_buffer, send_buffer = send_buffer, active_buffer

def conectar_wifi_pico(ssid, password, timeout=8, max_retries=2):
    global wifi_connection_attempts, connection_status
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.config(pm=0x11111)
    for retry in range(max_retries):
        wifi_connection_attempts += 1
        print(f"📡 WiFi {retry + 1}/{max_retries}")
        if wlan.isconnected():
            wlan.disconnect()
            time.sleep(0.5)
        wlan.connect(ssid, password)
        start_time = time.time()
        while not wlan.isconnected() and (time.time() - start_time) < timeout:
            time.sleep(0.2)
        if wlan.isconnected():
            print(f"✅ WiFi: {wlan.ifconfig()[0]}")
            connection_status = True
            return wlan
    print("❌ WiFi no conectado")
    connection_status = False
    return None

def initialize_camera_pico():
    print("🎥 Inicializando cámara...")
    pwm = PWM(Pin(Config.MCLK_PIN))
    pwm.freq(16_000_000)
    pwm.duty_u16(32768)
    i2c = I2C(0, freq=100_000, scl=Pin(Config.SCL_PIN), sda=Pin(Config.SDA_PIN))
    try:
        ov7670 = OV7670Wrapper(
            i2c_bus=i2c,
            mclk_pin_no=Config.MCLK_PIN,
            pclk_pin_no=Config.PCLK_PIN,
            data_pin_base=Config.DATA_PIN_BASE,
            vsync_pin_no=Config.VSYNC_PIN,
            href_pin_no=Config.HREF_PIN,
            reset_pin_no=Config.RESET_PIN,
            shutdown_pin_no=Config.SHUTDOWN_PIN,
        )
        ov7670.wrapper_configure_rgb()
        ov7670.wrapper_configure_base()
        width, height = ov7670.wrapper_configure_size(OV7670_WRAPPER_SIZE_DIV4)
        if not create_double_buffer(width, height):
            return None, None, None
        return ov7670, width, height
    except Exception as e:
        print(f"❌ Error cámara: {e}")
        return None, None, None

def check_memory_health():
    if gc.mem_free() < Config.MIN_FREE_MEMORY:
        stats['memory_errors'] += 1
        gc.collect()
        return False
    return True

def capture_frame_pico(ov7670):
    global active_buffer, stats
    start = time.time()
    if not check_memory_health():
        return None
    ov7670.capture(active_buffer)
    stats['capture_time'] = time.time() - start
    return active_buffer

def send_frame_pico(frame_data, width, height, seq_num, device_info):
    global temp_send_buffer, stats
    send_start = time.time()
    try:
        temp_send_buffer[0:2] = width.to_bytes(2, 'big')
        temp_send_buffer[2:4] = height.to_bytes(2, 'big')
        temp_send_buffer[4:] = frame_data
        headers = {
            "Content-Type": "application/octet-stream",
            "X-Device-ID": device_info['device_id'],
            "X-Sequence": str(seq_num),
            "X-Memory": str(gc.mem_free())
        }
        url = f"{Config.FLASH_SERVER_URL}{Config.UPLOAD_ENDPOINT}"
        resp = requests.post(url, data=temp_send_buffer, headers=headers, timeout=Config.SEND_TIMEOUT)
        ok = resp.status_code in [200, 201]
        resp.close()
        stats['send_time'] = time.time() - send_start
        stats['successful_sends' if ok else 'network_errors'] += 1
        return ok
    except Exception as e:
        print(f"❌ Error envío: {e}")
        stats['network_errors'] += 1
        return False

def sender_thread_pico(width, height, device_info):
    global frame_ready, current_frame_data, send_in_progress, send_buffer
    print("📤 Hilo de envío iniciado")
    while True:
        try:
            if frame_ready and not send_in_progress:
                send_in_progress = True
                try:
                    if current_frame_data and send_buffer:
                        send_frame_pico(send_buffer, width, height, current_frame_data, device_info)
                    else:
                        stats['dropped_frames'] += 1
                finally:
                    frame_ready = False
                    send_in_progress = False
            time.sleep(0.002)  # reducido de 0.005 a 0.002
        except Exception as e:
            print(f"❌ Error hilo envío: {e}")
            send_in_progress = False
            time.sleep(0.05)

def print_pico_stats():
    free_mem = gc.mem_free()
    efficiency = (stats['successful_sends'] / max(1, stats['total_frames'])) * 100
    print(f"\n📊 FPS: {stats['fps']:.1f} | Mem: {free_mem//1024}KB | Cap: {stats['capture_time']*1000:.0f}ms | Send: {stats['send_time']*1000:.0f}ms | Drops: {stats['dropped_frames']} | Eff: {efficiency:.0f}%")

def main_pico_stream():
    global image_sequence_number, stats, frame_ready, current_frame_data, send_in_progress
    print("🚀 Iniciando streaming...")
    setup_memory_optimizations()
    wlan = conectar_wifi_pico(Config.SSID, Config.PASSWORD)
    if not wlan:
        return
    device_info = {
        'device_id': f"PicoW_{ubinascii.hexlify(wlan.config('mac')).decode()[-6:]}",
        'ip': wlan.ifconfig()[0],
        'mac': ubinascii.hexlify(wlan.config('mac')).decode()
    }
    ov7670, width, height = initialize_camera_pico()
    if not ov7670:
        return
    _thread.start_new_thread(sender_thread_pico, (width, height, device_info))
    last_frame_time = time.time()
    while True:
        try:
            current_time = time.time()
            elapsed_time = current_time - last_frame_time
            if elapsed_time < Config.FRAME_INTERVAL:
                time.sleep(Config.FRAME_INTERVAL - elapsed_time)
                current_time = time.time()
                elapsed_time = current_time - last_frame_time
            stats['fps'] = 1.0 / elapsed_time if elapsed_time > 0 else float('inf')
            last_frame_time = current_time
            if not wlan.isconnected():
                print("⚠️  WiFi perdido, reconectando...")
                wlan = conectar_wifi_pico(Config.SSID, Config.PASSWORD)
                if not wlan:
                    time.sleep(1)
                    continue
                device_info['ip'] = wlan.ifconfig()[0]
            if not check_memory_health():
                gc.collect()
                time.sleep(0.05)
                continue
            if not frame_ready:
                frame_data = capture_frame_pico(ov7670)
                if frame_data:
                    swap_buffers()
                    image_sequence_number += 1
                    stats['total_frames'] += 1
                    current_frame_data = image_sequence_number
                    frame_ready = True
                else:
                    stats['dropped_frames'] += 1
            if image_sequence_number > 0 and image_sequence_number % Config.STATS_INTERVAL == 0:
                print_pico_stats()
            if image_sequence_number > 0 and image_sequence_number % Config.GC_INTERVAL == 0:
                gc.collect()
            led_pin.value(1 if image_sequence_number % 8 < 4 else 0)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error en bucle: {e}")
            stats['dropped_frames'] += 1
            time.sleep(0.1)
    led_pin.value(0)
    print("✅ Streaming detenido")
    print(f"📊 Frames totales: {stats['total_frames']}")
    print(f"📤 Enviados: {stats['successful_sends']}")
    print(f"📉 Perdidos: {stats['dropped_frames']}")

if __name__ == "__main__":
    main_pico_stream()
