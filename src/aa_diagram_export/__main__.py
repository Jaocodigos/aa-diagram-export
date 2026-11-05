"""CLI: chama as etapas na ordem do pipeline (§10.1 da spec).

Este arquivo não tem lógica própria. Ele lê os argumentos, chama
loader → parser → resolver → render e grava os arquivos. Quem quiser
entender o que o programa faz lê daqui de cima pra baixo.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config, loader, render, resolver
from .model import Bot
from .parser import parse_bot

SAIDA_PADRAO = Path("docs/diagramas")


def build_argparser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(
        prog="python -m aa_diagram_export",
        description=(
            "Gera diagramas Mermaid a partir de um export de bots do "
            "Automation Anywhere A360."
        ),
    )
    cli.add_argument(
        "--input",
        required=True,
        type=Path,
        metavar="<zip|pasta>",
        help="o .zip do Control Room ou a pasta já extraída",
    )
    cli.add_argument(
        "--out",
        type=Path,
        default=SAIDA_PADRAO,
        metavar="<pasta>",
        help=f"onde gravar os .md (padrão: {SAIDA_PADRAO})",
    )
    cli.add_argument(
        "--max-depth",
        type=int,
        default=None,
        metavar="N",
        help="profundidade de expansão das subtarefas (padrão: dicionario.toml)",
    )
    cli.add_argument(
        "--dicionario",
        type=Path,
        default=None,
        metavar="<arquivo>",
        help="caminho do dicionario.toml (padrão: o do diretório atual)",
    )
    cli.add_argument(
        "--no-call-graph",
        action="store_true",
        help="não desenhar o grafo de chamadas no index.md",
    )
    cli.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="terminar com erro se algum bot chamado não estiver no export",
    )
    cli.add_argument("--quiet", action="store_true", help="não escrever no console")
    return cli


def _desenhar_dentro_do_limite(
    bot: Bot,
    inventario: dict[str, Bot],
    dic: config.Dictionary,
    profundidade: int,
) -> tuple[render.Diagram, resolver.ResolveReport, int]:
    """Desenha o bot na maior profundidade que ainda renderiza.

    O Mermaid recusa diagrama com mais de 500 arestas e o GitHub usa esse
    padrão, então expandir demais produz um arquivo que não aparece para
    ninguém. Em vez de entregar isso, o diagrama é refeito com um nível a
    menos até caber, e a página diz que foi reduzida.
    """
    for tentativa in range(profundidade, -1, -1):
        parcial = resolver.ResolveReport()
        expandido, _ = resolver.expand(
            bot, inventario, max_depth=tentativa, report=parcial
        )
        diagrama = render.bot_diagram(expandido, dic)
        if not diagrama.too_big or tentativa == 0:
            return diagrama, parcial, tentativa
    raise AssertionError("inalcançável: o laço sempre retorna em tentativa == 0")


def main(argv: list[str] | None = None) -> int:
    args = build_argparser().parse_args(argv)

    def aviso(texto: str) -> None:
        if not args.quiet:
            print(texto, file=sys.stderr)

    try:
        dic = config.load(args.dicionario)
    except (FileNotFoundError, ValueError) as erro:
        aviso(f"erro no dicionário: {erro}")
        return 2

    profundidade = args.max_depth if args.max_depth is not None else dic.max_depth

    try:
        export = loader.load_export(args.input)
        bots: list[Bot] = []
        for arquivo in export.files:
            try:
                bots.append(parse_bot(json.loads(arquivo.content), arquivo.logical_path))
            except ValueError as erro:
                # Um arquivo ruim não derruba o export inteiro.
                aviso(f"ignorado: {erro}")
        ignorados = export.ignored
    except (FileNotFoundError, ValueError) as erro:
        aviso(f"erro na entrada: {erro}")
        return 2

    if not bots:
        aviso("nenhum bot encontrado no export.")
        return 1

    inventario = resolver.build_inventory(bots)
    relatorio = resolver.ResolveReport()
    desconhecidos: set[str] = set()
    reduzidos: dict[str, tuple[int, int]] = {}
    paginas: dict[str, str] = {}

    for bot in sorted(bots, key=lambda b: b.path):
        diagrama, parcial, usada = _desenhar_dentro_do_limite(
            bot, inventario, dic, profundidade
        )
        relatorio.merge(parcial)
        desconhecidos |= set(diagrama.unknown_commands)
        if usada < profundidade:
            reduzidos[bot.path] = (usada, profundidade)
            aviso(
                f"{bot.path}: expandido até {usada} em vez de {profundidade} "
                "para caber no limite de arestas do Mermaid"
            )
        # Os metadados vêm do bot original: a contagem de ações e a lista de
        # bots chamados são dele, não das subtarefas que entraram no desenho.
        paginas[render.page_relpath(bot)] = render.bot_page(
            bot, dic, diagram=diagrama, depth_used=usada, depth_requested=profundidade
        )

    paginas["index.md"] = render.index_page(
        sorted(bots, key=lambda b: b.path),
        dic,
        unresolved=relatorio.as_lists(),
        unknown_commands=desconhecidos,
        ignored_files=ignorados,
        include_call_graph=not args.no_call_graph,
        depth_reduced=reduzidos,
    )

    for relativo, conteudo in sorted(paginas.items()):
        destino = args.out / relativo
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(conteudo, encoding="utf-8", newline="\n")

    aviso(f"{len(bots)} bot(s) → {len(paginas)} arquivo(s) em {args.out}")
    if desconhecidos:
        aviso(
            f"{len(desconhecidos)} comando(s) sem rótulo no dicionario.toml "
            "(listados no index.md)"
        )
    if relatorio.unresolved:
        aviso(
            f"{len(relatorio.unresolved)} bot(s) chamado(s) e não encontrado(s) "
            "no export (listados no index.md)"
        )
        if args.fail_on_missing:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
