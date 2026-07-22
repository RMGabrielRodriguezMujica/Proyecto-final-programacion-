"""
auditor.py
----------
Auditor de Cambios.
Genera snapshots (fotografias) del estado de una carpeta, los compara
para detectar archivos nuevos, modificados o eliminados, y registra el
historial de auditorias en audit.log.
"""

import os
import json
from datetime import datetime

from utils import registrar_actividad, listar_archivos, obtener_metadata, escribir_log, calcular_hash_archivo

CARPETA_SNAPSHOTS = "snapshots"


@registrar_actividad
def crear_snapshot(carpeta, nombre_snapshot=None):
    """
    Crea un snapshot del estado actual de 'carpeta': nombre, tamano,
    fecha de modificacion y hash de cada archivo. Se guarda como JSON
    dentro de la carpeta 'snapshots/'. Retorna la ruta del snapshot creado.
    """
    try:
        os.makedirs(CARPETA_SNAPSHOTS, exist_ok=True)
    except PermissionError as e:
        raise IOError(
            f"No se pudo crear la carpeta '{CARPETA_SNAPSHOTS}/': permiso denegado. "
            f"Mueve el proyecto fuera de Descargas/Documentos o quita el atributo "
            f"'Solo lectura' de la carpeta. Detalle: {e}"
        )
    estado = {}
    # Se construye un estado resumido de cada archivo para poder comparar despues
    # si hubo cambios en nombre, tamano, fecha o contenido hash.
    for ruta in listar_archivos(carpeta):
        meta = obtener_metadata(ruta)
        estado[meta["nombre"]] = {
            "tamano": meta["tamano"],
            "modificado": meta["modificado"],
            "hash": calcular_hash_archivo(ruta),
        }

    if nombre_snapshot is None:
        nombre_snapshot = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    ruta_snapshot = os.path.join(CARPETA_SNAPSHOTS, nombre_snapshot)
    try:
        with open(ruta_snapshot, "w", encoding="utf-8") as f:
            json.dump(estado, f, indent=4, ensure_ascii=False)
    except OSError as e:
        raise IOError(f"No se pudo guardar el snapshot: {e}")

    return ruta_snapshot


def _ultimo_snapshot(excluir=None):
    """Retorna la ruta del snapshot mas reciente disponible, o None si no existe ninguno."""
    if not os.path.isdir(CARPETA_SNAPSHOTS):
        return None
    snapshots = [
        f for f in os.listdir(CARPETA_SNAPSHOTS)
        if f.endswith(".json") and f != excluir
    ]
    if not snapshots:
        return None
    snapshots.sort()
    return os.path.join(CARPETA_SNAPSHOTS, snapshots[-1])


def _cargar_snapshot(ruta_snapshot):
    """Carga un snapshot JSON desde disco y lo retorna como diccionario."""
    try:
        with open(ruta_snapshot, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise IOError(f"No se pudo leer el snapshot '{ruta_snapshot}': {e}")


@registrar_actividad
def comparar_snapshots(snapshot_anterior, snapshot_actual):
    """
    Compara dos snapshots (diccionarios) y detecta archivos nuevos,
    modificados (mismo nombre, distinto hash) y eliminados.
    """
    archivos_anteriores = set(snapshot_anterior.keys())
    archivos_actuales = set(snapshot_actual.keys())

    nuevos = archivos_actuales - archivos_anteriores
    eliminados = archivos_anteriores - archivos_actuales
    modificados = {
        nombre for nombre in archivos_actuales & archivos_anteriores
        if snapshot_actual[nombre]["hash"] != snapshot_anterior[nombre]["hash"]
    }

    return {
        "nuevos": sorted(nuevos),
        "modificados": sorted(modificados),
        "eliminados": sorted(eliminados),
    }


@registrar_actividad
def auditar_carpeta(carpeta):
    """
    Flujo completo de auditoria: carga el ultimo snapshot guardado (si
    existe), genera uno nuevo, compara ambos y registra el resultado en
    audit.log. Retorna el diccionario de diferencias detectadas.
    """
    ruta_snapshot_previo = _ultimo_snapshot()
    snapshot_previo = _cargar_snapshot(ruta_snapshot_previo) if ruta_snapshot_previo else {}

    ruta_snapshot_nuevo = crear_snapshot(carpeta)
    snapshot_nuevo = _cargar_snapshot(ruta_snapshot_nuevo)

    diferencias = comparar_snapshots(snapshot_previo, snapshot_nuevo)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    escribir_log(
        f"{timestamp} | AUDITORIA | nuevos={len(diferencias['nuevos'])} "
        f"modificados={len(diferencias['modificados'])} "
        f"eliminados={len(diferencias['eliminados'])}"
    )
    return diferencias

    