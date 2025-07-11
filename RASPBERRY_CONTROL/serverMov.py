import socket
import time
import machine

# HTML simplificado para el control
HTML_PAGINA = """<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<meta charset="UTF-8">
<title>Control de Carro</title>
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
    /* Estilos optimizados */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        touch-action: manipulation;
        -webkit-tap-highlight-color: transparent;
    }
    body {
        font-family: 'Roboto', sans-serif;
        background: #121212;
        height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: white;
        overflow: hidden;
        padding: 15px;
    }
    .container {
        width: 100%;
        max-width: 400px;
        text-align: center;
        padding: 20px;
        background: #1e1e1e;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    h1 {
        font-size: 24px;
        margin-bottom: 20px;
        color: #ffffff;
        font-weight: 500;
    }
    .controls {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        grid-gap: 12px;
        margin-top: 15px;
    }
    .btn {
        padding: 0;
        border: none;
        border-radius: 50%;
        background: #2d2d2d;
        color: white;
        font-size: 0;
        width: 80px;
        height: 80px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        transition: all 0.1s;
        outline: none;
    }
    .btn:active {
        transform: scale(0.92);
        background: #3a3a3a;
    }
    .btn i {
        font-size: 36px;
    }
    #btnAdelante {
        grid-column: 2;
        grid-row: 1;
        background: #4CAF50;
    }
    #btnIzquierda {
        grid-column: 1;
        grid-row: 2;
        background: #FF9800;
    }
    #btnDetener {
        grid-column: 2;
        grid-row: 2;
        background: #F44336;
        border-radius: 16px;
        width: 80px;
        height: 80px;
    }
    #btnDerecha {
        grid-column: 3;
        grid-row: 2;
        background: #FF9800;
    }
    #btnAtras {
        grid-column: 2;
        grid-row: 3;
        background: #FF9800;
    }
    .instructions {
        margin-top: 20px;
        font-size: 14px;
        color: #aaa;
    }
    @media (max-width: 400px) {
        .btn {
            width: 70px;
            height: 70px;
        }
        .btn i {
            font-size: 30px;
        }
    }
</style>
<script>
    // Función para enviar comandos
    function enviarComando(comando) {
        fetch(comando, { method: 'POST' })
            .catch(error => console.error('Error:', error));
    }
    
    // Variables para controlar el estado de pulsación
    let comandoActual = '';
    let intervalo = null;
    
    // Iniciar movimiento cuando se presiona un botón
    function iniciarMovimiento(comando) {
        if (comandoActual === comando) return;
        
        // Detener cualquier movimiento anterior
        if (intervalo) {
            clearInterval(intervalo);
            enviarComando('/detener');
        }
        
        comandoActual = comando;
        enviarComando(comando);
        
        // Enviar comandos repetidos cada 100ms mientras se mantiene presionado
        intervalo = setInterval(() => {
            enviarComando(comando);
        }, 100);
    }
    
    // Detener movimiento cuando se suelta el botón
    function detenerMovimiento() {
        if (intervalo) {
            clearInterval(intervalo);
            intervalo = null;
        }
        if (comandoActual) {
            enviarComando('/detener');
            comandoActual = '';
        }
    }
    
    // Configurar eventos para móviles y desktop
    function configurarBotones() {
        const botones = document.querySelectorAll('.btn');
        
        botones.forEach(boton => {
            // Eventos táctiles
            boton.ontouchstart = (e) => {
                e.preventDefault();
                const comando = boton.getAttribute('data-comando');
                if (comando) iniciarMovimiento(comando);
            };
            
            boton.ontouchend = (e) => {
                e.preventDefault();
                detenerMovimiento();
            };
            
            // Eventos de ratón
            boton.onmousedown = () => {
                const comando = boton.getAttribute('data-comando');
                if (comando) iniciarMovimiento(comando);
            };
            
            boton.onmouseup = detenerMovimiento;
            boton.onmouseleave = detenerMovimiento;
        });
        
        // Evitar desplazamiento en dispositivos móviles
        document.body.addEventListener('touchmove', (e) => {
            if (comandoActual) e.preventDefault();
        }, { passive: false });
    }
    
    // Inicializar al cargar la página
    window.addEventListener('load', configurarBotones);
</script>
</head>
<body>
    <div class="container">
        <h1>Control de Carro</h1>
        
        <div class="controls">
            <button id="btnAdelante" class="btn" data-comando="/adelante">
                <i class="material-icons">arrow_upward</i>
            </button>
            
            <button id="btnIzquierda" class="btn" data-comando="/izquierda">
                <i class="material-icons">arrow_back</i>
            </button>
            
            <button id="btnDetener" class="btn" data-comando="/detener">
                <i class="material-icons">stop</i>
            </button>
            
            <button id="btnDerecha" class="btn" data-comando="/derecha">
                <i class="material-icons">arrow_forward</i>
            </button>
            
            <button id="btnAtras" class="btn" data-comando="/atras">
                <i class="material-icons">arrow_downward</i>
            </button>
        </div>
        
        <div class="instructions">
            <p>Mantén presionado un botón para mover el carro</p>
        </div>
    </div>
</body>
</html>
"""

def mostrar_mensaje_oled(oled, linea1, linea2="", linea3="", linea4=""):
    """Muestra un mensaje de 4 líneas en la pantalla OLED"""
    if oled:
        try:
            oled.clear()
            oled.write_text(linea1, 0, 0)
            oled.write_text(linea2, 0, 10)
            oled.write_text(linea3, 0, 20)
            oled.write_text(linea4, 0, 30)
            time.sleep(0.1)
        except Exception as e:
            print("Error al mostrar mensaje en OLED:", e)

def manejar_solicitud(conn, request, carro, oled):
    try:
        request_str = request.decode('utf-8')
        
        # Manejar solicitud GET para la página principal
        if 'GET / ' in request_str or 'GET /' in request_str:
            conn.send('HTTP/1.1 200 OK\r\n')
            conn.send('Content-Type: text/html\r\n')
            conn.send('Connection: close\r\n\r\n')
            conn.send(HTML_PAGINA)
            
        # Manejar comandos POST
        elif 'POST /adelante' in request_str:
            carro.avanzar_continuo()
            conn.send('HTTP/1.1 200 OK\r\n\r\nOK')
            
        elif 'POST /atras' in request_str:
            carro.retroceder_continuo()
            conn.send('HTTP/1.1 200 OK\r\n\r\nOK')
            
        elif 'POST /izquierda' in request_str:
            carro.girar_izquierda_continuo()
            conn.send('HTTP/1.1 200 OK\r\n\r\nOK')
            
        elif 'POST /derecha' in request_str:
            carro.girar_derecha_continuo()
            conn.send('HTTP/1.1 200 OK\r\n\r\nOK')
            
        elif 'POST /detener' in request_str:
            carro.detener()
            conn.send('HTTP/1.1 200 OK\r\n\r\nOK')
            
        else:
            # Respuesta para otras solicitudes
            conn.send('HTTP/1.1 404 Not Found\r\n\r\n')
            
    except Exception as e:
        print('Error en solicitud:', e)
    finally:
        conn.close()

def iniciar_servidor_web(ip, carro, oled):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ip, 80))
    s.listen(5)
    
    # Mostrar en OLED que el servidor está activo
    mostrar_mensaje_oled(oled, "Servidor activo", "IP:", ip, "Esperando conexiones")
    print('Servidor en http://%s' % ip)
    
    # Configurar timeout para prevenir bloqueos
    s.settimeout(0.1)
    
    try:
        while True:
            try:
                conn, addr = s.accept()
                conn.settimeout(3.0)
                request = conn.recv(1024)
                if request:
                    # Mostrar actividad en OLED
                    mostrar_mensaje_oled(oled, "Conexion recibida", f"Desde: {addr[0]}", "Procesando...")
                    
                    manejar_solicitud(conn, request, carro, oled)
                    
                    # Restaurar IP después de procesar
                    mostrar_mensaje_oled(oled, "Servidor activo", "IP:", ip, "Esperando conexiones")
                else:
                    conn.close()
            except OSError as e:
                # Timeout, no hay conexiones nuevas
                if e.args[0] not in (110, 11, 116):  # Ignorar timeouts esperados
                    print('Error aceptando conexión:', e)
            except Exception as e:
                print('Error en servidor:', e)
                if 'conn' in locals():
                    conn.close()
    except Exception as e:
        print('Error crítico en servidor:', e)
    finally:
        s.close()