from stopots_v2 import cli


def test_public_game_url_is_accepted(monkeypatch):
    observed = []
    async def execute(args):
        observed.append(args.url)
        return {'status':'concluido'}
    monkeypatch.setattr(cli, 'execute', execute)
    assert cli.main(['executar','--url','https://stopots.com/pt/game']) == 0
    assert observed == ['https://stopots.com/pt/game']
    assert cli.main(['executar','--url','https://stopots.com.evil/pt/game']) == 2
    assert observed == ['https://stopots.com/pt/game']
