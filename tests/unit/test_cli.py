import json

from stopots_v2.cli import main, parser


def test_flags_are_explicit_even_in_automatic_mode():
    args = parser().parse_args(['executar', '--modo', 'automatico', '--stop', '--no-votos'])
    assert args.stop is True and args.votos is False and args.avaliar is None


def test_pause_and_resume_commands(tmp_path, capsys):
    path = tmp_path / 'control.json'
    assert main(['pausar', '--controle', str(path)]) == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {'paused': True}
    assert main(['retomar', '--controle', str(path)]) == 0
    assert json.loads(path.read_text(encoding="utf-8")) == {'paused': False}


def test_invalid_website_rejected_before_launch(capsys):
    assert main(['executar', '--url', 'https://example.com']) == 2
    assert 'Use a home' in capsys.readouterr().err
