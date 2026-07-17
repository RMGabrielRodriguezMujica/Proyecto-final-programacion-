"""
undo.py
-------
Sistema de Deshacer (Undo) de operaciones de organizacion.
Cada vez que organizer.py mueve o renombra archivos de verdad (dry_run=False),
registra los cambios aqui. Este modulo permite revertir la ultima operacion
realizada, por si el usuario se equivoco de carpeta o de patron.
"""

import os
import json
import shutil
from datetime import datetime

from utils import registrar_actividad, print_ok, print_warn, print_error

HISTORIAL_FILE = "historial_operaciones.json"


def _cargar_historial():
    """Carga el historial de operaciones desde disco (lista de operaciones)."""
    if not os.path.exists(HISTORIAL_FILE):
        return []
    try:
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def _guardar_historial(historial):
    """Guarda la lista de operaciones en disco."""
    try:
        with open(HISTORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
    except OSError as e:
        raise IOError(f"No se pudo guardar el historial de operaciones: {e}")


@registrar_actividad
def registrar_operacion(nombre_operacion, cambios):
    """
    Guarda en el historial una operacion reversible.
    'cambios' es una lista de diccionarios con alguna de estas formas:
      {"tipo": "mover", "origen": ruta_original, "destino": ruta_nueva}
      {"tipo": "renombrar", "carpeta": carpeta, "anterior": nombre, "nuevo": nombre}
    Si 'cambios' esta vacia, no se registra nada (no hubo modificaciones reales).
    """
    if not cambios:
        return

    historial = _cargar_historial()
    historial.append({
        "operacion": nombre_operacion,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cambios": cambios,
    })
    _guardar_historial(historial)


@registrar_actividad
def deshacer_ultima_operacion():
    """
    Revierte la ultima operacion de organizacion registrada: mueve de vuelta
    los archivos movidos y renombra de vuelta los archivos renombrados.
    Retorna un resumen con exitos y errores encontrados al revertir.
    """
    historial = _cargar_historial()
    if not historial:
        raise LookupError("No hay operaciones registradas para deshacer.")

    ultima = historial.pop()
    exitos, errores = [], []
    carpetas_a_revisar = set()

    # Se revierte en orden inverso al que se aplicaron los cambios
    for cambio in reversed(ultima["cambios"]):
        try:
            if cambio["tipo"] == "mover":
                origen, destino = cambio["origen"], cambio["destino"]
                if os.path.exists(destino):
                    shutil.move(destino, origen)
                    exitos.append(f"{os.path.basename(destino)} -> {origen}")
                    carpetas_a_revisar.add(os.path.dirname(destino))
                else:
                    errores.append(f"No se encontro '{destino}' para revertir.")

            elif cambio["tipo"] == "renombrar":
                carpeta, anterior, nuevo = cambio["carpeta"], cambio["anterior"], cambio["nuevo"]
                ruta_actual = os.path.join(carpeta, nuevo)
                ruta_original = os.path.join(carpeta, anterior)
                if os.path.exists(ruta_actual):
                    os.rename(ruta_actual, ruta_original)
                    exitos.append(f"{nuevo} -> {anterior}")
                else:
                    errores.append(f"No se encontro '{ruta_actual}' para revertir.")
            else:
                errores.append(f"Tipo de cambio desconocido: {cambio.get('tipo')}")

        except OSError as e:
            errores.append(f"Error al revertir {cambio}: {e}")

    # Limpieza: si alguna carpeta de destino quedo vacia, se elimina
    for carpeta in carpetas_a_revisar:
        try:
            if os.path.isdir(carpeta) and not os.listdir(carpeta):
                os.rmdir(carpeta)
        except OSError:
            pass  # si no se puede borrar, se deja tal cual (no es critico)

    _guardar_historial(historial)

    return {
        "operacion_deshecha": ultima["operacion"],
        "fecha_original": ultima["fecha"],
        "exitos": exitos,
        "errores": errores,
    }


def ver_historial(limite=10):
    """Retorna las ultimas 'limite' operaciones registradas (la mas reciente primero)."""
    historial = _cargar_historial()
    return list(reversed(historial))[:limite]
