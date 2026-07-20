"""Pruebas unitarias para auditor.py (Auditor de Cambios)."""
import os
import time
import tempfile
import unittest

import auditor


class TestAuditor(unittest.TestCase):
    def setUp(self):
        self._cwd_original = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

        self.carpeta = os.path.join(self._tmp.name, "datos")
        os.makedirs(self.carpeta)

    def tearDown(self):
        os.chdir(self._cwd_original)
        self._tmp.cleanup()

    def _crear_archivo(self, nombre, contenido="contenido"):
        ruta = os.path.join(self.carpeta, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        return ruta

    def test_crear_snapshot_genera_json_con_hash(self):
        self._crear_archivo("a.txt")
        ruta_snapshot = auditor.crear_snapshot(self.carpeta)
        self.assertTrue(os.path.exists(ruta_snapshot))

        snapshot = auditor._cargar_snapshot(ruta_snapshot)
        self.assertIn("a.txt", snapshot)
        self.assertIn("hash", snapshot["a.txt"])

    def test_comparar_snapshots_detecta_nuevos_modificados_eliminados(self):
        anterior = {
            "igual.txt": {"hash": "abc"},
            "cambia.txt": {"hash": "111"},
            "se_borra.txt": {"hash": "222"},
        }
        actual = {
            "igual.txt": {"hash": "abc"},
            "cambia.txt": {"hash": "999"},
            "nuevo.txt": {"hash": "333"},
        }
        diferencias = auditor.comparar_snapshots(anterior, actual)
        self.assertEqual(diferencias["nuevos"], ["nuevo.txt"])
        self.assertEqual(diferencias["modificados"], ["cambia.txt"])
        self.assertEqual(diferencias["eliminados"], ["se_borra.txt"])

    def test_auditar_carpeta_detecta_archivo_nuevo_entre_dos_auditorias(self):
        self._crear_archivo("uno.txt")
        auditor.auditar_carpeta(self.carpeta)  # primera auditoria = linea base

        self._crear_archivo("dos.txt")
        diferencias = auditor.auditar_carpeta(self.carpeta)  # segunda auditoria

        self.assertIn("dos.txt", diferencias["nuevos"])
        self.assertEqual(diferencias["eliminados"], [])

    def test_auditar_carpeta_detecta_modificacion_de_contenido(self):
        ruta = self._crear_archivo("uno.txt", "version original")
        auditor.auditar_carpeta(self.carpeta)

        with open(ruta, "w", encoding="utf-8") as f:
            f.write("version modificada, contenido distinto")

        diferencias = auditor.auditar_carpeta(self.carpeta)
        self.assertIn("uno.txt", diferencias["modificados"])


if __name__ == "__main__":
    unittest.main()



