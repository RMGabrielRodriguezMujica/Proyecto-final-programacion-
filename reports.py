"""
reports.py
----------
Generador de Reportes.
Crea reportes en formato .txt y .csv a partir de los resultados
producidos por organizer.py, analyzer.py y auditor.py.
"""

import os
import csv
from datetime import datetime

from utils import registrar_actividad, print_ok, print_warn

CARPETA_REPORTES = "reportes"


def _ruta_reporte(nombre_base, extension):
    """Construye una ruta unica (con timestamp) dentro de la carpeta 'reportes/'."""
    # Cada reporte recibe una marca de tiempo para evitar sobrescribir archivos
    # anteriores y facilitar su trazabilidad.
    try:
        os.makedirs(CARPETA_REPORTES, exist_ok=True)
    except PermissionError as e:
        raise IOError(
            f"No se pudo crear la carpeta '{CARPETA_REPORTES}/': permiso denegado. "
            f"Mueve el proyecto fuera de Descargas/Documentos o quita el atributo "
            f"'Solo lectura' de la carpeta. Detalle: {e}"
        )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(CARPETA_REPORTES, f"{nombre_base}_{timestamp}.{extension}")


@registrar_actividad
def generar_reporte_txt(datos, nombre_base, titulo):
    """
    Genera un reporte de texto legible a partir de un diccionario o
    lista de datos. Retorna la ruta del archivo generado.
    """
    ruta = _ruta_reporte(nombre_base, "txt")
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(f"{titulo}\n")
            f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")

            if isinstance(datos, dict):
                for clave, valor in datos.items():
                    f.write(f"{clave}: {valor}\n")
            elif isinstance(datos, list):
                for item in datos:
                    f.write(f"{item}\n")
            else:
                f.write(str(datos))
    except OSError as e:
        raise IOError(f"No se pudo generar el reporte TXT: {e}")

    return ruta


@registrar_actividad
def generar_reporte_csv(filas, encabezados, nombre_base):
    """
    Genera un reporte CSV a partir de una lista de filas (listas o
    tuplas) y una lista de encabezados de columna.
    """
    ruta = _ruta_reporte(nombre_base, "csv")
    try:
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            escritor.writerow(encabezados)
            escritor.writerows(filas)
    except OSError as e:
        raise IOError(f"No se pudo generar el reporte CSV: {e}")

    return ruta


@registrar_actividad
def reporte_organizacion(resultado_clasificacion, nombre_base="reporte_organizacion"):
    """Genera reportes TXT y CSV a partir del resultado de una clasificacion de archivos."""
    ruta_txt = generar_reporte_txt(
        resultado_clasificacion, nombre_base, "Reporte de Organizacion de Archivos"
    )
    filas = [(categoria, len(archivos)) for categoria, archivos in resultado_clasificacion.items()]
    ruta_csv = generar_reporte_csv(filas, ["Categoria", "Cantidad de archivos"], nombre_base)
    return ruta_txt, ruta_csv


@registrar_actividad
def reporte_analisis(resultado_analisis, nombre_base="reporte_analisis"):
    """Genera reportes TXT y CSV a partir del resultado del analizador de contenido."""
    ruta_txt = generar_reporte_txt(
        resultado_analisis, nombre_base, "Reporte de Analisis de Contenido"
    )
    filas = [
        (valor, frecuencia)
        for valor, frecuencia in resultado_analisis.get("frecuencias", {}).items()
    ]
    ruta_csv = generar_reporte_csv(filas, ["Coincidencia", "Frecuencia"], nombre_base)
    return ruta_txt, ruta_csv


@registrar_actividad
def reporte_auditoria(diferencias, nombre_base="reporte_auditoria"):
    """Genera reportes TXT y CSV a partir del resultado de una auditoria de cambios."""
    ruta_txt = generar_reporte_txt(diferencias, nombre_base, "Reporte de Auditoria de Cambios")
    filas = []
    for tipo_cambio, archivos in diferencias.items():
        for archivo in archivos:
            filas.append((tipo_cambio, archivo))
    ruta_csv = generar_reporte_csv(filas, ["Tipo de cambio", "Archivo"], nombre_base)
    return ruta_txt, ruta_csv


# ---------------------------------------------------------------------------
# Grafico visual (extra / dinamico) con matplotlib
# ---------------------------------------------------------------------------
@registrar_actividad
def generar_grafico_barras(datos, nombre_base, titulo, etiqueta_x="Categoria", etiqueta_y="Cantidad"):
    """
    Genera un grafico de barras en PNG a partir de un diccionario
    {categoria: cantidad}. Es una funcionalidad extra para dar una vista
    rapida y visual de los resultados de organizacion, analisis o auditoria.
    Si matplotlib no esta instalado, informa y no interrumpe el programa.
    """
    if not datos:
        print_warn("No hay datos para graficar.")
        return None

    try:
        import matplotlib
        matplotlib.use("Agg")  # backend sin interfaz grafica, apto para consola
        import matplotlib.pyplot as plt
        # Se dibuja el grafico en memoria y luego se guarda como archivo PNG.
    except ImportError:
        print_warn("matplotlib no esta instalado; se omite el grafico. "
                    "Instalalo con: pip install matplotlib")
        return None

    os.makedirs(CARPETA_REPORTES, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = os.path.join(CARPETA_REPORTES, f"{nombre_base}_{timestamp}.png")

    categorias = list(datos.keys())
    valores = list(datos.values())

    try:
        fig, ax = plt.subplots(figsize=(7, 4.2))
        barras = ax.bar(categorias, valores, color="#2b5e8c")
        ax.set_title(titulo)
        ax.set_xlabel(etiqueta_x)
        ax.set_ylabel(etiqueta_y)
        ax.bar_label(barras, padding=3)
        plt.xticks(rotation=30, ha="right")
        fig.tight_layout()
        fig.savefig(ruta, dpi=140)
        plt.close(fig)
    except OSError as e:
        raise IOError(f"No se pudo generar el grafico: {e}")

    print_ok(f"Grafico generado en: {ruta}")
    return ruta
