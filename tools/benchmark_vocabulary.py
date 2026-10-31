"""Mede busca em memória, separada de parsing, Chrome e rede."""
import argparse
import json
import platform
import statistics
import time

from stopots_v2.vocabulary import Vocabulary


def benchmark(iterations=2000):
    started = time.perf_counter()
    vocab = Vocabulary.bundled()
    load_ms = (time.perf_counter() - started) * 1000
    cases = [(label, letter) for label in ('Animal', 'Profissão', 'Objeto', 'Cidade', 'CEP', 'Palavra em Inglês') for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']
    for label, letter in cases:
        vocab.choose(label, letter, 20, 'aquecimento')
    elapsed = []
    for i in range(iterations):
        label, letter = cases[i % len(cases)]
        start = time.perf_counter_ns()
        vocab.choose(label, letter, 20, str(i))
        elapsed.append((time.perf_counter_ns() - start) / 1000000)
    elapsed.sort()
    return {'schema_version': 1, 'subject': 'in_memory_lookup', 'vocabulary': vocab.version,
            'python': platform.python_version(), 'iterations': iterations, 'load_ms': round(load_ms, 3),
            'median_ms': round(statistics.median(elapsed), 4), 'p95_ms': round(elapsed[int(.95 * (len(elapsed)-1))], 4),
            'max_ms': round(max(elapsed),4), 'scope': 'Consulta com limite 20 UTF-16; exclui navegador, parsing e rede',
            'city_coverage': vocab.coverage(['Cidade','CEP'], list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--iteracoes', type=int, default=2000)
    args = p.parse_args()
    if args.iteracoes < 1:
        p.error('Use pelo menos uma iteração')
    print(json.dumps(benchmark(args.iteracoes), ensure_ascii=False, indent=2))
