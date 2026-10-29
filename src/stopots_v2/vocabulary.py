from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
import hashlib
import json
import os
import re
import tempfile
import unicodedata

from .domain import Verdict
from .normalization import NORMALIZATION_VERSION, game_value, lookup, utf16_length

SCHEMA = 1


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(data):
    return hashlib.sha256(canonical(data)).hexdigest()


def category_id(label):
    return re.sub(r"[^a-z0-9]+", "_", lookup(label)).strip("_")


def lexeme_id(spelling, language="pt", sense=""):
    return hashlib.sha256(canonical([language, lookup(spelling), sense])).hexdigest()[:24]


@dataclass(frozen=True)
class Resolution:
    state: str
    category: str | None
    reason: str


class Taxonomy:
    def __init__(self, document):
        self.categories = document["categories"]
        self.aliases = {}
        for cid, data in self.categories.items():
            for alias in [data["label"], cid.replace("_", " "), *data.get("aliases", [])]:
                self.aliases.setdefault(lookup(alias), set()).add(cid)
        for cid in self.categories:
            self.accepted_categories(cid)  # verifica referências e ciclos

    def resolve(self, label):
        ids = self.aliases.get(lookup(label), set())
        if len(ids) == 1:
            return Resolution("resolved", next(iter(ids)), "rótulo ou alias explícito")
        return Resolution("ambiguous" if ids else "unknown", None, "tema ambíguo" if ids else "tema sem categoria")

    def accepted_categories(self, cid, path=()):
        if cid not in self.categories:
            raise ValueError(f"Categoria não definida: {cid}")
        if cid in path:
            raise ValueError("Ciclo na taxonomia")
        result = {cid}
        for child in self.categories[cid].get("includes", []):
            result |= self.accepted_categories(child, (*path, cid))
        return result


def validate(document):
    if not isinstance(document, dict):
        raise ValueError("Documento deve ser um objeto JSON")
    if document.get("schema_version") != SCHEMA:
        raise ValueError("Versão de vocabulário incompatível")
    if not isinstance(document.get("categories"), dict) or not isinstance(document.get("sources"), dict):
        raise ValueError("Taxonomia e fontes devem ser objetos")
    tax = Taxonomy(document)
    lexemes = document["lexemes"]
    if not isinstance(lexemes, list) or not isinstance(document["associations"], list):
        raise ValueError("Lexemas e associações devem ser listas")
    ids = set()
    for word in lexemes:
        if not isinstance(word, dict) or not all(isinstance(word.get(k), str) and word[k] for k in ("id", "display", "key", "language")):
            raise ValueError("Lexema malformado")
        if word["id"] in ids or not word["display"].strip():
            raise ValueError("Lexema duplicado ou vazio")
        ids.add(word["id"])
        if word["display"] != unicodedata.normalize("NFC", word["display"]):
            raise ValueError("Grafia deve estar em NFC")
        if word["key"] != lookup(word["display"]) or not word["language"]:
            raise ValueError("Chave ou idioma inválido")
    seen = set()
    for a in document["associations"]:
        if not isinstance(a, dict) or not all(isinstance(a.get(k), str) for k in ("lexeme_id", "category", "state")):
            raise ValueError("Associação malformada")
        if not isinstance(a.get("sources"), list):
            raise ValueError("Procedência deve ser uma lista")
        pair = (a["lexeme_id"], a["category"])
        if pair in seen or pair[0] not in ids or pair[1] not in tax.categories:
            raise ValueError("Associação duplicada ou referência inválida")
        seen.add(pair)
        if a["state"] not in ("pending", "approved", "rejected"):
            raise ValueError("Estado editorial inválido")
        if not a["sources"] or any(s not in document["sources"] for s in a["sources"]):
            raise ValueError("Associação sem procedência")
        if a["state"] == "approved" and not a.get("review_note"):
            raise ValueError("Aprovação requer nota editorial")
    return document


def import_legacy(path: Path, taxonomy: dict):
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes)
    document = {"schema_version": SCHEMA, "categories": taxonomy, "lexemes": [], "associations": [],
                "sources": {"legacy": {"kind": "legacy_import", "sha256": hashlib.sha256(raw_bytes).hexdigest(),
                                        "license": "MIT", "approval": "pending"}}}
    words, pairs = {}, {}
    metrics = {"letters": len(raw), "categories": len({c for cell in raw.values() for c in cell}),
               "cells": 0, "empty_cells": 0, "entries": 0, "normalized_duplicate_excess": 0}
    for letter, cell in raw.items():
        for label, values in cell.items():
            if not isinstance(values, list):
                raise ValueError("Importação exige listas; arquivo legado corrompido")
            cid = category_id(label)
            if cid not in taxonomy:
                raise ValueError("Categoria do legado sem taxonomia: " + label)
            metrics["cells"] += 1
            metrics["empty_cells"] += not values
            keys = set()
            for value in values:
                metrics["entries"] += 1
                key = lookup(value)
                if key in keys:
                    metrics["normalized_duplicate_excess"] += 1
                keys.add(key)
                if not key.startswith(lookup(letter)):
                    raise ValueError("Inicial inconsistente no legado")
                language = taxonomy[cid].get("language", "pt")
                lid = lexeme_id(value, language)
                words.setdefault(lid, {"id": lid, "display": unicodedata.normalize("NFC", value),
                                       "key": key, "language": language, "sense": "", "variants": []})
                if value not in words[lid]["variants"]:
                    words[lid]["variants"].append(unicodedata.normalize("NFC", value))
                pairs.setdefault((lid, cid), {"lexeme_id": lid, "category": cid, "state": "pending", "sources": ["legacy"]})
    document["lexemes"] = sorted(words.values(), key=lambda w: w["id"])
    document["associations"] = sorted(pairs.values(), key=lambda a: (a["category"], a["lexeme_id"]))
    document["import_metrics"] = metrics
    return validate(document)


def upsert(document, label, spelling, state, source, note, language=None, sense=""):
    # Copia inclusive listas internas; leitores da partida continuam imutáveis.
    result = json.loads(json.dumps(document))
    tax = Taxonomy(result)
    resolution = tax.resolve(label)
    if resolution.state != "resolved":
        raise ValueError(resolution.reason)
    cid = resolution.category
    lang = language or tax.categories[cid].get("language", "pt")
    display = unicodedata.normalize("NFC", spelling.strip())
    lid = lexeme_id(display, lang, sense)
    word = next((w for w in result["lexemes"] if w["id"] == lid), None)
    if word is None:
        word = {"id": lid, "display": display, "key": lookup(display), "language": lang, "sense": sense, "variants": [display]}
        result["lexemes"].append(word)
    elif state == "approved":
        word["display"] = display
        if display not in word["variants"]:
            word["variants"].append(display)
    assoc = next((a for a in result["associations"] if (a["lexeme_id"], a["category"]) == (lid, cid)), None)
    if assoc is None:
        assoc = {"lexeme_id": lid, "category": cid, "sources": []}
        result["associations"].append(assoc)
    if source not in assoc["sources"]:
        assoc["sources"].append(source)
    assoc.update(state=state, review_note=note)
    return validate(result)


def compile_release(document):
    validate(document)
    approved = sorted((a for a in document["associations"] if a["state"] == "approved"),
                      key=lambda a: (a["category"], a["lexeme_id"]))
    ids = {a["lexeme_id"] for a in approved}
    payload = {"schema_version": SCHEMA, "normalization_version": NORMALIZATION_VERSION,
               "categories": document["categories"], "sources": document["sources"],
               "lexemes": sorted((w for w in document["lexemes"] if w["id"] in ids), key=lambda w: w["id"]),
               "associations": approved}
    return {"manifest": {"sha256": digest(payload), "source_sha256": digest(document),
                         "approved_associations": len(approved), "lexemes": len(ids),
                         "pending_associations": sum(a["state"] == "pending" for a in document["associations"])},
            "payload": payload}


def read_release(path):
    result = json.loads(Path(path).read_text(encoding="utf-8"))
    if result["manifest"]["sha256"] != digest(result["payload"]):
        raise ValueError("Checksum do vocabulário inválido")
    validate(result["payload"])
    if result["payload"]["normalization_version"] != NORMALIZATION_VERSION:
        raise ValueError("Normalização incompatível")
    if any(a["state"] != "approved" for a in result["payload"]["associations"]):
        raise ValueError("Release contém associações não aprovadas")
    if result['manifest']['approved_associations'] != len(result['payload']['associations']) or result['manifest']['lexemes'] != len(result['payload']['lexemes']):
        raise ValueError("Contagens do manifesto inconsistentes")
    return result


def atomic_write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def publish(document, path: Path):
    release = compile_release(document)  # valida antes de tocar na versão atual
    data = canonical(release) + b"\n"
    if path.exists():
        read_release(path)
        atomic_write(path.with_suffix(path.suffix + ".previous"), path.read_bytes())
    atomic_write(path, data)
    return release["manifest"]


class Vocabulary:
    def __init__(self, release):
        # Revalida também em memória e guarda uma cópia sem estado editorial mutável.
        if digest(release["payload"]) != release["manifest"]["sha256"]:
            raise ValueError("Checksum inválido")
        payload = json.loads(json.dumps(validate(release["payload"])))
        self.version = release["manifest"]["sha256"]
        self.taxonomy = Taxonomy(payload)
        words = {w["id"]: w for w in payload["lexemes"]}
        self.index = {}
        for a in payload["associations"]:
            if a["state"] != "approved":
                continue
            w = words[a["lexeme_id"]]
            lang = self.taxonomy.categories[a["category"]].get("language", "pt")
            if w["language"] != lang:
                continue
            self.index.setdefault((a["category"], w["key"][0]), []).append((w["id"], w["display"], w["key"]))
        self.index = {k: tuple(sorted(v)) for k, v in self.index.items()}

    @classmethod
    def bundled(cls):
        resource = files("stopots_v2").joinpath("resources/vocabulary.json")
        return cls(json.loads(resource.read_text(encoding="utf-8")))

    def candidates(self, label, letter, max_length=None):
        resolution = self.taxonomy.resolve(label)
        if resolution.state != "resolved" or not letter:
            return ()
        result = {}
        for cid in sorted(self.taxonomy.accepted_categories(resolution.category)):
            for lid, display, key in self.index.get((cid, lookup(letter)), ()):
                if max_length is None or utf16_length(game_value(display)) <= max_length:
                    # Homônimos mantêm IDs/fonte; a palavra digitada não ganha
                    # peso extra por existir em vários municípios/categorias.
                    result.setdefault(game_value(display), (lid, display))
        return tuple(result[k] for k in sorted(result))

    def choose(self, label, letter, max_length=None, seed=""):
        candidates = self.candidates(label, letter, max_length)
        if not candidates:
            return None
        index = int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(candidates)
        return candidates[index]

    def evaluate(self, label, letter, answer):
        key = lookup(answer)
        if not key or not letter:
            return Verdict.UNKNOWN, "resposta vazia ou inicial ausente"
        if not key.startswith(lookup(letter)):
            return Verdict.INCOMPATIBLE, "inicial incompatível"
        resolution = self.taxonomy.resolve(label)
        if resolution.state != "resolved":
            return Verdict.UNKNOWN, resolution.reason
        # A resposta já veio da UI: não reaplicar uma transformação que pode
        # gerar novos espaços ao remover pontuação. Aceitar grafia e forma UI.
        if any(key in (lookup(display), lookup(game_value(display))) for _, display in self.candidates(label, letter)):
            return Verdict.COMPATIBLE, "associação aprovada"
        return Verdict.UNKNOWN, "ausência na base não prova invalidade"

    def coverage(self, labels, letters):
        return {label: {letter: len(self.candidates(label, letter)) for letter in letters} for label in labels}
