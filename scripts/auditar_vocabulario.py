"""Auditoría del vocabulario de la Biblia del proyecto.

Cuenta los términos que pueden sonar ajenos a un lector católico y vuelca los
versículos más conocidos, para decidir las reglas de adaptación con el texto
real delante.

Uso:
    python scripts/auditar_vocabulario.py datos/biblia.json informe.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evangelio.biblia import Biblia, TextoNoEncontrado  # noqa: E402

NT = set(
    "MAT MRK LUK JHN ACT ROM 1CO 2CO GAL EPH PHP COL 1TH 2TH 1TI 2TI TIT PHM HEB JAS "
    "1PE 2PE 1JN 2JN 3JN JUD REV".split()
)
DEUTERO = set("TOB JDT ESG WIS SIR BAR 1MA 2MA DAG 1ES 2ES 3MA 4MA MAN PS2".split())

TERMINOS = [
    ("Yahvé", r"\bYahv[eé]h?\b"),
    ("Yah", r"\bYah\b"),
    ("Jehová", r"\bJehov[aá]\b"),
    ("de los Ejércitos", r"de los [Ee]jércitos"),
    ("Señor Yahvé", r"Señor Yahv[eé]"),
    ("Yahvé Dios", r"Yahv[eé] Dios"),
    ("oh Yahvé", r"\b[Oo]h,? Yahv[eé]"),
    ("asamblea(s)", r"\b[Aa]sambleas?\b"),
    ("congregación", r"\b[Cc]ongregaci(?:ón|ones)\b"),
    ("iglesia(s)", r"\b[Ii]glesias?\b"),
    ("Seol", r"\bS[eh]e?ol\b"),
    ("Hades", r"\bHades\b"),
    ("Gehena", r"\bGeh?enn?a\b"),
    ("infierno", r"\b[Ii]nfiernos?\b"),
    ("Jacobo", r"\bJacobo\b"),
    ("Santiago", r"\bSantiago\b"),
    ("Elisabet", r"\bElisabeth?\b"),
    ("Isabel", r"\bIsabel\b"),
    ("Buenas Nuevas", r"\b[Bb]uenas? [Nn]uevas?\b"),
    ("Buena Noticia", r"\b[Bb]uenas? [Nn]oticias?\b"),
    ("evangelio", r"\b[Ee]vangelio\b"),
    ("copa", r"\b[Cc]opas?\b"),
    ("cáliz", r"\b[Cc]áliz\b"),
    ("anciano(s)", r"\b[Aa]ncianos?\b"),
    ("presbítero", r"\b[Pp]resbíteros?\b"),
    ("supervisor", r"\b[Ss]upervisor(?:es)?\b"),
    ("obispo", r"\b[Oo]bispos?\b"),
    ("diácono / servidor", r"\b[Dd]iáconos?\b|\b[Ss]ervidor(?:es)?\b"),
    ("arrepent-", r"\b[Aa]rrep[ie]nt\w+"),
    ("convert-", r"\b[Cc]onv[ie]rt\w+"),
    ("bienaventurado", r"\b[Bb]ienaventurad[oa]s?\b"),
    ("dichoso", r"\b[Dd]ichos[oa]s?\b"),
    ("bendito/bendecido", r"\b[Bb]endit[oa]s?\b|\b[Bb]endecid[oa]s?\b"),
    ("día de reposo", r"día de (?:reposo|descanso)"),
    ("sábado", r"\b[Ss]ábados?\b"),
    ("Consolador", r"\bConsolador\b"),
    ("Abogado / Paráclito", r"\bAbogado\b|\bParáclito\b"),
    ("Verbo", r"\bVerbo\b"),
    ("Palabra (mayúscula)", r"\bPalabra\b"),
    ("gracia", r"\b[Gg]racia\b"),
    ("favor", r"\b[Ff]avor(?:ecid[oa])?\b"),
    ("recaudador de impuestos", r"recaudador(?:es)? de impuestos"),
    ("publicano", r"\b[Pp]ublicanos?\b"),
    ("gentiles", r"\b[Gg]entil(?:es)?\b"),
    ("Mesías", r"\bMesías\b"),
    ("Emanuel", r"\bEmm?anuel\b"),
    ("Espíritu Santo", r"Espíritu Santo"),
    ("Santo Espíritu", r"Santo Espíritu"),
    ("vosotros", r"\b[Vv]osotros\b"),
    ("ustedes", r"\b[Uu]stedes\b"),
    ("comillas inglesas", r"[“”]"),
    ("comillas latinas", r"[«»]"),
]

VERSICULOS_CLAVE = [
    "Gn 1,1-2", "Ex 3,14-15", "Is 7,14", "Is 9,5", "Sal 22,1-4", "Sal 50,1-4", "Sal 94,1-3",
    "Mt 3,2", "Mt 5,3-10", "Mt 6,9-13", "Mt 16,16-19", "Mt 26,26-28", "Mt 26,39", "Mt 28,19-20",
    "Mc 1,15", "Lc 1,28", "Lc 1,41-43", "Lc 1,46-49", "Lc 2,14", "Lc 22,19-20",
    "Jn 1,1", "Jn 1,14", "Jn 6,53-56", "Jn 14,16", "Jn 19,26-27", "Jn 20,22-23",
    "Hch 2,42", "Hch 20,17", "Hch 20,28", "Rm 1,16", "1Co 11,23-26", "Flp 2,10-11",
    "1Tm 3,1-2", "Tt 1,5", "St 5,14", "1Pe 2,9", "Ap 12,1",
]


def grupo(libro: str) -> str:
    return "NT" if libro in NT else "DC" if libro in DEUTERO else "AT"


def main() -> int:
    biblia = Biblia.desde_json(sys.argv[1])
    salida = Path(sys.argv[2])
    lineas = ["# Auditoría de vocabulario", ""]
    lineas += ["## Términos", "", "| Término | AT | DC | NT | Primer caso |", "| --- | --- | --- | --- | --- |"]
    for nombre, patron in TERMINOS:
        rx = re.compile(patron)
        cuenta = {"AT": 0, "DC": 0, "NT": 0}
        ejemplo = ""
        ejemplo_nt = ""
        for libro, caps in biblia.libros.items():
            g = grupo(libro)
            for cap, versos in caps.items():
                for num, texto in versos.items():
                    n = len(rx.findall(texto))
                    if not n:
                        continue
                    cuenta[g] += n
                    if not ejemplo:
                        ejemplo = f"{libro} {cap},{num}: {texto[:110]}"
                    if g == "NT" and not ejemplo_nt:
                        ejemplo_nt = f"{libro} {cap},{num}: {texto[:110]}"
        caso = ejemplo_nt or ejemplo
        lineas.append(
            f"| {nombre} | {cuenta['AT']} | {cuenta['DC']} | {cuenta['NT']} | {caso.replace('|', '/')} |"
        )

    lineas += ["", "## Versículos clave", ""]
    for cita in VERSICULOS_CLAVE:
        try:
            texto = biblia.texto(cita)
        except TextoNoEncontrado as e:
            texto = f"NO ENCONTRADO: {e}"
        lineas.append(f"- **{cita}**: {texto}")

    lineas += ["", "## Estructura de los salmos", ""]
    salmos = biblia.libros.get("PSA", {})
    lineas.append("Versículos por salmo: " + " ".join(f"{n}:{len(v)}" for n, v in sorted(salmos.items())))

    salida.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Informe escrito en {salida} ({salida.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
