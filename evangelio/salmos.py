"""Conversión de la numeración litúrgica de los salmos a la hebrea.

La liturgia en español numera los salmos como la Vulgata y los Setenta. La
mayoría de las Biblias actuales, incluida la que usa este proyecto, siguen la
numeración hebrea. Del 10 al 147 casi todos difieren en uno.

Esta tabla convierte solo el NÚMERO del salmo. La numeración de los
versículos también puede variar entre ediciones (por ejemplo, según si el
título del salmo cuenta como versículo), y eso no se resuelve aquí.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SalmoHebreo:
    numero: int
    ver_ini: int | None = None  # None = salmo entero
    ver_fin: int | None = None


def liturgico_a_hebreo(numero: int) -> list[SalmoHebreo]:
    """Devuelve el salmo o salmos hebreos que forman el salmo litúrgico dado."""
    if not 1 <= numero <= 150:
        raise ValueError(f"No existe el salmo {numero}")
    if numero <= 8 or numero >= 148:
        return [SalmoHebreo(numero)]
    if numero == 9:  # el 9 litúrgico reúne el 9 y el 10 hebreos
        return [SalmoHebreo(9), SalmoHebreo(10)]
    if numero <= 112:
        return [SalmoHebreo(numero + 1)]
    if numero == 113:  # reúne el 114 y el 115 hebreos
        return [SalmoHebreo(114), SalmoHebreo(115)]
    if numero == 114:  # primera mitad del 116 hebreo
        return [SalmoHebreo(116, 1, 9)]
    if numero == 115:  # segunda mitad del 116 hebreo
        return [SalmoHebreo(116, 10, 19)]
    if numero <= 145:
        return [SalmoHebreo(numero + 1)]
    if numero == 146:  # primera mitad del 147 hebreo
        return [SalmoHebreo(147, 1, 11)]
    return [SalmoHebreo(147, 12, 20)]  # 147 litúrgico
