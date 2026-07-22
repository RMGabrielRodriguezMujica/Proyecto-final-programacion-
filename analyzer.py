"""
analyzer.py
-----------
Analizador de Contenido.
Busca patrones (correos, telefonos, fechas) dentro de archivos de texto
usando expresiones regulares, extrae lineas relevantes y genera
resumenes de frecuencia y coincidencias unicas.
"""

import os
import re
from collections import Counter

from utils import (
    registrar_actividad, leer_lineas, listar_archivos, obtener_metadata,
    calcular_hash_archivo, formatear_tamano, con_barra_progreso, print_info,
)

# Patrones de busqueda disponibles para el analizador de contenido.
# Cada clave representa un tipo de dato que se desea detectar dentro del texto.
PATRONES = {
    "correos": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "telefonos": r"(?:\+?\d{1,3}[- ]?)?\(?\d{3,4}\)?[- ]?\d{3}[- ]?\d{4}",
    "fechas": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
}

# Se consideran archivos de texto plano aquellos con extensiones tipicas
# para documentos y codigo fuente, ya que el analizador trabaja sobre texto legible.
EXTENSIONES_TEXTO = {".txt", ".csv", ".log", ".md", ".py", ".json"}


@registrar_actividad
def buscar_patron_en_archivo(ruta_archivo, patron):
    """
    Busca un patron regex dentro de un archivo de texto usando el
    generador leer_lineas (eficiente incluso en archivos grandes).
    Retorna una lista de tuplas (numero_de_linea, texto_encontrado).
    """
    try:
        regex = re.compile(patron)
    except re.error as e:
        raise ValueError(f"Expresion regular invalida: {e}")

    coincidencias = []
    for numero_linea, linea in leer_lineas(ruta_archivo):
        for match in regex.finditer(linea):
            coincidencias.append((numero_linea, match.group()))
    return coincidencias


@registrar_actividad
def extraer_lineas_relevantes(ruta_archivo, palabra_clave):
    """
    Extrae las lineas completas de un archivo que contienen una
    palabra clave dada (busqueda insensible a mayusculas/minusculas).
    """
    regex = re.compile(re.escape(palabra_clave), re.IGNORECASE)
    lineas_relevantes = []
    for numero_linea, linea in leer_lineas(ruta_archivo):
        if regex.search(linea):
            lineas_relevantes.append((numero_linea, linea.strip()))
    return lineas_relevantes


@registrar_actividad
def analizar_carpeta(carpeta, tipo_patron="correos"):
    """
    Analiza todos los archivos de texto de una carpeta buscando el tipo
    de patron indicado ('correos', 'telefonos' o 'fechas'). Genera un
    resumen de coincidencias por archivo, un conjunto de coincidencias
    unicas y un contador de frecuencias globales.
    """
    if tipo_patron not in PATRONES:
        raise KeyError(f"Tipo de patron desconocido: '{tipo_patron}'")

    patron = PATRONES[tipo_patron]
    resumen_por_archivo = {}
    coincidencias_unicas = set()
    contador_global = Counter()

    # Se recorre cada archivo de la carpeta para buscar el patron solicitado.
    # Si el archivo no parece ser texto, se omite para evitar errores innecesarios.
    for ruta in listar_archivos(carpeta):
        if not _es_texto_probable(ruta):
            continue
        try:
            encontrados = buscar_patron_en_archivo(ruta, patron)
        except (IOError, ValueError) as e:
            print_info(f"Se omitio '{ruta}': {e}")
            continue

        nombre = os.path.basename(ruta)
        resumen_por_archivo[nombre] = len(encontrados)
        for _, valor in encontrados:
            coincidencias_unicas.add(valor)
            contador_global[valor] += 1

    return {
        "tipo_patron": tipo_patron,
        "resumen_por_archivo": resumen_por_archivo,
        "coincidencias_unicas": sorted(coincidencias_unicas),
        "frecuencias": dict(contador_global),
    }


def _es_texto_probable(ruta_archivo):
    """Determina heuristicamente si un archivo es de texto plano por su extension."""
    return os.path.splitext(ruta_archivo)[1].lower() in EXTENSIONES_TEXTO


# ---------------------------------------------------------------------------
# Resumen general de la carpeta (extra)
# ---------------------------------------------------------------------------
@registrar_actividad
def generar_resumen_general(carpeta):
    """
    Recorre una carpeta y genera una vista rapida de su contenido: total de
    archivos, espacio ocupado, cuantos archivos hay de cada extension, y
    cuales son el mas grande, el mas reciente y el mas antiguo.
    """
    archivos = list(listar_archivos(carpeta))
    if not archivos:
        return {
            "total_archivos": 0, "tamano_total": 0, "tamano_total_legible": "0 B",
            "por_extension": {}, "mas_grande": None, "mas_reciente": None, "mas_antiguo": None,
        }

    por_extension = Counter()
    tamano_total = 0
    mas_grande = None
    mas_reciente = None
    mas_antiguo = None

    for ruta in archivos:
        meta = obtener_metadata(ruta)
        por_extension[meta["extension"]] += 1
        tamano_total += meta["tamano"]

        if mas_grande is None or meta["tamano"] > mas_grande["tamano"]:
            mas_grande = meta
        if mas_reciente is None or meta["timestamp_mod"] > mas_reciente["timestamp_mod"]:
            mas_reciente = meta
        if mas_antiguo is None or meta["timestamp_mod"] < mas_antiguo["timestamp_mod"]:
            mas_antiguo = meta

    return {
        "total_archivos": len(archivos),
        "tamano_total": tamano_total,
        "tamano_total_legible": formatear_tamano(tamano_total),
        "por_extension": dict(por_extension),
        "mas_grande": {"nombre": mas_grande["nombre"], "tamano": formatear_tamano(mas_grande["tamano"])},
        "mas_reciente": {"nombre": mas_reciente["nombre"], "fecha": mas_reciente["modificado"]},
        "mas_antiguo": {"nombre": mas_antiguo["nombre"], "fecha": mas_antiguo["modificado"]},
    }


# ---------------------------------------------------------------------------
# Detector de archivos duplicados (extra)
# ---------------------------------------------------------------------------
@registrar_actividad
def buscar_duplicados(carpeta):
    """
    Detecta archivos con contenido identico (aunque tengan nombres distintos)
    calculando el hash MD5 de cada uno y agrupando los que coinciden.
    Retorna un diccionario {hash: [nombres_de_archivo]} SOLO con los grupos
    que tienen 2 o mas archivos (es decir, duplicados reales).
    """
    archivos = list(listar_archivos(carpeta))
    por_hash = {}

    for ruta in con_barra_progreso(archivos, "Calculando hashes"):
        try:
            hash_archivo = calcular_hash_archivo(ruta)
        except IOError as e:
            print_info(f"Se omitio '{ruta}': {e}")
            continue
        por_hash.setdefault(hash_archivo, []).append(os.path.basename(ruta))

    duplicados = {h: nombres for h, nombres in por_hash.items() if len(nombres) > 1}
    return duplicados
