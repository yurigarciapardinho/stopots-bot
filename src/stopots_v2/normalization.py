"""Busca e transformação observada no input são contratos separados."""
import re
import unicodedata

NORMALIZATION_VERSION = "lookup-1"


def lookup(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.casefold())
    return re.sub(r"\s+", " ", "".join(c for c in decomposed if not unicodedata.combining(c))).strip()


def game_value(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", value) if not unicodedata.combining(c)).upper().strip()


def utf16_length(value: str) -> int:
    return len(value.encode("utf-16-le")) // 2
