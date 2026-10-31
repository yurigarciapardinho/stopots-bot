# SPDX-License-Identifier: LicenseRef-YGP-NoResale-1.0
# Copyright (c) 2026 Yuri Garcia Pardinho
"""Busca e transformação observada no input são contratos separados."""
import re
import unicodedata

NORMALIZATION_VERSION = "lookup-1"
GAME_INPUT_VERSION = "stopots-web-pt-2026-10-29"


def lookup(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return re.sub(r"\s+", " ", "".join(c for c in decomposed if not unicodedata.combining(c))).strip()


def game_value(value: str) -> str:
    # Contrato medido no campo real: espaços repetidos são reduzidos antes
    # da remoção de pontuação; hífen vira espaço, apóstrofo é removido.
    value = re.sub(r"\s+", " ", value).replace("-", " ")
    value = "".join(c for c in unicodedata.normalize("NFD", value) if not unicodedata.combining(c)).upper()
    return re.sub(r"[^A-Z0-9 ]", "", value).strip()


def utf16_length(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2
