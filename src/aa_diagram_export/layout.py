"""Quebra um bot grande em seções legíveis (§8.2 da spec).

Um diagrama é encolhido pelo navegador até caber na largura da página, então
desenho grande não vira desenho grande: vira desenho ilegível. Acima do
orçamento de nós, os `Step` maiores saem do desenho principal e viram seções
da mesma página, cada uma com o seu diagrama.

O `Step` é a costura natural porque é o agrupador que o próprio dev criou no
A360: tem título, e tirar um da vista não altera o fluxo, só esconde o miolo.

Esta camada é só apresentação. O modelo não sabe que existe seção — o render
recebe um mapa de "este Step vira referência" e o resto segue igual.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterator

from .config import Dictionary
from .model import Bot, CallBot, If, Loop, Node, Step, TryCatch, stable_node_id
from .render import Diagram, Section, bot_diagram, section_diagram

#: Step menor que isto não vale virar seção: a página ganharia um salto de
#: navegação para economizar quase nada no desenho.
MINIMO_PARA_VIRAR_SECAO = 4


@dataclass(frozen=True)
class Layout:
    """O desenho principal de um bot e as seções que saíram dele."""

    diagram: Diagram
    sections: tuple[Section, ...] = ()


def split_bot(bot: Bot, dic: Dictionary, *, budget: int | None = None) -> Layout:
    """Desenha o bot, quebrando-o em seções enquanto passar do orçamento."""
    orcamento = budget if budget is not None else dic.node_budget
    externalizados: dict[str, str] = {}
    escolhidos: list[Step] = []

    while True:
        principal = bot_diagram(bot, dic, externalize=externalizados)
        if principal.node_count <= orcamento:
            break
        candidato = _maior_candidato(bot.body, dic, externalizados)
        if candidato is None:
            break
        externalizados[candidato.uid] = _ancora(candidato)
        escolhidos.append(candidato)

    secoes: list[Section] = []
    for passo in escolhidos:
        secoes.extend(_secoes_de(passo, dic, orcamento))

    return Layout(diagram=principal, sections=tuple(secoes))


def _secoes_de(passo: Step, dic: Dictionary, orcamento: int) -> list[Section]:
    """A seção de um Step, quebrada de novo se ela mesma passar do orçamento."""
    externalizados: dict[str, str] = {}
    escolhidos: list[Step] = []

    while True:
        desenho = section_diagram(passo, dic, externalize=externalizados)
        if desenho.node_count <= orcamento:
            break
        candidato = _maior_candidato(passo.body, dic, externalizados)
        if candidato is None:
            break
        externalizados[candidato.uid] = _ancora(candidato)
        escolhidos.append(candidato)

    secoes = [
        Section(anchor=_ancora(passo), title=passo.title or "Passo", diagram=desenho)
    ]
    for filho in escolhidos:
        secoes.extend(_secoes_de(filho, dic, orcamento))
    return secoes


def _maior_candidato(
    corpo: tuple[Node, ...], dic: Dictionary, ja_externalizados: dict[str, str]
) -> Step | None:
    """O Step mais caro que ainda está desenhado por inteiro.

    Só os Steps superficiais entram: tirar um Step de dentro de outro que
    continua no desenho deixaria a página com uma seção que ninguém alcança
    pelo caminho de leitura natural.
    """
    melhor: Step | None = None
    melhor_tamanho = MINIMO_PARA_VIRAR_SECAO - 1

    for passo in _steps_superficiais(corpo, ja_externalizados):
        tamanho = _tamanho_do_miolo(passo, dic)
        if tamanho > melhor_tamanho:
            melhor, melhor_tamanho = passo, tamanho

    return melhor


def _tamanho_do_miolo(passo: Step, dic: Dictionary) -> int:
    """Quantos nós o Step traz de verdade.

    Desconta o início e o fim que a seção acrescenta ao redor do miolo. Sem
    isso um Step com duas ações contaria quatro e passaria pelo mínimo, e a
    página ganharia um salto de navegação para economizar dois nós.
    """
    return max(0, section_diagram(passo, dic).node_count - 2)


def _steps_superficiais(
    nodes: tuple[Node, ...], ja_externalizados: dict[str, str]
) -> Iterator[Step]:
    """Os Steps mais rasos de cada ramo, sem descer para dentro deles."""
    for node in nodes:
        match node:
            case Step() if node.uid not in ja_externalizados:
                yield node
            case Step():
                # Já virou referência: o miolo saiu do desenho, nada a tirar.
                continue
            case If(branches=branches, else_body=else_body):
                for ramo in branches:
                    yield from _steps_superficiais(ramo.body, ja_externalizados)
                yield from _steps_superficiais(else_body, ja_externalizados)
            case Loop(body=body) | CallBot(body=body):
                yield from _steps_superficiais(body, ja_externalizados)
            case TryCatch(try_body=t, catch_body=c, finally_body=f):
                yield from _steps_superficiais(t, ja_externalizados)
                yield from _steps_superficiais(c, ja_externalizados)
                yield from _steps_superficiais(f, ja_externalizados)
            case _:
                continue


def _ancora(passo: Step) -> str:
    """Âncora estável, derivada do uid, não do título.

    Dois Steps podem ter o mesmo título, e cada plataforma monta o slug de um
    cabeçalho de um jeito. Derivar do uid evita colisão e não depende de
    adivinhar a regra do renderizador.
    """
    return f"secao-{stable_node_id(passo.uid)[1:]}"
