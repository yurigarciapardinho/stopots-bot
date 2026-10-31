# SPDX-License-Identifier: LicenseRef-YGP-NoResale-1.0
# Copyright (c) 2026 Yuri Garcia Pardinho
"""Importação offline de fatos geográficos; sem rede no runtime do jogo."""
from __future__ import annotations

import json
import re
import unicodedata

from .normalization import lookup
from .vocabulary import digest, lexeme_id, validate

IBGE_URL = 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome'
IBGE_SOURCE = 'ibge-municipios-2026-10-29'


def validate_ibge(snapshot):
    if snapshot.get('schema_version') != 1 or snapshot.get('source_url') != IBGE_URL:
        raise ValueError('Origem ou esquema IBGE inesperado')
    if not re.fullmatch('[a-f0-9]{64}', snapshot.get('response_sha256', '')) or not snapshot.get('observed_at'):
        raise ValueError('Snapshot sem data/checksum de obtenção')
    records = snapshot.get('records')
    if not isinstance(records, list) or not records:
        raise ValueError('Lista IBGE vazia ou inválida')
    ids = set()
    for record in records:
        if not isinstance(record, dict) or type(record.get('id')) is not int or not 1000000 <= record['id'] <= 9999999:
            raise ValueError('Código de município inválido')
        name = record.get('name')
        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            raise ValueError('Nome de município inválido')
        if record['id'] in ids:
            raise ValueError('Código de município duplicado')
        ids.add(record['id'])
    return snapshot


def import_ibge(document, snapshot):
    validate(document)
    validate_ibge(snapshot)
    result = json.loads(json.dumps(document))
    if IBGE_SOURCE in result['sources']:
        raise ValueError('Fonte IBGE já importada; importe numa nova cópia editorial')
    result['sources'][IBGE_SOURCE] = {
        'kind': 'official_geographic_records', 'url': IBGE_URL,
        'documentation': 'https://servicodados.ibge.gov.br/api/docs/localidades',
        'open_data_policy': 'https://www.ibge.gov.br/acesso-informacao/dados-abertos.html',
        'attribution': 'Fonte: IBGE, API de Localidades, nomes e códigos de municípios',
        'license': 'sem identificador de licença na resposta da API; fonte e política de dados abertos registradas',
        'observed_at': snapshot['observed_at'], 'response_sha256': snapshot['response_sha256'],
        'snapshot_sha256': digest(snapshot), 'records': len(snapshot['records'])}
    for record in sorted(snapshot['records'], key=lambda r: r['id']):
        display = unicodedata.normalize('NFC', record['name'].strip())
        sense = 'ibge:' + str(record['id'])
        lid = lexeme_id(display, 'pt', sense)
        result['lexemes'].append({'id': lid, 'display': display, 'key': lookup(display),
                                 'language': 'pt', 'sense': sense, 'variants': [display]})
        result['associations'].append({'lexeme_id': lid, 'category': 'cidade', 'state': 'pending',
                                      'sources': [IBGE_SOURCE], 'source_record': str(record['id'])})
    return validate(result)


def approve_ibge_geography(document, snapshot):
    """Regra editorial explícita ibge-city-v1, aplicada após a importação pendente.

    Aprova somente pares id/nome idênticos ao snapshot oficial identificado.
    Não promove outros temas, fontes ou todo o legado.
    """
    validate(document)
    validate_ibge(snapshot)
    result = json.loads(json.dumps(document))
    source = result['sources'][IBGE_SOURCE]
    if source['snapshot_sha256'] != digest(snapshot):
        raise ValueError('Snapshot diverge da fonte importada')
    words = {w['id']: w for w in result['lexemes']}
    records = {str(r['id']): r['name'] for r in snapshot['records']}
    approved = 0
    for association in result['associations']:
        if IBGE_SOURCE not in association['sources']:
            continue
        code = association.get('source_record')
        word = words[association['lexeme_id']]
        if association['category'] != 'cidade' or code not in records or word['display'] != unicodedata.normalize('NFC', records[code].strip()) or word['sense'] != 'ibge:' + code:
            raise ValueError('Associação não satisfaz ibge-city-v1')
        association.update(state='approved', review_note='ibge-city-v1: nome de município identificado diretamente por código oficial; esquema e unicidade validados')
        approved += 1
    if approved != len(records):
        raise ValueError('Importação IBGE incompleta')
    source['review_rule'] = 'ibge-city-v1'
    return validate(result)
