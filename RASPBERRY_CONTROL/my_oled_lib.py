from machine import Pin, I2C
import ssd1306
import time

# Dimensiones estándar de la pantalla OLED
OLED_WIDTH = 128
OLED_HEIGHT = 64  # Para pantallas de 128x64

class MyOLED:
    def __init__(self, sda_pin=2, scl_pin=3, width=OLED_WIDTH, height=OLED_HEIGHT):
        """
        Inicializa la pantalla OLED con manejo de errores.
        sda_pin: Pin GPIO para SDA (Datos I2C). Por defecto GP2.
        scl_pin: Pin GPIO para SCL (Reloj I2C). Por defecto GP3.
        width: Ancho de la pantalla en píxeles.
        height: Alto de la pantalla en píxeles.
        """
        try:
            # Usamos I2C bus 1 para los pines GP2 y GP3
            self.i2c = I2C(1, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=400000)
            self.oled = ssd1306.SSD1306_I2C(width, height, self.i2c, addr=0x3C)
            self.width = width
            self.height = height
            self.is_initialized = True
            
            # Mostrar mensaje de inicio
            self.clear()
            self.write_text("OLED Iniciada", 0, 0)
            self.write_text(f"{width}x{height}", 0, 20)
            time.sleep(1)
            self.clear()
            
            print(f"OLED inicializada en I2C bus 1 (SDA: GP{sda_pin}, SCL: GP{scl_pin})")
        except Exception as e:
            print("Error inicializando OLED:", e)
            self.is_initialized = False

    def clear(self):
        """Limpia toda la pantalla (la pone en negro)."""
        if self.is_initialized:
            try:
                self.oled.fill(0)  # 0 para negro
                self.oled.show()
            except Exception as e:
                print("Error al limpiar OLED:", e)

    def write_text(self, text, x=0, y=0, color=1, clear_first=False):
        """
        Escribe texto en la pantalla.
        text: La cadena de texto a escribir.
        x: Coordenada X de inicio (columna).
        y: Coordenada Y de inicio (fila).
        color: 1 para blanco, 0 para negro.
        clear_first: Si True, limpia la pantalla antes de escribir.
        """
        if not self.is_initialized:
            return
            
        try:
            if clear_first:
                self.clear()
                
            # Truncar texto si es demasiado largo
            max_chars = (self.width - x) // 8
            if len(text) > max_chars:
                text = text[:max_chars]
            
            self.oled.text(text, x, y, color)
            self.oled.show()
        except Exception as e:
            print("Error escribiendo en OLED:", e)

    def draw_pixel(self, x, y, color=1):
        """
        Dibuja un píxel individual en la pantalla.
        x: Coordenada X del píxel.
        y: Coordenada Y del píxel.
        color: 1 para blanco, 0 para negro.
        """
        if not self.is_initialized:
            return
            
        try:
            self.oled.pixel(x, y, color)
            self.oled.show()
        except Exception as e:
            print("Error dibujando pixel:", e)

    def draw_line(self, x1, y1, x2, y2, color=1):
        """
        Dibuja una línea entre dos puntos.
        (x1, y1): Coordenadas del punto inicial.
        (x2, y2): Coordenadas del punto final.
        color: 1 para blanco, 0 para negro.
        """
        if not self.is_initialized:
            return
            
        try:
            self.oled.line(x1, y1, x2, y2, color)
            self.oled.show()
        except Exception as e:
            print("Error dibujando linea:", e)

    def draw_rectangle(self, x, y, width, height, color=1, fill=False):
        """
        Dibuja un rectángulo.
        x, y: Coordenadas de la esquina superior izquierda.
        width, height: Ancho y alto del rectángulo.
        color: 1 para blanco, 0 para negro.
        fill: True para un rectángulo relleno, False para un contorno.
        """
        if not self.is_initialized:
            return
            
        try:
            if fill:
                self.oled.fill_rect(x, y, width, height, color)
            else:
                self.oled.rect(x, y, width, height, color)
            self.oled.show()
        except Exception as e:
            print("Error dibujando rectangulo:", e)

    def draw_circle(self, x, y, radius, color=1, fill=False):
        """
        Dibuja un círculo.
        x, y: Coordenadas del centro del círculo.
        radius: Radio del círculo.
        color: 1 para blanco, 0 para negro.
        fill: True para un círculo relleno, False para un contorno.
        """
        if not self.is_initialized:
            return
            
        try:
            if fill:
                # Algoritmo para círculo relleno
                for i in range(-radius, radius + 1):
                    for j in range(-radius, radius + 1):
                        if i*i + j*j <= radius*radius:
                            self.oled.pixel(x + i, y + j, color)
            else:
                # Algoritmo de Bresenham para círculo
                d = 3 - 2 * radius
                xc = 0
                yc = radius
                
                while yc >= xc:
                    self.oled.pixel(x + xc, y - yc, color)
                    self.oled.pixel(x - xc, y - yc, color)
                    self.oled.pixel(x + xc, y + yc, color)
                    self.oled.pixel(x - xc, y + yc, color)
                    self.oled.pixel(x + yc, y - xc, color)
                    self.oled.pixel(x - yc, y - xc, color)
                    self.oled.pixel(x + yc, y + xc, color)
                    self.oled.pixel(x - yc, y + xc, color)
                    
                    xc += 1
                    if d > 0:
                        yc -= 1
                        d += 4 * (xc - yc) + 10
                    else:
                        d += 4 * xc + 6
            
            self.oled.show()
        except Exception as e:
            print("Error dibujando circulo:", e)

    def display_on(self):
        """Enciende la pantalla (sale del modo de ahorro de energía)."""
        if not self.is_initialized:
            return
            
        try:
            self.oled.poweron()
        except Exception as e:
            print("Error encendiendo OLED:", e)

    def display_off(self):
        """Apaga la pantalla (entra en modo de ahorro de energía)."""
        if not self.is_initialized:
            return
            
        try:
            self.oled.poweroff()
        except Exception as e:
            print("Error apagando OLED:", e)

    def contrast(self, level):
        """
        Ajusta el contraste de la pantalla.
        level: Nivel de contraste (0-255).
        """
        if not self.is_initialized:
            return
            
        try:
            self.oled.contrast(level)
            self.oled.show()
        except Exception as e:
            print("Error ajustando contraste:", e)

    def invert(self, invert=True):
        """
        Invierte los colores de la pantalla.
        invert: True para invertir colores, False para normal.
        """
        if not self.is_initialized:
            return
            
        try:
            self.oled.invert(invert)
            self.oled.show()
        except Exception as e:
            print("Error invirtiendo colores:", e)

    def show_bitmap(self, bitmap_data, x=0, y=0, width=128, height=64):
        """
        Muestra una imagen bitmap en la pantalla.
        bitmap_data: Datos de la imagen en formato de bytes.
        x, y: Posición de inicio.
        width, height: Dimensiones de la imagen.
        """
        if not self.is_initialized:
            return
            
        try:
            # Calcular el número de bytes por fila
            bytes_per_row = width // 8
            if width % 8 != 0:
                bytes_per_row += 1
                
            # Mostrar la imagen
            for row in range(height):
                for col in range(width):
                    byte_index = row * bytes_per_row + col // 8
                    bit_index = 7 - (col % 8)
                    pixel_value = (bitmap_data[byte_index] >> bit_index) & 1
                    self.oled.pixel(x + col, y + row, pixel_value)
            
            self.oled.show()
        except Exception as e:
            print("Error mostrando bitmap:", e)

    def show_multiline_text(self, lines, x=0, y=0, line_height=10, color=1, clear_first=True):
        """
        Muestra múltiples líneas de texto en la pantalla.
        lines: Lista de cadenas de texto a mostrar.
        x, y: Posición inicial.
        line_height: Espacio vertical entre líneas.
        color: Color del texto (1 blanco, 0 negro).
        clear_first: Si True, limpia la pantalla primero.
        """
        if not self.is_initialized:
            return
            
        try:
            if clear_first:
                self.clear()
                
            current_y = y
            for line in lines:
                self.write_text(line, x, current_y, color, False)
                current_y += line_height
        except Exception as e:
            print("Error mostrando texto multilinea:", e)

    def progress_bar(self, x, y, width, height, progress, color=1):
        """
        Dibuja una barra de progreso.
        x, y: Posición de la barra.
        width, height: Dimensiones de la barra.
        progress: Progreso actual (0.0 a 1.0).
        color: Color de la barra (1 blanco, 0 negro).
        """
        if not self.is_initialized:
            return
            
        try:
            # Dibujar borde
            self.oled.rect(x, y, width, height, color)
            
            # Calcular el ancho del relleno
            fill_width = int((width - 2) * progress)
            if fill_width > 0:
                # Dibujar relleno
                self.oled.fill_rect(x + 1, y + 1, fill_width, height - 2, color)
            
            self.oled.show()
        except Exception as e:
            print("Error dibujando barra de progreso:", e)

    def is_initialized(self):
        """Devuelve True si la pantalla OLED está inicializada correctamente."""
        return self.is_initialized