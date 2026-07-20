"""Pruebas unitarias para analyzer.py (Analizador de Contenido)."""
import os
import tempfile
import unittest

import analyzer


class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        self._cwd_original = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        os.chdir(self._tmp.name)

        self.carpeta = os.path.join(self._tmp.name, "datos")
        os.makedirs(self.carpeta)

    def tearDown(self):
        os.chdir(self._cwd_original)
        self._tmp.cleanup()

    def _crear_archivo(self, nombre, contenido):
        ruta = os.path.join(self.carpeta, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        return ruta

    def test_buscar_patron_en_archivo_encuentra_correos(self):
        ruta = self._crear_archivo("contactos.txt", "Contacto: ana@correo.com\nOtro: no es email\n")
        coincidencias = analyzer.buscar_patron_en_archivo(ruta, analyzer.PATRONES["correos"])
        self.assertEqual(len(coincidencias), 1)
        self.assertEqual(coincidencias[0][1], "ana@correo.com")

    def test_analizar_carpeta_correos_cuenta_por_archivo(self):
        self._crear_archivo("a.txt", "correo1@x.com y correo2@x.com")
        self._crear_archivo("b.txt", "sin coincidencias aqui")
        resultado = analyzer.analizar_carpeta(self.carpeta, "correos")
        self.assertEqual(resultado["resumen_por_archivo"]["a.txt"], 2)
        self.assertEqual(resultado["resumen_por_archivo"]["b.txt"], 0)
        self.assertEqual(len(resultado["coincidencias_unicas"]), 2)

    def test_analizar_carpeta_tipo_invalido_lanza_keyerror(self):
        with self.assertRaises(KeyError):
            analyzer.analizar_carpeta(self.carpeta, "no_existe")

    def test_generar_resumen_general(self):
        self._crear_archivo("uno.txt", "a" * 100)
        self._crear_archivo("dos.txt", "b" * 50)
        resumen = analyzer.generar_resumen_general(self.carpeta)
        self.assertEqual(resumen["total_archivos"], 2)
        self.assertEqual(resumen["tamano_total"], 150)
        self.assertEqual(resumen["mas_grande"]["nombre"], "uno.txt")

    def test_generar_resumen_general_carpeta_vacia(self):
        vacia = os.path.join(self._tmp.name, "vacia")
        os.makedirs(vacia)
        resumen = analyzer.generar_resumen_general(vacia)
        self.assertEqual(resumen["total_archivos"], 0)

    def test_buscar_duplicados_agrupa_contenido_identico(self):
        self._crear_archivo("original.txt", "mismo contenido exacto")
        self._crear_archivo("copia.txt", "mismo contenido exacto")
        self._crear_archivo("distinto.txt", "contenido diferente")
        duplicados = analyzer.buscar_duplicados(self.carpeta)
        self.assertEqual(len(duplicados), 1)
        grupo = list(duplicados.values())[0]
        self.assertEqual(sorted(grupo), ["copia.txt", "original.txt"])

    def test_buscar_duplicados_sin_duplicados_retorna_vacio(self):
        self._crear_archivo("a.txt", "contenido A")
        self._crear_archivo("b.txt", "contenido B")
        duplicados = analyzer.buscar_duplicados(self.carpeta)
        self.assertEqual(duplicados, {})


if __name__ == "__main__":
    unittest.main()
