import os
from datetime import datetime
from flask import Flask, request, send_from_directory, jsonify, make_response, render_template_string
import requests

app = Flask(__name__)

# --- Configuración ---
IMAGE_DIR = "imagenes"
os.makedirs(IMAGE_DIR, exist_ok=True)
last_saved_image = None
PICO_IP = "192.168.1.101"  # Cambia si es necesario
PICO_PORT = 8080

# --- Utilidades de imagen ---
def rgb565_to_rgb888(rgb565_bytes):
    result = bytearray()
    for i in range(0, len(rgb565_bytes), 2):
        pixel = (rgb565_bytes[i] << 8) | rgb565_bytes[i + 1]
        r = (pixel >> 11) & 0x1F
        g = (pixel >> 5) & 0x3F
        b = pixel & 0x1F
        r = (r << 3) | (r >> 2)
        g = (g << 2) | (g >> 4)
        b = (b << 3) | (b >> 2)
        result.extend([b, g, r])
    return bytes(result)

def save_bmp(width, height, rgb888_data, filename):
    row_size = (width * 3 + 3) & ~3
    padding = row_size - width * 3
    bmp_data = bytearray()
    for row in range(height):
        start = row * width * 3
        end = start + width * 3
        bmp_data.extend(rgb888_data[start:end])
        bmp_data.extend(b'\x00' * padding)
    file_size = 54 + len(bmp_data)
    bmp_header = bytearray([
        0x42, 0x4D,
        *file_size.to_bytes(4, 'little'), 0, 0, 0, 0, 54, 0, 0, 0,
        40, 0, 0, 0,
        *width.to_bytes(4, 'little'),
        *height.to_bytes(4, 'little'),
        1, 0, 24, 0,
        0, 0, 0, 0,
        *len(bmp_data).to_bytes(4, 'little'),
        0x13, 0x0B, 0, 0, 0x13, 0x0B, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0
    ])
    with open(filename, "wb") as f:
        f.write(bmp_header)
        f.write(bmp_data)

# --- CORS ---
@app.after_request
def apply_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Connection"] = "close"
    return response

# --- Rutas de imagen ---
@app.route("/upload_raw_image_flash/", methods=["POST"])
def upload_image():
    global last_saved_image
    data = request.get_data()
    if len(data) < 4:
        return jsonify({"status": "error", "message": "Datos insuficientes."}), 400

    width = int.from_bytes(data[0:2], 'big')
    height = int.from_bytes(data[2:4], 'big')
    image_data = data[4:]

    if len(image_data) != width * height * 2:
        return jsonify({"status": "error", "message": "Tamaño incorrecto de imagen."}), 400

    rgb888 = rgb565_to_rgb888(image_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"img_{timestamp}.bmp"
    path = os.path.join(IMAGE_DIR, filename)
    save_bmp(width, height, rgb888, path)
    last_saved_image = filename

    return jsonify({"status": "ok", "filename": filename})

@app.route("/image/<path:filename>")
def serve_image(filename):
    response = make_response(send_from_directory(IMAGE_DIR, filename))
    response.headers["Cache-Control"] = "no-cache"
    return response

@app.route("/last_image_name")
def last_image_name():
    return jsonify({"image_name": last_saved_image})

@app.route("/view_image/<image_name>")
def view_image(image_name):
    return f"""
    <html>
    <head><title>Imagen</title></head>
    <body style="background:#111; color:white; text-align:center;">
        <h2>{image_name}</h2>
        <img src="/image/{image_name}" style="max-width:90%;" />
    </body>
    </html>
    """

# --- Página principal con stream y controles ---
@app.route("/stream")
def stream_page():
    return render_template_string("""
    <html>
    <head>
        <title>Stream + Control</title>
        <style>
            body { background-color: #111; color: white; text-align: center; font-family: sans-serif; }
            img { max-width: 90%; height: auto; border: 4px solid #333; border-radius: 8px; margin: 15px; }
            button {
                font-size: 16px; padding: 12px 18px; margin: 5px;
                border: none; border-radius: 10px;
                background-color: #444; color: white; cursor: pointer;
            }
            button:hover { background-color: #666; }
        </style>
        <script>
            async function updateImage() {
                try {
                    const res = await fetch("/last_image_name");
                    const data = await res.json();
                    if (data.image_name) {
                        const timestamp = new Date().getTime();
                        document.getElementById("stream").src = `/image/${data.image_name}?t=${timestamp}`;
                    }
                } catch (e) {
                    console.error("Error al actualizar imagen:", e);
                }
            }

            async function enviar(direccion) {
                const res = await fetch('/move', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ direction: direccion })
                });
                const r = await res.json();
                console.log(r);
            }

            async function controlarBrazo(accion) {
                try {
                    const res = await fetch(`/brazo?accion=${accion}`, { method: 'POST' });
                    const r = await res.json();
                    console.log(r);
                } catch (err) {
                    alert("Error: " + err);
                }
            }

            setInterval(updateImage, 200);
            window.onload = updateImage;
        </script>
    </head>
    <body>
        <h1>Stream + Control</h1>
        <img id="stream" src="" alt="Esperando imagen..." />
        <div>
            <h2>Movimientos</h2>
            <button onclick="enviar('forward')">↑ Adelante</button><br/>
            <button onclick="enviar('left')">← Izquierda</button>
            <button onclick="enviar('stop')">■ Detener</button>
            <button onclick="enviar('right')">→ Derecha</button><br/>
            <button onclick="enviar('backward')">↓ Atrás</button>
        </div>
        <div>
            <h2>Brazo Robótico</h2>
            <button onclick="controlarBrazo('recoger')">🤖 Recoger</button>
            <button onclick="controlarBrazo('alzar')">🔼 Alzar</button>
        </div>
    </body>
    </html>
    """)

# --- Endpoint para movimiento de carro ---
@app.route("/move", methods=["POST"])
def move():
    data = request.json
    direction = data.get("direction", "stop")
    try:
        url = f"http://{PICO_IP}:{PICO_PORT}/motor?dir={direction}"
        res = requests.get(url, timeout=1)
        if res.status_code == 200:
            return jsonify({"status": "ok", "message": f"Comando '{direction}' enviado a la Pico W"})
        else:
            return jsonify({"status": "error", "message": f"Respuesta: {res.status_code}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Endpoint para controlar el brazo robótico ---
@app.route("/brazo", methods=["POST"])
def brazo():
    accion = request.args.get("accion", "")
    if accion not in ("alzar", "recoger"):
        return jsonify({"status": "error", "message": "Acción inválida"}), 400
    try:
        url = f"http://{PICO_IP}:{PICO_PORT}/brazo?accion={accion}"
        res = requests.get(url, timeout=1)
        if res.status_code == 200:
            return jsonify({"status": "ok", "accion": accion})
        else:
            return jsonify({"status": "error", "message": f"Respuesta: {res.status_code}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Lanzamiento del servidor ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
