"""Pruebas del localizador por texto guía, con una Biblia inventada."""

import unittest

from evangelio.alineacion import fichas, localizar, parecido, versiculos_del_salmo
from evangelio.biblia import Biblia

# Un libro cuya numeración va un versículo por delante de la que usa la cita,
# como ocurre en Isaías 9.
ISAIAS = {
    8: {1: "Toma una tabla grande y escribe en ella.", 2: "Llamé a dos testigos fieles."},
    9: {
        1: "No habrá siempre oscuridad para la tierra angustiada.",
        2: "El pueblo que andaba en tinieblas vio una gran luz.",
        3: "Aumentaste la alegría y multiplicaste el gozo de la nación.",
        4: "Quebraste el yugo pesado y la vara del opresor.",
        5: "Toda bota de guerrero será quemada como pasto del fuego.",
        6: "Porque un niño nos ha nacido y un hijo se nos ha dado.",
        7: "Su reino tendrá paz sin fin sobre el trono de David.",
    },
}

# Un salmo «23» de seis versículos; en la liturgia es el 22.
SALMOS = {
    23: {
        1: "El pastor me guía y nada me falta.",
        2: "En prados verdes me hace descansar; junto a aguas tranquilas me conduce.",
        3: "Restaura mis fuerzas; me lleva por sendas rectas.",
        4: "Aunque cruce el valle oscuro, no temeré ningún mal.",
        5: "Preparas un banquete delante de mis enemigos; unges mi cabeza con aceite.",
        6: "Tu bondad me acompañará siempre; viviré en tu casa por largos días.",
    }
}


def biblia() -> Biblia:
    return Biblia({"ISA": ISAIAS, "PSA": SALMOS})


class Fichas(unittest.TestCase):
    def test_ignora_palabras_vacias_y_acentos(self):
        self.assertEqual(fichas("El niño y la niña de él"), {"nino", "nina"})

    def test_parecido(self):
        self.assertEqual(parecido({"a", "b"}, {"a", "b"}), 1.0)
        self.assertEqual(parecido({"a"}, {"b"}), 0.0)
        self.assertEqual(parecido(set(), {"b"}), 0.0)


class Localizar(unittest.TestCase):
    def test_numeracion_igual(self):
        guia = "Coge una tabla grande y escribe sobre ella. Llamé a dos testigos fieles."
        r = localizar(biblia(), "Is 8,1-2", guia)
        self.assertEqual(r.desplazamiento, 0)
        self.assertEqual([(v.capitulo, v.numero) for v in r.versiculos], [(8, 1), (8, 2)])
        self.assertTrue(r.fiable)

    def test_numeracion_desplazada(self):
        guia = (
            "El pueblo que caminaba en tinieblas vio una luz grande. Acreciste la alegría, "
            "aumentaste el gozo. Quebraste el yugo y la vara del opresor. Toda bota de guerrero "
            "será pasto del fuego. Un niño nos ha nacido, un hijo se nos ha dado."
        )
        r = localizar(biblia(), "Is 9,1-5", guia)
        self.assertEqual(r.desplazamiento, 1)
        self.assertEqual([(v.capitulo, v.numero) for v in r.versiculos], [(9, n) for n in range(2, 7)])
        self.assertGreater(r.similitud, r.similitud_sin_mover)

    def test_versiculo_que_aqui_cae_en_el_capitulo_siguiente(self):
        # La cita dice 8,3, que aquí no existe: es el 9,1.
        guia = "No habrá siempre oscuridad para la tierra que estaba angustiada."
        r = localizar(biblia(), "Is 8,3", guia)
        self.assertEqual([(v.capitulo, v.numero) for v in r.versiculos], [(9, 1)])

    def test_guia_que_no_corresponde(self):
        r = localizar(biblia(), "Is 8,1-2", "Un texto que habla de barcas, redes y peces en el lago.")
        self.assertFalse(r.fiable)


class Salmo(unittest.TestCase):
    def test_salmo_entero_con_estribillo(self):
        guia = (
            "Viviré en tu casa por largos días. "  # estribillo, repetido del final
            "El pastor me guía, nada me falta. En verdes praderas me hace reposar; me lleva a fuentes "
            "tranquilas. Repara mis fuerzas; me guía por el sendero justo. Aunque camine por cañadas "
            "oscuras, nada temo. Preparas una mesa ante mis enemigos; me unges la cabeza con perfume. "
            "Tu bondad me acompaña siempre; habitaré en tu casa por días sin término."
        )
        r = versiculos_del_salmo(biblia(), 22, guia)
        self.assertEqual([v.numero for v in r.versiculos], [1, 2, 3, 4, 5, 6])
        self.assertEqual(r.versiculos[0].capitulo, 23)

    def test_solo_algunas_estrofas(self):
        guia = (
            "El pastor me guía, nada me falta. Preparas una mesa ante mis enemigos; "
            "me unges la cabeza con aceite. Tu bondad me acompaña siempre; habitaré en tu casa."
        )
        r = versiculos_del_salmo(biblia(), 22, guia)
        self.assertEqual([v.numero for v in r.versiculos], [1, 5, 6])

    def test_guia_vacia(self):
        self.assertEqual(versiculos_del_salmo(biblia(), 22, "").versiculos, ())


if __name__ == "__main__":
    unittest.main()
