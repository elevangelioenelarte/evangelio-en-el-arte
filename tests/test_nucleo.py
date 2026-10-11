import unittest

from evangelio import fidelidad, usfm
from evangelio.biblia import Biblia, TextoNoEncontrado
from evangelio.citas import CitaInvalida, Tramo, analizar
from evangelio.salmos import SalmoHebreo, liturgico_a_hebreo

USFM_FILIPENSES = r"""\id PHP - Biblia de prueba
\h Filipenses
\mt1 Carta a los Filipenses
\c 4
\s1 Agradecimiento
\p
\v 12 Sé vivir \w humildemente|strong="G5013"\w* y sé tener abundancia.\f + \fr 4:12 \ft Nota al pie.\f*
\v 13 Todo lo puedo en \add Cristo\add* que me fortalece.
\p
\v 14 Sin embargo, hicieron bien. \v 15 Y ustedes lo saben.
\v 16-17 Versículos unidos en uno solo.
\v 18 He recibido todo.
\q1
\v 19 Mi Dios suplirá
\q2 todo lo que les falta.\x - \xo 4:19 \xt Sal 23:1\x*
\v 20 Gloria a Dios. Amén.
"""

USFM_SALMOS = r"""\id PSA
\c 22
\d Salmo de David.
\v 1 Dios mío, Dios mío.
\c 23
\d Salmo de David.
\q1
\v 1 El Señor es mi pastor;
\q2 nada me faltará.
\v 2 En lugares de verdes pastos me hace descansar.
\c 116
\v 1 Amo al Señor.
\v 9 Caminaré delante del Señor.
\v 10 Creí, por eso hablé.
"""


def biblia_de_prueba() -> Biblia:
    libros = {}
    for texto in (USFM_FILIPENSES, USFM_SALMOS):
        codigo, capitulos = usfm.leer_libro(texto)
        libros[codigo] = capitulos
    return Biblia(libros)


class Citas(unittest.TestCase):
    def test_tramo_simple(self):
        c = analizar("Mt 22,1-14")
        self.assertEqual(c.libro, "MAT")
        self.assertEqual(c.tramos, (Tramo(22, 1, 22, 14),))

    def test_saltos_en_el_mismo_capitulo(self):
        c = analizar("Flp 4,12-14.19-20")
        self.assertEqual(c.libro, "PHP")
        self.assertEqual(c.tramos, (Tramo(4, 12, 4, 14), Tramo(4, 19, 4, 20)))

    def test_medio_versiculo(self):
        c = analizar("Is 25,6-10a")
        self.assertEqual(c.tramos, (Tramo(25, 6, 25, 10, parcial=True),))
        self.assertTrue(c.tiene_parciales)

    def test_versiculo_suelto_y_tramo(self):
        c = analizar("Hch 2,14.22-33")
        self.assertEqual(c.libro, "ACT")
        self.assertEqual(c.tramos, (Tramo(2, 14, 2, 14), Tramo(2, 22, 2, 33)))

    def test_cruza_capitulos(self):
        for texto in ("Jn 18,1-19,42", "Jn 18,1—19,42", "Jn 18, 1 – 19, 42"):
            self.assertEqual(analizar(texto).tramos, (Tramo(18, 1, 19, 42),), texto)

    def test_varios_capitulos(self):
        c = analizar("Gn 2,7-9; 3,1-7")
        self.assertEqual(c.tramos, (Tramo(2, 7, 2, 9), Tramo(3, 1, 3, 7)))

    def test_libro_numerado(self):
        for texto in ("1Cor 12,3b-7.12-13", "1 Co 12,3b-7.12-13"):
            c = analizar(texto)
            self.assertEqual(c.libro, "1CO")
            self.assertEqual(c.tramos, (Tramo(12, 3, 12, 7, parcial=True), Tramo(12, 12, 12, 13)))

    def test_capitulo_entero(self):
        self.assertEqual(analizar("Sal 22").tramos, (Tramo(22, None, 22, None),))

    def test_libro_de_un_capitulo(self):
        c = analizar("Flm 7-20")
        self.assertEqual(c.libro, "PHM")
        self.assertEqual(c.tramos, (Tramo(1, 7, 1, 20),))

    def test_acentos_y_punto(self):
        self.assertEqual(analizar("Éx. 17,3-7").libro, "EXO")

    def test_errores(self):
        for texto in ("Xyz 1,1", "Mt", "Mt 5,9-3", "Mt 5,a"):
            with self.assertRaises(CitaInvalida, msg=texto):
                analizar(texto)


class Salmos(unittest.TestCase):
    def test_conversion(self):
        casos = {
            8: [SalmoHebreo(8)],
            9: [SalmoHebreo(9), SalmoHebreo(10)],
            22: [SalmoHebreo(23)],
            50: [SalmoHebreo(51)],
            112: [SalmoHebreo(113)],
            113: [SalmoHebreo(114), SalmoHebreo(115)],
            114: [SalmoHebreo(116, 1, 9)],
            115: [SalmoHebreo(116, 10, 19)],
            116: [SalmoHebreo(117)],
            145: [SalmoHebreo(146)],
            146: [SalmoHebreo(147, 1, 11)],
            147: [SalmoHebreo(147, 12, 20)],
            148: [SalmoHebreo(148)],
            150: [SalmoHebreo(150)],
        }
        for liturgico, esperado in casos.items():
            self.assertEqual(liturgico_a_hebreo(liturgico), esperado, liturgico)

    def test_fuera_de_rango(self):
        for n in (0, 151):
            with self.assertRaises(ValueError):
                liturgico_a_hebreo(n)


class Usfm(unittest.TestCase):
    def setUp(self):
        self.codigo, self.caps = usfm.leer_libro(USFM_FILIPENSES)

    def test_codigo(self):
        self.assertEqual(self.codigo, "PHP")

    def test_quita_notas_y_atributos(self):
        self.assertEqual(self.caps[4][12], "Sé vivir humildemente y sé tener abundancia.")

    def test_conserva_palabras_marcadas(self):
        self.assertEqual(self.caps[4][13], "Todo lo puedo en Cristo que me fortalece.")

    def test_dos_versiculos_en_una_linea(self):
        self.assertEqual(self.caps[4][14], "Sin embargo, hicieron bien.")
        self.assertEqual(self.caps[4][15], "Y ustedes lo saben.")

    def test_versiculos_unidos(self):
        self.assertEqual(self.caps[4][16], "Versículos unidos en uno solo.")
        self.assertEqual(self.caps[4][17], "")

    def test_poesia_y_referencias(self):
        self.assertEqual(self.caps[4][19], "Mi Dios suplirá todo lo que les falta.")

    def test_sin_titulos(self):
        todo = " ".join(self.caps[4].values())
        self.assertNotIn("Agradecimiento", todo)
        self.assertNotIn("Carta", todo)


class BibliaTexto(unittest.TestCase):
    def setUp(self):
        self.b = biblia_de_prueba()

    def test_cita_con_saltos(self):
        self.assertEqual(
            self.b.texto("Flp 4,12-14.19-20"),
            "Sé vivir humildemente y sé tener abundancia. "
            "Todo lo puedo en Cristo que me fortalece. "
            "Sin embargo, hicieron bien. "
            "Mi Dios suplirá todo lo que les falta. "
            "Gloria a Dios. Amén.",
        )

    def test_salmo_liturgico_se_convierte(self):
        texto = self.b.texto("Sal 22")
        self.assertTrue(texto.startswith("El Señor es mi pastor"))
        self.assertNotIn("Salmo de David", texto)

    def test_salmo_con_versiculos(self):
        self.assertEqual(
            self.b.texto("Sal 22,2"), "En lugares de verdes pastos me hace descansar."
        )

    def test_salmo_sin_convertir(self):
        self.assertEqual(self.b.texto("Sal 22", salmo_liturgico=False), "Dios mío, Dios mío.")

    def test_salmo_partido_con_versiculos_no_se_adivina(self):
        with self.assertRaises(TextoNoEncontrado):
            self.b.texto("Sal 115,1-3")

    def test_versiculo_inexistente(self):
        with self.assertRaises(TextoNoEncontrado):
            self.b.texto("Flp 4,21-23")
        with self.assertRaises(TextoNoEncontrado):
            self.b.texto("Mt 22,1-14")

    def test_texto_adaptado(self):
        b = Biblia({"PSA": {23: {1: "Yahvé es mi pastor; nada me faltará."}}})
        texto, cambios = b.texto_adaptado("Sal 22")
        self.assertEqual(texto, "El Señor es mi pastor; nada me faltará.")
        self.assertEqual(len(cambios), 1)

    def test_versiculos_unidos_no_duplican(self):
        self.assertEqual(self.b.texto("Flp 4,16-17"), "Versículos unidos en uno solo.")


class Fidelidad(unittest.TestCase):
    TEXTO = "El Señor es mi pastor; nada me faltará."

    def test_ignora_puntuacion_y_mayusculas(self):
        r = fidelidad.comparar(self.TEXTO, "el señor es mi pastor nada me faltará")
        self.assertTrue(r.exacto)
        self.assertEqual(r.similitud, 1.0)

    def test_detecta_palabra_cambiada(self):
        r = fidelidad.comparar(self.TEXTO, "El Señor es mi pastor; nada me faltara.")
        self.assertFalse(r.exacto)
        self.assertEqual(r.diferencias[0].tipo, "cambia")
        self.assertEqual(r.diferencias[0].esperado, "faltará")

    def test_detecta_palabra_que_falta_y_que_sobra(self):
        falta = fidelidad.comparar(self.TEXTO, "El Señor es mi pastor; nada faltará.")
        self.assertEqual([d.tipo for d in falta.diferencias], ["falta"])
        sobra = fidelidad.comparar(self.TEXTO, "El Señor Dios es mi pastor; nada me faltará.")
        self.assertEqual([d.tipo for d in sobra.diferencias], ["sobra"])

    def test_guion_y_audio(self):
        self.assertTrue(fidelidad.guion_fiel(self.TEXTO, self.TEXTO).exacto)
        self.assertFalse(fidelidad.audio_fiel(self.TEXTO, "Un texto completamente distinto."))
        self.assertTrue(fidelidad.audio_fiel(self.TEXTO, "el señor es mi pastor nada me faltará"))


if __name__ == "__main__":
    unittest.main()
