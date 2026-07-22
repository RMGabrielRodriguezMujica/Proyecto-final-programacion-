"""
organizer.py
------------
Gestor de Organizacion de Archivos.
Clasifica archivos por extension, tamano y fecha de modificacion,
renombra archivos mediante expresiones regulares y los mueve a
carpetas de destino. Soporta modo simulacion (dry-run) y registra
cada cambio real en undo.py para poder deshacerlo despues.
"""

import os
import re
import shutil
from datetime import datetime

from utils import (
    registrar_actividad,
    listar_archivos,
    obtener_metadata,
    con_barra_progreso,
    print_ok,
    print_info,
    print_warn,
)
import undo

# Umbrales de tamano usados para clasificar archivos (en bytes)
UMBRAL_PEQUENO = 100 * 1024        # 100 KB
UMBRAL_MEDIANO = 5 * 1024 * 1024   # 5 MB


@registrar_actividad
def clasificar_por_extension(carpeta, dry_run=False):
    """
    Agrupa los archivos de 'carpeta' por extension. Si dry_run es False,
    los mueve a subcarpetas nombradas segun la extension (ej: .txt -> TXT/)
    y registra cada movimiento para poder deshacerlo.
    Retorna un diccionario {extension: [nombres_de_archivo]}.
    """
    resultado = {}
    cambios = []
    archivos = list(listar_archivos(carpeta))

    # Cada archivo se agrupa segun su extension y, si el modo no es simulacion,
    # se mueve a la carpeta destino correspondiente.
    for ruta in con_barra_progreso(archivos, "Clasificando por extension"):
        meta = obtener_metadata(ruta)
        ext = meta["extension"].replace(".", "").upper() or "SIN_EXTENSION"
        resultado.setdefault(ext, []).append(meta["nombre"])

        if not dry_run:
            destino_carpeta = os.path.join(carpeta, ext)
            os.makedirs(destino_carpeta, exist_ok=True)
            ruta_destino = os.path.join(destino_carpeta, meta["nombre"])
            try:
                shutil.move(ruta, ruta_destino)
                cambios.append({"tipo": "mover", "origen": ruta, "destino": ruta_destino})
            except (shutil.Error, OSError) as e:
                print_warn(f"No se pudo mover '{meta['nombre']}': {e}")

    undo.registrar_operacion("clasificar_por_extension", cambios)
    _reportar_modo(dry_run, "clasificacion por extension")
    return resultado


@registrar_actividad
def clasificar_por_tamano(carpeta, dry_run=False):
    """
    Clasifica archivos en 'Pequenos', 'Medianos' y 'Grandes' segun su
    tamano, moviendolos a subcarpetas correspondientes si dry_run es False.
    """
    categorias = {"Pequenos": [], "Medianos": [], "Grandes": []}
    cambios = []
    archivos = list(listar_archivos(carpeta))

    # Se aplica la misma logica de clasificacion, pero usando umbrales de
    # tamano para decidir en que categoria entra cada archivo.
    for ruta in con_barra_progreso(archivos, "Clasificando por tamano"):
        meta = obtener_metadata(ruta)
        if meta["tamano"] < UMBRAL_PEQUENO:
            categoria = "Pequenos"
        elif meta["tamano"] < UMBRAL_MEDIANO:
            categoria = "Medianos"
        else:
            categoria = "Grandes"
        categorias[categoria].append(meta["nombre"])

        if not dry_run:
            destino_carpeta = os.path.join(carpeta, categoria)
            os.makedirs(destino_carpeta, exist_ok=True)
            ruta_destino = os.path.join(destino_carpeta, meta["nombre"])
            try:
                shutil.move(ruta, ruta_destino)
                cambios.append({"tipo": "mover", "origen": ruta, "destino": ruta_destino})
            except (shutil.Error, OSError) as e:
                print_warn(f"No se pudo mover '{meta['nombre']}': {e}")

    undo.registrar_operacion("clasificar_por_tamano", cambios)
    _reportar_modo(dry_run, "clasificacion por tamano")
    return categorias


@registrar_actividad
def clasificar_por_fecha(carpeta, dry_run=False):
    """
    Clasifica archivos segun su fecha de modificacion (formato anio-mes),
    moviendolos a subcarpetas correspondientes si dry_run es False.
    """
    grupos = {}
    cambios = []
    archivos = list(listar_archivos(carpeta))

    for ruta in con_barra_progreso(archivos, "Clasificando por fecha"):
        meta = obtener_metadata(ruta)
        periodo = datetime.fromtimestamp(meta["timestamp_mod"]).strftime("%Y-%m")
        grupos.setdefault(periodo, []).append(meta["nombre"])

        if not dry_run:
            destino_carpeta = os.path.join(carpeta, periodo)
            os.makedirs(destino_carpeta, exist_ok=True)
            ruta_destino = os.path.join(destino_carpeta, meta["nombre"])
            try:
                shutil.move(ruta, ruta_destino)
                cambios.append({"tipo": "mover", "origen": ruta, "destino": ruta_destino})
            except (shutil.Error, OSError) as e:
                print_warn(f"No se pudo mover '{meta['nombre']}': {e}")

    undo.registrar_operacion("clasificar_por_fecha", cambios)
    _reportar_modo(dry_run, "clasificacion por fecha")
    return grupos


@registrar_actividad
def renombrar_con_patron(carpeta, patron, reemplazo, dry_run=False):
    """
    Renombra los archivos de 'carpeta' cuyo nombre coincide con la
    expresion regular 'patron', sustituyendo la coincidencia por
    'reemplazo'. Retorna una lista de tuplas (nombre_original, nombre_nuevo).
    """
    try:
        regex = re.compile(patron)
    except re.error as e:
        raise ValueError(f"Patron de expresion regular invalido: {e}")

    cambios_reporte = []
    cambios_undo = []
    archivos = list(listar_archivos(carpeta))

    # Se busca coincidir el nombre actual con la expresion regular y se calcula
    # el nuevo nombre para luego registrar la operacion de undo si aplica.
    for ruta in con_barra_progreso(archivos, "Renombrando archivos"):
        nombre_actual = os.path.basename(ruta)
        if regex.search(nombre_actual):
            nuevo_nombre = regex.sub(reemplazo, nombre_actual)
            if nuevo_nombre != nombre_actual:
                cambios_reporte.append((nombre_actual, nuevo_nombre))
                if not dry_run:
                    try:
                        os.rename(ruta, os.path.join(carpeta, nuevo_nombre))
                        cambios_undo.append({
                            "tipo": "renombrar", "carpeta": carpeta,
                            "anterior": nombre_actual, "nuevo": nuevo_nombre,
                        })
                    except OSError as e:
                        print_warn(f"No se pudo renombrar '{nombre_actual}': {e}")

    undo.registrar_operacion("renombrar_con_patron", cambios_undo)
    _reportar_modo(dry_run, "renombrado por patron")
    return cambios_reporte


def _reportar_modo(dry_run, accion):
    """Imprime un mensaje indicando si la accion fue simulada o aplicada."""
    if dry_run:
        print_info(f"[SIMULACION] Se calculo la {accion} sin aplicar cambios reales.")
    else:
        print_ok(f"Se aplico la {accion} correctamente.")
