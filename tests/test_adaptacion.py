"""Pruebas de la adaptación católica, con frases tomadas del texto real."""

import unittest

from evangelio.adaptacion import adaptar


def a(libro, cap, ver, texto):
    return adaptar(libro, cap, ver, texto)[0]


class NombreDeDios(unittest.TestCase):
    def test_sujeto_al_abrir_frase(self):
        self.assertEqual(
            a("PSA", 23, 1, "Yahvé es mi pastor; nada me faltará."),
            "El Señor es mi pastor; nada me faltará.",
        )

    def test_sujeto_en_mitad_de_frase(self):
        self.assertEqual(
            a("PSA", 95, 3, "Porque Yahvé es Dios grande, y Rey grande sobre todos los dioses."),
            "Porque el Señor es Dios grande, y Rey grande sobre todos los dioses.",
        )

    def test_preposiciones(self):
        self.assertEqual(
            a("PSA", 95, 1, "¡ Venid, aclamemos alegremente a Yahvé!"),
            "¡ Venid, aclamemos alegremente al Señor!",
        )
        self.assertEqual(a("ISA", 1, 10, "Oíd la palabra de Yahvé."), "Oíd la palabra del Señor.")
        self.assertEqual(a("PSA", 1, 2, "se deleita en Yahvé"), "se deleita en el Señor")

    def test_yahve_dios(self):
        self.assertEqual(
            a("GEN", 2, 4, "el día en que Yahvé Dios hizo la tierra y los cielos."),
            "el día en que el Señor Dios hizo la tierra y los cielos.",
        )

    def test_senor_yahve(self):
        self.assertEqual(
            a("GEN", 15, 2, "Y respondió Abram: “Señor Yahvé, ¿ qué me darás?”"),
            "Y respondió Abram: “Señor Dios, ¿ qué me darás?”",
        )

    def test_vocativo_con_oh(self):
        self.assertEqual(
            a("GEN", 24, 12, "Y dijo: “Oh Yahvé, Dios de mi señor Abraham, dame buen encuentro.”"),
            "Y dijo: “Oh Señor, Dios de mi señor Abraham, dame buen encuentro.”",
        )

    def test_vocativo_entre_comas(self):
        self.assertEqual(
            a("PSA", 27, 7, "Escucha, Yahvé, cuando clamo con mi voz."),
            "Escucha, Señor, cuando clamo con mi voz.",
        )

    def test_vocativo_al_abrir_frase(self):
        self.assertEqual(
            a("PSA", 15, 1, "Yahvé, ¿quién habitará en tu santuario?"),
            "Señor, ¿quién habitará en tu santuario?",
        )

    def test_aposicion_no_es_vocativo(self):
        self.assertEqual(
            a("EXO", 3, 15, "«Dirás esto: Yahvé, el Dios de vuestros padres, me ha enviado.»"),
            "«Dirás esto: El Señor, el Dios de vuestros padres, me ha enviado.»",
        )
        self.assertEqual(
            a("DEU", 6, 5, "Amarás a Yahvé, tu Dios, con todo tu corazón."),
            "Amarás al Señor, tu Dios, con todo tu corazón.",
        )

    def test_aposicion_al_pronombre(self):
        self.assertEqual(
            a("LEV", 21, 8, "Será santo para ti, porque yo, Yahvé, que os santifico, soy santo."),
            "Será santo para ti, porque yo, el Señor, que os santifico, soy santo.",
        )
        self.assertEqual(a("ISA", 27, 3, "Yo, Yahvé, soy su guardián;"), "Yo, el Señor, soy su guardián;")

    def test_sujeto_con_inciso_no_es_vocativo(self):
        self.assertEqual(
            a("1KI", 5, 12, "Yahvé, pues, dio a Salomón sabiduría, como le había prometido;"),
            "El Señor, pues, dio a Salomón sabiduría, como le había prometido;",
        )
        self.assertEqual(
            a("PSA", 146, 6, "Yahvé, que hizo los cielos y la tierra, te bendiga."),
            "El Señor, que hizo los cielos y la tierra, te bendiga.",
        )

    def test_vocativos_reales(self):
        self.assertEqual(a("DEU", 33, 11, "Yahvé, bendice sus habilidades."), "Señor, bendice sus habilidades.")
        self.assertEqual(a("PSA", 3, 3, "Pero tú, Yahvé, eres escudo en torno a mí,"), "Pero tú, Señor, eres escudo en torno a mí,")
        self.assertEqual(a("PSA", 139, 1, "Yahvé, tú me has examinado y me conoces."), "Señor, tú me has examinado y me conoces.")

    def test_yah_yahve_es_una_sola_mencion(self):
        self.assertEqual(
            a("ISA", 12, 2, "porque Yah, Yahvé, es mi fortaleza y mi cántico;"),
            "porque el Señor es mi fortaleza y mi cántico;",
        )
        self.assertEqual(
            a("ISA", 26, 4, "porque en Yah, Yahvé, está la Roca de los siglos."),
            "porque en el Señor está la Roca de los siglos.",
        )

    def test_de_los_ejercitos(self):
        self.assertEqual(
            a("ISA", 25, 6, "Y Yahvé de los Ejércitos hará en este monte un banquete."),
            "Y el Señor de los ejércitos hará en este monte un banquete.",
        )

    def test_yah_y_jehova(self):
        self.assertEqual(a("EXO", 15, 2, "Yah es mi fuerza y mi cántico."), "El Señor es mi fuerza y mi cántico.")
        self.assertEqual(a("EZK", 9, 3, "la gloria de Jehová se elevó"), "la gloria del Señor se elevó")

    def test_no_queda_ningun_yahve(self):
        frases = [
            "Yahvé dijo a Moisés: Yo soy Yahvé.",
            "Bendito sea Yahvé, porque Yahvé es bueno; alabad a Yahvé.",
            "¡Yahvé reina! Tiemblen los pueblos ante Yahvé.",
        ]
        for f in frases:
            self.assertNotRegex(a("PSA", 1, 1, f), r"Yahv|Jehov|\bYah\b")


class Pasajes(unittest.TestCase):
    def test_llena_de_gracia(self):
        self.assertEqual(
            a("LUK", 1, 28, "«¡Alégrate, muy favorecida! El Señor está contigo.»"),
            "«¡Alégrate, llena de gracia! El Señor está contigo.»",
        )

    def test_bienaventuranzas(self):
        self.assertEqual(
            a("MAT", 5, 3, "“Benditos sean los pobres de espíritu, porque de ellos es el Reino de los Cielos."),
            "“Bienaventurados los pobres de espíritu, porque de ellos es el Reino de los Cielos.",
        )
        self.assertEqual(
            a("MAT", 5, 6, "Dichosos los que tienen hambre y sed de justicia."),
            "Bienaventurados los que tienen hambre y sed de justicia.",
        )
        # Fuera de las bienaventuranzas no se toca
        self.assertEqual(a("MAT", 13, 16, "Dichosos vuestros ojos."), "Dichosos vuestros ojos.")

    def test_convertios(self):
        self.assertEqual(
            a("MRK", 1, 15, "« ¡ El Reino de Dios está cerca! Arrepentíos y creed en la Buena Nueva»."),
            "« ¡ El Reino de Dios está cerca! Convertíos y creed en el Evangelio».",
        )
        self.assertEqual(a("ACT", 2, 38, "Arrepentíos y bautizaos."), "Arrepentíos y bautizaos.")

    def test_padre_nuestro(self):
        self.assertEqual(
            a("MAT", 6, 13, "Y no nos metas en tentación, mas líbranos del mal. Porque tuyo es el Reino, "
                             "el poder y la gloria por todos los siglos. Amén.”"),
            "Y no nos dejes caer en la tentación, mas líbranos del mal.”",
        )

    def test_gloria(self):
        self.assertEqual(
            a("LUK", 2, 14, "« Gloria a Dios en las alturas, en la tierra la paz, la buena voluntad hacia los hombres»."),
            "« Gloria a Dios en las alturas, en la tierra paz a los hombres de buena voluntad».",
        )

    def test_infierno_y_abismo(self):
        self.assertEqual(
            a("MAT", 16, 18, "edificaré mi iglesia; y las puertas del Hades no prevalecerán contra ella."),
            "edificaré mi iglesia; y las puertas del infierno no prevalecerán contra ella.",
        )
        self.assertEqual(a("MAT", 11, 23, "descenderás al Hades."), "descenderás al abismo.")
        self.assertEqual(a("PSA", 16, 10, "no dejarás mi alma en el Seol"), "no dejarás mi alma en el abismo")

    def test_caliz(self):
        self.assertEqual(
            a("MAT", 26, 27, "Tomó la copa, dio gracias y se la dio a ellos, diciendo: « Bebed todos de ella,"),
            "Tomó el cáliz, dio gracias y se lo dio a ellos, diciendo: « Bebed todos de él,",
        )
        self.assertEqual(
            a("MAT", 26, 39, "« Padre mío, si es posible, haz que pase de mí esta copa;"),
            "« Padre mío, si es posible, haz que pase de mí este cáliz;",
        )
        self.assertEqual(
            a("LUK", 22, 20, "tomó la copa, diciendo: « Esta copa es el nuevo pacto en mi sangre,"),
            "tomó el cáliz, diciendo: « Este cáliz es la nueva alianza en mi sangre,",
        )
        self.assertEqual(
            a("MAT", 26, 42, "si esta copa no puede pasar de mí sin que yo la beba, hágase tu voluntad"),
            "si este cáliz no puede pasar de mí sin que yo lo beba, hágase tu voluntad",
        )
        self.assertEqual(
            a("1CO", 11, 28, "y así coma del pan y beba de la copa."), "y así coma del pan y beba del cáliz."
        )
        # Una copa cualquiera no cambia
        self.assertEqual(a("MAT", 10, 42, "una copa de agua fría"), "una copa de agua fría")

    def test_presbiteros(self):
        self.assertEqual(
            a("JAS", 5, 14, "Que llame a los ancianos de la iglesia, y que oren por él,"),
            "Que llame a los presbíteros de la iglesia, y que oren por él,",
        )
        self.assertEqual(
            a("MAT", 15, 2, "la tradición de los ancianos"), "la tradición de los ancianos"
        )

    def test_paraclito(self):
        self.assertEqual(
            a("JHN", 14, 16, "Yo rogaré al Padre, y él os dará otro Consejero,"),
            "Yo rogaré al Padre, y él os dará otro Paráclito,",
        )

    def test_nombres(self):
        self.assertEqual(a("LUK", 8, 51, "a Pedro, a Jacobo, a Juan"), "a Pedro, a Santiago, a Juan")
        self.assertEqual(a("LUK", 1, 5, "su mujer se llamaba Elisabet"), "su mujer se llamaba Isabel")
        self.assertEqual(a("GEN", 25, 26, "y fue llamado Jacob"), "y fue llamado Jacob")


class Registro(unittest.TestCase):
    def test_registra_los_cambios(self):
        texto, cambios = adaptar("PSA", 23, 1, "Yahvé es mi pastor.")
        self.assertEqual(len(cambios), 1)
        self.assertEqual(cambios[0].antes, "Yahvé es mi pastor.")
        self.assertEqual(cambios[0].despues, texto)

    def test_sin_cambios(self):
        texto, cambios = adaptar("JHN", 1, 1, "En el principio era el Verbo.")
        self.assertEqual(texto, "En el principio era el Verbo.")
        self.assertEqual(cambios, [])


if __name__ == "__main__":
    unittest.main()
