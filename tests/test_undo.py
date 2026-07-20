"""Pruebas unitarias para undo.py (Sistema de Deshacer)."""
import os
import tempfile
import unittest

import organizer
import undo


class TestUndo(unittest.TestCase):
    def setUp(self):
        self._cwd_original = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

        self.carpeta = os.path.join(self._tmp.name, "datos")
        os.makedirs(self.carpeta)
        self._crear_archivo("foto.jpg")
        self._crear_archivo("documento.txt")

    def tearDown(self):
        os.chdir(self._cwd_original)
        self._tmp.cleanup()

    def _crear_archivo(self, nombre, contenido="x"):
        ruta = os.path.join(self.carpeta, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        return ruta

    def test_deshacer_sin_historial_lanza_lookuperror(self):
        with self.assertRaises(LookupError):
            undo.deshacer_ultima_operacion()

    def test_deshacer_revierte_clasificacion_por_extension(self):
        # Se organiza de verdad (dry_run=False), lo que deberia registrar la
        # operacion automaticamente en el historial.
        organizer.clasificar_por_extension(self.carpeta, dry_run=False)
        self.assertTrue(os.path.exists(os.path.join(self.carpeta, "JPG", "foto.jpg")))

        resumen = undo.deshacer_ultima_operacion()
        self.assertEqual(resumen["operacion_deshecha"], "clasificar_por_extension")
        self.assertEqual(resumen["errores"], [])

        # Los archivos deben haber vuelto a su ubicacion original...
        self.assertTrue(os.path.exists(os.path.join(self.carpeta, "foto.jpg")))
        self.assertTrue(os.path.exists(os.path.join(self.carpeta, "documento.txt")))
        # ...y las carpetas vacias que quedaron deben haberse eliminado.
        self.assertFalse(os.path.isdir(os.path.join(self.carpeta, "JPG")))

    def test_deshacer_revierte_renombrado(self):
        organizer.renombrar_con_patron(self.carpeta, r"^documento", "DOC_", dry_run=False)
        self.assertTrue(os.path.exists(os.path.join(self.carpeta, "DOC_.txt")))

        undo.deshacer_ultima_operacion()
        self.assertTrue(os.path.exists(os.path.join(self.carpeta, "documento.txt")))
        self.assertFalse(os.path.exists(os.path.join(self.carpeta, "DOC_.txt")))

    def test_dry_run_no_registra_operacion(self):
        # En modo simulacion no debe quedar nada que deshacer.
        organizer.clasificar_por_extension(self.carpeta, dry_run=True)
        with self.assertRaises(LookupError):
            undo.deshacer_ultima_operacion()

    def test_deshacer_dos_veces_solo_revierte_la_ultima(self):
        organizer.clasificar_por_extension(self.carpeta, dry_run=False)
        undo.deshacer_ultima_operacion()
        # Ya no debe quedar nada en el historial para deshacer de nuevo.
        with self.assertRaises(LookupError):
            undo.deshacer_ultima_operacion()


if __name__ == "__main__":
    unittest.main()


