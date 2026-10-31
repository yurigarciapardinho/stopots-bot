"""Regressão: sucesso da CLI não pode virar falha na corrida do observador."""
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('public_harness', Path(__file__).parents[2] / 'tools/validate_public_v2.py')
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


def test_cli_completion_accepts_real_log_with_preamble(tmp_path):
    result = {'status': 'concluido', 'final_result_verified': True,
              'ranking': {'rows': [['participante_1', 490]], 'semantic': 'total_partida'}}
    log = tmp_path / 'cli.log'
    log.write_text('Chrome pronto.\nAções: {}\n' + json.dumps(result, indent=2), encoding="utf-8")
    assert harness.cli_completion(0, log) == result
    assert harness.cli_completion(2, log) is None


def test_cli_completion_rejects_timeout_and_truncated_output(tmp_path):
    log = tmp_path / 'cli.log'
    log.write_text(json.dumps({'status': 'prazo_encerrado', 'final_result_verified': False}, indent=2), encoding="utf-8")
    assert harness.cli_completion(0, log) is None
    log.write_text('{\n  "status": "concluido",', encoding="utf-8")
    assert harness.cli_completion(0, log) is None


def test_partial_public_match_does_not_become_full_certification():
    class Observer:
        player_ids = {'ValidacaoV2': 'participante_6'}
    report = {'versions': {'package_path_kind': 'installed-wheel'},
              'stage': {'total_rounds': 8},
              'rounds': {str(i): {'writing_observed': True} for i in range(3, 9)}}
    harness.record_final(report, {'rows': [['participante_1', 490]]}, 'cli', 0, Observer())
    assert report['status'] == 'completed' and report['final_result_verified']
    assert not report['full_match_observed'] and not report['final_own_score_verified']
    assert report['writing_rounds_observed'] == [3, 4, 5, 6, 7, 8]
