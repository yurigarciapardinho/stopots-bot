from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
import json
import re

from .application import Policy
from .vocabulary import atomic_write, canonical
from .normalization import utf16_length


PRESETS = {
    'Só preencher': Policy(),
    'Só observar': Policy(fill_blanks=False, observe_only=True),
    'Automático': Policy(request_stop=True, set_votes=True, confirm_review=True, continue_results=True),
}
ACTION_KEYS = ('fill_blanks', 'request_stop', 'set_votes', 'confirm_review', 'continue_results')


def invitation_url(value: str) -> str:
    match = re.fullmatch(r'https://stopots\.com/pt/([0-9]+)/?', value.strip())
    if not match:
        raise ValueError('Cole um convite como https://stopots.com/pt/08193')
    return 'https://stopots.com/pt/' + match[1]


@dataclass
class Invitation:
    url: str
    nickname: str
    has_password: bool
    password: str = field(default='', repr=False)

    def validate(self):
        self.url = invitation_url(self.url)
        if not self.nickname.strip() or utf16_length(self.nickname) > 15:
            raise ValueError('Informe um apelido com até 15 caracteres.')
        if type(self.has_password) is not bool:
            raise ValueError('Indique se a sala tem senha.')
        if self.has_password and not self.password:
            raise ValueError('Informe a senha da sala.')
        return self


class Preferences:
    def __init__(self, path: Path):
        self.path = path
        self.theme = 'sistema'
        self.nickname = 'Jogador'
        self.profile = 'Só preencher'
        self.policy = Policy()
        self.reduced_motion = False
        try:
            d = json.loads(path.read_text(encoding='utf-8'))
            self.theme = d['theme'] if d.get('theme') in ('claro', 'escuro', 'sistema') else 'sistema'
            self.nickname = d.get('nickname', 'Jogador') if isinstance(d.get('nickname', 'Jogador'), str) else 'Jogador'
            settings = d.get('policy', {})
            if all(type(v) is bool for k, v in settings.items() if k in ACTION_KEYS + ('observe_only', 'require_all_filled')):
                self.policy = replace(Policy(), **{k: v for k, v in settings.items() if k in ACTION_KEYS + ('observe_only', 'require_all_filled')})
            self.profile = d.get('profile', 'Personalizado')
            self.reduced_motion = bool(d.get('reduced_motion', False))
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def save(self):
        # Lista permitida: senha, URL, endpoint e estado ativo nunca são persistidos.
        d = {'schema_version': 1, 'theme': self.theme, 'nickname': self.nickname,
             'profile': self.profile, 'policy': asdict(self.policy), 'reduced_motion': self.reduced_motion}
        atomic_write(self.path, canonical(d) + b'\n')

    def preset(self, name):
        if name not in PRESETS:
            raise ValueError('Perfil desconhecido')
        self.profile, self.policy = name, PRESETS[name]
        self.save()

    def action(self, key, enabled):
        if key not in ACTION_KEYS + ('require_all_filled',):
            raise ValueError('Ação desconhecida')
        self.policy = replace(self.policy, **{key: bool(enabled)}, observe_only=False)
        self.profile = 'Personalizado'
        self.save()
