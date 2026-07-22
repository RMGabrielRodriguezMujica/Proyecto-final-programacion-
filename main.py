"""
main.py
-------
Menu principal del Kit Multifuncional de Automatizacion de Archivos.
Integra los modulos organizer, analyzer, auditor, reports y undo mediante
una interfaz de linea de comandos (CLI) con banner ASCII, colores y sonido.
"""

import sys

from utils import (
    pedir_opcion, pedir_ruta_valida, print_ok, print_error, print_info, print_warn,
    Color, mostrar_banner, imprimir_titulo, reproducir_sonido, verificar_permisos_escritura,
    formatear_tamano,
)
import organizer
import analyzer
import auditor
import reports
import undo

# Mapa de opciones del menu de organizacion: cada clave representa una opcion
# numerica y cada valor contiene el nombre de la funcion del modulo y la
# referencia callable que debe ejecutarse.
FUNCIONES_CLASIFICACION = {
    "1": ("clasificar_por_extension", organizer.clasificar_por_extension),
    "2": ("clasificar_por_tamano", organizer.clasificar_por_tamano),
    "3": ("clasificar_por_fecha", organizer.clasificar_por_fecha),
}


def menu_organizador():
    # Menu principal del gestor de organizacion. Aqui se decide si el usuario
    # quiere clasificar archivos, renombrarlos o deshacer la ultima accion.
    imprimir_titulo("Gestor de Organizacion de Archivos")
    print("1) Clasificar por extension")
    print("2) Clasificar por tamano")
    print("3) Clasificar por fecha de modificacion")
    print("4) Renombrar archivos con patron (regex)")
    print("5) Deshacer la ultima operacion realizada")
    print("0) Volver al menu principal")
    opcion = pedir_opcion("Seleccione una opcion: ", {"0", "1", "2", "3", "4", "5"})

    if opcion == "0":
        return
    if opcion == "5":
        _deshacer_ultima_operacion()
        return

    carpeta = pedir_ruta_valida("Ruta de la carpeta a organizar: ")

    try:
        if opcion in FUNCIONES_CLASIFICACION:
            _clasificar_con_confirmacion(carpeta, opcion)
        elif opcion == "4":
            _renombrar_con_confirmacion(carpeta)

    except (FileNotFoundError, NotADirectoryError, ValueError, IOError) as e:
        print_error(str(e))
        reproducir_sonido("error")


def _clasificar_con_confirmacion(carpeta, opcion):
    """
    Siempre corre primero una vista previa (dry-run) para que el usuario vea
    que va a pasar ANTES de tocar un solo archivo. Solo si confirma, se
    aplica de verdad. Esto es una capa extra de seguridad sobre el dry-run.
    """
    # Se ejecuta primero la operacion en modo de prueba para mostrar el efecto
    # esperado sin modificar archivos reales.
    nombre_funcion, funcion = FUNCIONES_CLASIFICACION[opcion]
    preview = funcion(carpeta, dry_run=True)

    print_info("Vista previa (nada se ha movido todavia):")
    for categoria, archivos in preview.items():
        print(f"  - {categoria}: {len(archivos)} archivo(s)")

    if not any(preview.values()):
        print_warn("No hay archivos para organizar con este criterio.")
        return

    if pedir_opcion("Aplicar estos cambios de verdad? (s/n): ", {"s", "n"}) != "s":
        print_info("No se aplico ningun cambio. (Puedes repetir en modo simulacion cuando quieras.)")
        return

    resultado = funcion(carpeta, dry_run=False)
    print_ok("Cambios aplicados correctamente.")
    print_info("Si algo salio mal, usa la opcion 5 (Deshacer) del menu de organizacion.")
    reproducir_sonido("ok")

    if pedir_opcion("Generar reporte de esta operacion? (s/n): ", {"s", "n"}) == "s":
        reports.reporte_organizacion(resultado)
        print_ok("Reporte generado en la carpeta 'reportes/'.")
        _ofrecer_grafico({k: len(v) for k, v in resultado.items()}, "grafico_organizacion",
                           "Archivos por categoria")


def _renombrar_con_confirmacion(carpeta):
    # El usuario ingresa un patron regex y el texto de reemplazo para cambiar
    # los nombres de archivo de forma controlada.
    patron = input("Patron regex a buscar en los nombres de archivo: ")
    reemplazo = input("Texto de reemplazo: ")

    preview = organizer.renombrar_con_patron(carpeta, patron, reemplazo, dry_run=True)
    if not preview:
        print_warn("Ningun archivo coincide con ese patron.")
        return

    print_info("Vista previa de renombrado (nada se ha aplicado todavia):")
    for viejo, nuevo in preview:
        print(f"  - {viejo}  ->  {nuevo}")

    if pedir_opcion("Aplicar estos cambios de verdad? (s/n): ", {"s", "n"}) != "s":
        print_info("No se aplico ningun cambio.")
        return

    resultado = organizer.renombrar_con_patron(carpeta, patron, reemplazo, dry_run=False)
    print_ok("Archivos renombrados correctamente.")
    print_info("Si algo salio mal, usa la opcion 5 (Deshacer) del menu de organizacion.")
    reproducir_sonido("ok")

    if pedir_opcion("Generar reporte de esta operacion? (s/n): ", {"s", "n"}) == "s":
        reports.generar_reporte_txt(resultado, "reporte_renombrado", "Reporte de Renombrado de Archivos")
        print_ok("Reporte generado en la carpeta 'reportes/'.")


def _deshacer_ultima_operacion():
    try:
        resumen = undo.deshacer_ultima_operacion()
        print_ok(f"Se deshizo la operacion: {resumen['operacion_deshecha']} "
                  f"(realizada el {resumen['fecha_original']})")
        for linea in resumen["exitos"]:
            print(f"  {Color.OK}<-{Color.RESET} {linea}")
        for linea in resumen["errores"]:
            print_warn(linea)
        reproducir_sonido("ok")
    except (LookupError, IOError) as e:
        print_error(str(e))
        reproducir_sonido("error")


def _ofrecer_grafico(datos, nombre_base, titulo):
    """Pregunta si se desea generar un grafico de barras visual (extra)."""
    if pedir_opcion("Generar tambien un grafico visual (.png)? (s/n): ", {"s", "n"}) == "s":
        reports.generar_grafico_barras(datos, nombre_base, titulo)


def menu_analizador():
    # Menu del analizador: permite buscar patrones, obtener resumentes o
    # identificar archivos duplicados dentro de una carpeta.
    imprimir_titulo("Analizador de Contenido")
    carpeta = pedir_ruta_valida("Ruta de la carpeta a analizar: ")
    print("\n1) Buscar correos electronicos")
    print("2) Buscar numeros de telefono")
    print("3) Buscar fechas")
    print("4) Resumen general de la carpeta")
    print("5) Buscar archivos duplicados")
    print("0) Volver al menu principal")
    opcion = pedir_opcion("Seleccione una opcion: ", {"0", "1", "2", "3", "4", "5"})

    if opcion == "0":
        return

    try:
        if opcion in {"1", "2", "3"}:
            _buscar_patron(carpeta, opcion)
        elif opcion == "4":
            _mostrar_resumen_general(carpeta)
        elif opcion == "5":
            _buscar_duplicados(carpeta)

    except (FileNotFoundError, KeyError, ValueError, IOError) as e:
        print_error(str(e))
        reproducir_sonido("error")


def _buscar_patron(carpeta, opcion):
    # Traduce la opcion elegida por el usuario a un tipo de analisis concreto.
    mapa_tipos = {"1": "correos", "2": "telefonos", "3": "fechas"}
    resultado = analyzer.analizar_carpeta(carpeta, mapa_tipos[opcion])
    print_info(f"Coincidencias unicas encontradas: {len(resultado['coincidencias_unicas'])}")
    for archivo, cantidad in resultado["resumen_por_archivo"].items():
        print(f"  - {archivo}: {cantidad} coincidencia(s)")
    reproducir_sonido("ok")

    if pedir_opcion("Generar reporte de este analisis? (s/n): ", {"s", "n"}) == "s":
        reports.reporte_analisis(resultado)
        print_ok("Reporte generado en la carpeta 'reportes/'.")
        _ofrecer_grafico(resultado["resumen_por_archivo"], "grafico_analisis",
                           f"Coincidencias de {mapa_tipos[opcion]} por archivo")


def _mostrar_resumen_general(carpeta):
    resumen = analyzer.generar_resumen_general(carpeta)
    if resumen["total_archivos"] == 0:
        print_warn("La carpeta no tiene archivos.")
        return

    imprimir_titulo("Resumen general de la carpeta")
    print_info(f"Total de archivos: {resumen['total_archivos']}")
    print_info(f"Espacio total ocupado: {resumen['tamano_total_legible']}")
    print_info(f"Archivo mas grande: {resumen['mas_grande']['nombre']} ({resumen['mas_grande']['tamano']})")
    print_info(f"Archivo mas reciente: {resumen['mas_reciente']['nombre']} ({resumen['mas_reciente']['fecha']})")
    print_info(f"Archivo mas antiguo: {resumen['mas_antiguo']['nombre']} ({resumen['mas_antiguo']['fecha']})")
    print(f"\n{Color.BOLD}Archivos por extension:{Color.RESET}")
    for ext, cantidad in sorted(resumen["por_extension"].items(), key=lambda x: -x[1]):
        print(f"  - {ext}: {cantidad}")
    reproducir_sonido("ok")

    if pedir_opcion("Generar reporte de este resumen? (s/n): ", {"s", "n"}) == "s":
        reports.generar_reporte_txt(resumen, "reporte_resumen_general", "Resumen General de la Carpeta")
        print_ok("Reporte generado en la carpeta 'reportes/'.")
        conteo = {ext: cant for ext, cant in resumen["por_extension"].items()}
        _ofrecer_grafico(conteo, "grafico_resumen", "Archivos por extension")


def _buscar_duplicados(carpeta):
    duplicados = analyzer.buscar_duplicados(carpeta)
    if not duplicados:
        print_ok("No se encontraron archivos duplicados.")
        reproducir_sonido("ok")
        return

    print_warn(f"Se encontraron {len(duplicados)} grupo(s) de archivos duplicados:")
    for hash_archivo, nombres in duplicados.items():
        print(f"\n  {Color.MAGENTA}Hash {hash_archivo[:10]}...{Color.RESET}")
        for nombre in nombres:
            print(f"    - {nombre}")
    reproducir_sonido("aviso")
    print_info("Revisa la lista y borra manualmente los que no necesites; "
                "el sistema no elimina archivos de duplicados automaticamente.")

    if pedir_opcion("Generar reporte de duplicados? (s/n): ", {"s", "n"}) == "s":
        texto = {f"Grupo {i+1} ({h[:10]}...)": ", ".join(n) for i, (h, n) in enumerate(duplicados.items())}
        reports.generar_reporte_txt(texto, "reporte_duplicados", "Archivos Duplicados Encontrados")
        print_ok("Reporte generado en la carpeta 'reportes/'.")


def menu_auditor():
    # Menu del auditor: permite crear snapshots manuales y comparar una carpeta
    # con el ultimo estado guardado para detectar cambios.
    imprimir_titulo("Auditor de Cambios")
    carpeta = pedir_ruta_valida("Ruta de la carpeta a auditar: ")
    print("\n1) Crear snapshot manual")
    print("2) Auditar carpeta, compara con el ultimo snapshot")
    print("0) Volver al menu principal")
    opcion = pedir_opcion("Seleccione una opcion: ", {"0", "1", "2"})

    if opcion == "0":
        return

    try:
        if opcion == "1":
            ruta = auditor.crear_snapshot(carpeta)
            print_ok(f"Snapshot creado en: {ruta}")
            reproducir_sonido("ok")
        elif opcion == "2":
            diferencias = auditor.auditar_carpeta(carpeta)
            print_info(f"Archivos nuevos: {len(diferencias['nuevos'])}")
            print_info(f"Archivos modificados: {len(diferencias['modificados'])}")
            print_info(f"Archivos eliminados: {len(diferencias['eliminados'])}")
            reproducir_sonido("ok")

            if pedir_opcion("Generar reporte de auditoria? (s/n): ", {"s", "n"}) == "s":
                reports.reporte_auditoria(diferencias)
                print_ok("Reporte generado en la carpeta 'reportes/'.")
                conteo = {k: len(v) for k, v in diferencias.items()}
                _ofrecer_grafico(conteo, "grafico_auditoria", "Cambios detectados por tipo")

    except (FileNotFoundError, IOError) as e:
        print_error(str(e))
        reproducir_sonido("error")


def mostrar_menu_principal():
    # Presenta la pantalla inicial del programa con las tres areas principales
    # disponibles para el usuario.
    print(f"\n{Color.BOLD}=== KIT MULTIFUNCIONAL DE AUTOMATIZACION DE ARCHIVOS ==={Color.RESET}")
    print("1) Gestor de Organizacion de Archivos")
    print("2) Analizador de Contenido")
    print("3) Auditor de Cambios")
    print("4) Salir")


def main():
    # Inicio del programa: se muestra el banner, se valida el acceso de
    # escritura y luego se mantiene el menu principal en ciclo.
    mostrar_banner()
    verificar_permisos_escritura()
    while True:
        mostrar_menu_principal()
        opcion = pedir_opcion("Seleccione una opcion: ", {"1", "2", "3", "4"})

        if opcion == "1":
            menu_organizador()
        elif opcion == "2":
            menu_analizador()
        elif opcion == "3":
            menu_auditor()
        elif opcion == "4":
            print_ok("Saliendo del sistema. Hasta luego.")
            reproducir_sonido("aviso")
            sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_error("Programa interrumpido por el usuario.")
        sys.exit(1)
