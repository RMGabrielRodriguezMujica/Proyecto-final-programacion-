"""
utils.py
--------
Modulo de utilidades comunes para el Kit Multifuncional de Automatizacion
de Archivos. Contiene validaciones, decoradores, generadores y utilidades
de interfaz (banner ASCII, colores, sonido, barra de progreso) reutilizadas
por organizer.py, analyzer.py, auditor.py y reports.py.
"""

import os
import sys
import time
import hashlib
import functools
from datetime import datetime

AUDIT_LOG_FILE = "audit.log"


# ---------------------------------------------------------------------------
# Colores ANSI para mejorar la salida en terminal
# ---------------------------------------------------------------------------
class Color:
    OK = "\033[92m"
    WARN = "\033[93m"
    ERROR = "\033[91m"
    INFO = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CIAN = "\033[96m"
    MAGENTA = "\033[95m"
    AZUL = "\033[94m"
    GRIS = "\033[90m"


def print_ok(msg):
    print(f"{Color.OK}[OK]{Color.RESET} {msg}")


def print_warn(msg):
    print(f"{Color.WARN}[!]{Color.RESET} {msg}")


def print_error(msg):
    print(f"{Color.ERROR}[ERROR]{Color.RESET} {msg}")


def print_info(msg):
    print(f"{Color.INFO}[i]{Color.RESET} {msg}")


# ---------------------------------------------------------------------------
# Banner ASCII de bienvenida
# ---------------------------------------------------------------------------
# BANNER_ASCII = r"""
#  _  __ ___ _____    _         _                            _   _
# | |/ /|_ _|_   _|  / \  _   _| |_ ___  _ __ ___   __ _ ___(_) | |_
# | ' /  | |  | |   / _ \| | | | __/ _ \| '_ ` _ \ / _` / __| | | __|
# | . \  | |  | |  / ___ \ |_| | || (_) | | | | | | (_| \__ \_|_| |_
# |_|\_\|___| |_| /_/   \_\__,_|\__\___/|_| |_| |_|\__,_|___(_|_) \__|

#      DE  A R C H I V O S  -  Proyecto Final Unidad VII
# """


BANNER_ASCII = r"""
                 _  __ ___ _____   
                | |/ /|_ _|_   _|    GABRIEL  RODRIGUEZ - GERM
                | ' /  | |  | |      SEBATIAN RODRIGUEZ -  SR
                | . \  | |  | |      SEBATIAN MATTO     -  SM
                |_|\_\|___| |_|  
    _         _                        _   _                    _             
   / \  _   _| |_ ___  _ __ ___   __ _| |_(_)____ _    ___(_) ___  _ __  
  / _ \| | | | __/ _ \| '_ ` _ \ / _` | __| |_  / _` |/ __| |/ _ \| '_ \ 
 / ___ \ |_| | || (_) | | | | | | (_| | |_| |/ / (_| | (__| | (_) | | | |
/_/   \_\__,_|\__\___/|_| |_| |_|\__,_|\__|_/___\__,_|\___|_|\___/|_| |_|

               DE  A R C H I V O S  -  Proyecto Final Unidad VII
"""

def mostrar_banner():
    """ Imprime el banner ASCII de bienvenida con color, una sola vez al iniciar. """
    print(f"{Color.CIAN}{Color.BOLD}{BANNER_ASCII}{Color.RESET}")
    print(f"{Color.GRIS}{'=' * 66}{Color.RESET}")


def imprimir_titulo(texto):
    """Imprime un titulo de seccion dentro de un recuadro de color."""
    ancho = max(len(texto) + 4, 40)
    print(f"\n{Color.MAGENTA}{'-' * ancho}{Color.RESET}")
    print(f"{Color.MAGENTA}{Color.BOLD}  {texto.upper()}{Color.RESET}")
    print(f"{Color.MAGENTA}{'-' * ancho}{Color.RESET}")


# ---------------------------------------------------------------------------
# Sonido (con alternativa segura si el sistema operativo no lo soporta)
# ---------------------------------------------------------------------------
def reproducir_sonido(tipo="ok"):
    """
    Reproduce un sonido corto segun el resultado de una operacion.
    En Windows usa winsound; en otros sistemas emite el timbre ASCII (\\a)
    como alternativa segura, para que el programa funcione en cualquier equipo.
    """
    frecuencias = {"ok": 880, "error": 300, "aviso": 550}
    frecuencia = frecuencias.get(tipo, 700)
    try:
        import winsound
        winsound.Beep(frecuencia, 150)
    except (ImportError, RuntimeError, ValueError):
        try:
            sys.stdout.write("\a")
            sys.stdout.flush()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Barra de progreso animada (para operaciones sobre muchos archivos)
# ---------------------------------------------------------------------------
def con_barra_progreso(items, descripcion="Procesando"):
    """
    Envuelve una lista de elementos y muestra una barra de progreso animada
    en la misma linea de la terminal mientras se itera sobre ellos.
    """
    total = len(items)
    if total == 0:
        return
    ancho_barra = 30
    for indice, item in enumerate(items, start=1):
        progreso = int((indice / total) * ancho_barra)
        barra = "#" * progreso + "-" * (ancho_barra - progreso)
        porcentaje = int((indice / total) * 100)
        print(f"\r{Color.CIAN}{descripcion} [{barra}] {porcentaje}%{Color.RESET}", end="", flush=True)
        yield item
        time.sleep(0.02)
    print()


# ---------------------------------------------------------------------------
# Validaciones de entrada
# ---------------------------------------------------------------------------
def validar_carpeta(ruta):
    """
    Valida que una ruta exista y sea un directorio.
    Lanza FileNotFoundError o NotADirectoryError si no es valida.
    """
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"La ruta '{ruta}' no existe.")
    if not os.path.isdir(ruta):
        raise NotADirectoryError(f"La ruta '{ruta}' no es una carpeta.")
    return True


def pedir_opcion(mensaje, opciones_validas):
    """
    Solicita al usuario una opcion dentro de un conjunto valido.
    Se repite hasta recibir una entrada correcta.
    """
    while True:
        opcion = input(mensaje).strip().lower()
        if opcion in opciones_validas:
            return opcion
        print_error(f"Opcion invalida. Opciones validas: {', '.join(sorted(opciones_validas))}")


def pedir_ruta_valida(mensaje):
    """Solicita al usuario una ruta de carpeta valida, repitiendo si falla."""
    while True:
        ruta = input(mensaje).strip()
        try:
            validar_carpeta(ruta)
            return ruta
        except (FileNotFoundError, NotADirectoryError) as e:
            print_error(str(e))


# ---------------------------------------------------------------------------
# Decorador principal: registra ejecucion, tiempo y errores de funciones
# criticas del sistema en audit.log. Requisito obligatorio del proyecto.
# ---------------------------------------------------------------------------
def registrar_actividad(func):
    """
    Decorador que envuelve una funcion para registrar en audit.log:
    marca de tiempo, nombre de la funcion, duracion de ejecucion y si
    finalizo correctamente o con error.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            resultado = func(*args, **kwargs)
            duracion = round(time.time() - inicio, 4)
            escribir_log(f"{timestamp} | OK    | {func.__name__:<28} | {duracion}s")
            return resultado
        except Exception as e:
            duracion = round(time.time() - inicio, 4)
            escribir_log(f"{timestamp} | ERROR | {func.__name__:<28} | {duracion}s | {e}")
            raise
    return wrapper


_AVISO_LOG_MOSTRADO = False


def escribir_log(linea):
    """
    Escribe (append) una linea en el archivo audit.log.
    Si no hay permisos de escritura (comun en Windows por Descargas/Documentos
    protegidos), avisa UNA sola vez con instrucciones claras, en vez de repetir
    el mismo error por cada archivo procesado.
    """
    global _AVISO_LOG_MOSTRADO
    try:
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as log:
            log.write(linea + "\n")
    except PermissionError:
        if not _AVISO_LOG_MOSTRADO:
            print_error(
                "Sin permisos para escribir 'audit.log' en esta carpeta.\n"
                "     Esto suele pasar en Windows si el proyecto esta dentro de\n"
                "     Descargas/Documentos/Escritorio (proteccion contra ransomware)\n"
                "     o si la carpeta quedo marcada como 'Solo lectura' al extraer el ZIP.\n"
                "     Solucion: mueve la carpeta a otra ubicacion (ej: C:\\Proyectos\\)\n"
                "     o quita el atributo 'Solo lectura' en Propiedades de la carpeta.\n"
                "     El programa seguira funcionando, pero sin guardar el historial."
            )
            _AVISO_LOG_MOSTRADO = True
    except OSError as e:
        print_error(f"No se pudo escribir en el log: {e}")


# ---------------------------------------------------------------------------
# Generadores (lectura eficiente de archivos y carpetas)
# ---------------------------------------------------------------------------
def leer_lineas(ruta_archivo):
    """
    Generador que lee un archivo de texto linea por linea, permitiendo
    procesar archivos grandes sin cargarlos completos en memoria.
    Entrega tuplas (numero_de_linea, contenido_de_linea).
    """
    try:
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            for numero_linea, linea in enumerate(f, start=1):
                yield numero_linea, linea.rstrip("\n")
    except OSError as e:
        raise IOError(f"No se pudo leer el archivo '{ruta_archivo}': {e}")


def listar_archivos(carpeta):
    """
    Generador que recorre una carpeta (nivel superior, sin subcarpetas)
    y entrega la ruta completa de cada archivo encontrado.
    """
    try:
        for nombre in sorted(os.listdir(carpeta)):
            ruta_completa = os.path.join(carpeta, nombre)
            if os.path.isfile(ruta_completa):
                yield ruta_completa
    except OSError as e:
        raise IOError(f"No se pudo listar la carpeta '{carpeta}': {e}")


def obtener_metadata(ruta_archivo):
    """Devuelve un diccionario con metadatos basicos de un archivo."""
    stat = os.stat(ruta_archivo)
    extension = os.path.splitext(ruta_archivo)[1].lower() or ".sin_extension"
    return {
        "nombre": os.path.basename(ruta_archivo),
        "extension": extension,
        "tamano": stat.st_size,
        "modificado": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_mod": stat.st_mtime,
    }


def calcular_hash_archivo(ruta_archivo, bloque=65536):
    """
    Calcula el hash MD5 del contenido de un archivo, leyendo por bloques
    para no cargarlo completo en memoria. Se usa tanto en auditor.py
    (deteccion de cambios) como en analyzer.py (deteccion de duplicados).
    """
    hasher = hashlib.md5()
    try:
        with open(ruta_archivo, "rb") as f:
            for bloque_datos in iter(lambda: f.read(bloque), b""):
                hasher.update(bloque_datos)
        return hasher.hexdigest()
    except OSError as e:
        raise IOError(f"No se pudo calcular el hash de '{ruta_archivo}': {e}")


def formatear_tamano(bytes_):
    """Convierte un tamano en bytes a una cadena legible (KB, MB, GB)."""
    tamano = float(bytes_)
    for unidad in ("B", "KB", "MB", "GB"):
        if tamano < 1024:
            return f"{tamano:.1f} {unidad}"
        tamano /= 1024
    return f"{tamano:.1f} TB"


# ---------------------------------------------------------------------------
# Verificacion de permisos de escritura (evita sorpresas a mitad de operacion)
# ---------------------------------------------------------------------------
def verificar_permisos_escritura():
    """
    Intenta crear/escribir un archivo temporal en la carpeta actual para
    detectar problemas de permisos ANTES de que el usuario empiece a usar
    el sistema. Si falla, muestra instrucciones claras (comun en Windows
    por Descargas/Documentos protegidos por 'Controlled Folder Access').
    Retorna True si se puede escribir, False si no.
    """
    archivo_prueba = ".permisos_test.tmp"
    try:
        with open(archivo_prueba, "w", encoding="utf-8") as f:
            f.write("test")
        os.remove(archivo_prueba)
        return True
    except (PermissionError, OSError):
        print_warn(
            "No se detectaron permisos de escritura en esta carpeta.\n"
            "     En Windows esto casi siempre se debe a:\n"
            "       1) El proyecto esta dentro de Descargas/Documentos/Escritorio\n"
            "          y la 'Proteccion contra ransomware' de Windows lo bloquea.\n"
            "       2) La carpeta quedo marcada como 'Solo lectura' al extraer el ZIP.\n"
            "     Soluciones sugeridas:\n"
            "       - Mueve la carpeta a otra ubicacion, ej: C:\\Proyectos\\\n"
            "       - O clic derecho en la carpeta > Propiedades > desmarcar 'Solo lectura'\n"
            "         (aplicar a todas las subcarpetas y archivos)\n"
            "     El programa puede seguir, pero no podra guardar logs, reportes ni snapshots."
        )
        return False
