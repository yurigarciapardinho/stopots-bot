from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager
from dataclasses import asdict
import importlib.metadata
from importlib.resources import files
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import tomllib

from . import __version__
from .application import Controller, EventLog, Policy
from .vocabulary import Vocabulary, atomic_write, canonical, import_legacy, publish, read_release, upsert, validate


def runtime():
    return Path(os.environ.get("STOPOTS_RUNTIME", Path.cwd() / ".runtime/v2")).resolve()


def load_vocab(path=None):
    if not path:
        return Vocabulary.bundled()
    current = Path(path)
    try:
        return Vocabulary(read_release(current))
    except (OSError, ValueError, KeyError):
        previous = current.with_suffix(current.suffix + ".previous")
        if not previous.exists():
            raise
        recovered = Vocabulary(read_release(previous))
        print("Base atual inválida; usando versão anterior validada.", file=sys.stderr)
        return recovered


@asynccontextmanager
async def playwright_for(directory, attached=False):
    from playwright.async_api import async_playwright
    previous_env, previous_cache = os.environ.get('TMPDIR'), tempfile.tempdir
    try:
        if not attached:
            temporary = directory / 'tmp'
            temporary.mkdir(parents=True, exist_ok=True)
            os.environ['TMPDIR'] = str(temporary)
            tempfile.tempdir = None
        async with async_playwright() as pw:
            yield pw
    finally:
        if previous_env is None:
            os.environ.pop('TMPDIR', None)
        else:
            os.environ['TMPDIR'] = previous_env
        tempfile.tempdir = previous_cache


async def execute(args):
    from playwright.async_api import async_playwright
    from .adapters.web import StopotsWeb

    settings = {}
    if args.config:
        settings = tomllib.loads(Path(args.config).read_text(encoding="utf-8"))
    a = settings.get("automacao", {})
    def option(name, default):
        value = getattr(args, name)
        return a.get(name, default) if value is None else value
    policy = Policy(fill_blanks=option("preencher", True), request_stop=option("stop", False),
                    require_all_filled=option("exigir_todos", True), set_votes=option("votos", False),
                    confirm_review=option("avaliar", False), continue_results=option("continuar", False),
                    observe_only=args.modo == "observar", seed=args.semente)
    vocab = load_vocab(args.vocabulario)
    directory = runtime()
    directory.mkdir(parents=True, exist_ok=True)
    profile = Path(args.perfil) if args.perfil else directory / "chrome-v2"
    events = EventLog(Path(args.eventos) if args.eventos else directory / f"eventos-{int(time.time())}.jsonl")
    control = Path(args.controle) if args.controle else directory / "controle-v2.json"
    if not control.exists():
        atomic_write(control, b'{"paused":false}\n')
    async with playwright_for(directory, attached=bool(args.cdp)) as pw:
        context = None
        try:
            if args.cdp:
                import re
                if not re.fullmatch(r'http://(?:127\.0\.0\.1|localhost):\d+/?', args.cdp):
                    raise ValueError('O endpoint CDP precisa ser local')
                browser = await pw.chromium.connect_over_cdp(args.cdp, timeout=10000)
                matches = [page for ctx in browser.contexts for page in ctx.pages if page.url.rstrip('/') == args.url.rstrip('/')]
                if len(matches) != 1:
                    raise ValueError('Seleção CDP precisa corresponder a exatamente uma página pela URL')
                page = matches[0]
            else:
                context = await pw.chromium.launch_persistent_context(str(profile), channel="chrome", headless=args.headless,
                             locale="pt-BR", viewport={"width": 1440, "height": 1000},
                             args=["--no-first-run", "--no-default-browser-check"])
                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto(args.url, wait_until="domcontentloaded", timeout=45000)
            port = StopotsWeb(page)
            print("Chrome pronto. Entre na sala pela interface. Controle:", control, flush=True)
            print("Ações:", json.dumps(asdict(policy), ensure_ascii=False), flush=True)
            controller = Controller(port, vocab, policy, events, control)
            result = await controller.run(args.tempo_limite)
            await port.close()
            return result
        finally:
            if context:
                await context.close()


def parser():
    p = argparse.ArgumentParser(prog="stopots-v2", description="StopotS v2 — assistente local em português")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("diagnostico", help="Versões, base instalada e capacidades verificadas")
    run = sub.add_parser("executar", help="Abrir Chrome dedicado e acompanhar uma partida")
    run.add_argument("--modo", choices=["observar", "assistido", "automatico"], default="assistido",
                     help="As opções de ação são explícitas em qualquer modo")
    run.add_argument("--url", default="https://stopots.com/pt")
    run.add_argument("--perfil")
    run.add_argument("--cdp", help="Anexar a Chrome já preparado via endpoint local; preserva seus contextos")
    run.add_argument("--eventos")
    run.add_argument("--controle")
    run.add_argument("--config", help="Arquivo TOML com tabela [automacao]")
    run.add_argument("--vocabulario", help="Release JSON; versão fixada durante a execução")
    run.add_argument("--semente", default="stopots-v2")
    run.add_argument("--headless", action="store_true")
    run.add_argument("--tempo-limite", type=float, default=1800)
    for name in ["preencher", "stop", "votos", "avaliar", "continuar", "exigir-todos"]:
        run.add_argument("--" + name, action=argparse.BooleanOptionalAction, default=None)
    for command in ("pausar", "retomar"):
        action = sub.add_parser(command, help="Suspender ou retomar ações da execução")
        action.add_argument("--controle", type=Path, default=runtime() / "controle-v2.json")
    vocab = sub.add_parser("vocabulario", help="Importação, curadoria e cobertura offline")
    vs = vocab.add_subparsers(dest="operation", required=True)
    imp = vs.add_parser("importar-legado")
    imp.add_argument("origem", type=Path)
    imp.add_argument("taxonomia", type=Path, help="Objeto categories do documento editorial")
    imp.add_argument("destino", type=Path)
    edit = vs.add_parser("editar")
    edit.add_argument("documento", type=Path)
    edit.add_argument("categoria")
    edit.add_argument("palavra")
    edit.add_argument("--estado", choices=["pending", "approved", "rejected"], default="pending")
    edit.add_argument("--fonte", required=True)
    edit.add_argument("--nota", required=True)
    pub = vs.add_parser("publicar")
    pub.add_argument("documento", type=Path)
    pub.add_argument("destino", type=Path)
    cov = vs.add_parser("cobertura")
    cov.add_argument("--vocabulario")
    cov.add_argument("--letras", default="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    cov.add_argument("--temas", nargs="+")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "executar":
            import re
            if not re.fullmatch(r"https://stopots\.com/pt(?:/\d+)?/?", args.url):
                raise ValueError("Use a home ou URL de sala do StopotS em português")
            result = asyncio.run(execute(args))
        elif args.command in ("pausar", "retomar"):
            atomic_write(args.controle, canonical({"paused": args.command == "pausar"}) + b"\n")
            result = {"status": "pausado" if args.command == "pausar" else "retomado"}
        elif args.command == "diagnostico":
            v = Vocabulary.bundled()
            try:
                chrome = subprocess.check_output(["google-chrome", "--version"], text=True).strip()
            except (OSError, subprocess.CalledProcessError):
                chrome = "não encontrado; instale Chrome ou configure o canal no adaptador"
            result = {"version": __version__, "python": sys.version.split()[0],
                      "playwright": importlib.metadata.version("playwright"), "chrome": chrome,
                      "vocabulary": v.version,
                      "capabilities": json.loads(files("stopots_v2").joinpath("resources/capabilities.json").read_text())}
        elif args.operation == "importar-legado":
            doc = import_legacy(args.origem, json.loads(args.taxonomia.read_text(encoding="utf-8")))
            atomic_write(args.destino, canonical(doc) + b"\n")
            result = doc["import_metrics"]
        elif args.operation == "editar":
            doc = validate(json.loads(args.documento.read_text(encoding="utf-8")))
            doc = upsert(doc, args.categoria, args.palavra, args.estado, args.fonte, args.nota)
            atomic_write(args.documento, canonical(doc) + b"\n")
            result = {"status": "salvo", "publicado": False}
        elif args.operation == "publicar":
            result = publish(json.loads(args.documento.read_text(encoding="utf-8")), args.destino)
        else:
            v = load_vocab(args.vocabulario)
            labels = args.temas or [d["label"] for d in v.taxonomy.categories.values()]
            result = {"version": v.version, "coverage": v.coverage(labels, list(args.letras.upper()))}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") not in ("bloqueado", "prazo_encerrado") else 2
    except KeyboardInterrupt:
        print("Execução encerrada; recursos próprios fechados.")
        return 130
    except (OSError, ValueError, KeyError) as exc:
        print("Erro:", str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
