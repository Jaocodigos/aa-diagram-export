"""Quebra um bot grande em arquivos legíveis (§8.2 da spec).

Um diagrama é encolhido pelo navegador até caber na largura da página, então
desenho grande não vira desenho grande: vira desenho ilegível. Acima do
orçamento de nós, os `Step` maiores saem do desenho principal e viram
arquivos próprios, numa pasta irmã com o nome do bot.

O `Step` é a costura natural porque é o agrupador que o próprio dev criou no
A360: tem título, e tirar um da vista não altera o fluxo, só esconde o miolo.

Esta camada é só apresentação. O modelo não sabe que existe seção — o render
recebe um mapa de "este Step vira referência, apontando para tal arquivo" e o
resto segue igual.

O trabalho sai em três fases porque o nome do arquivo de uma seção depende da
ordem final de todas elas, e a ordem só é conhecida depois de decidir quais
saem: primeiro decide-se o que sai, depois ordena-se e nomeia-se, e só então
os diagramas são desenhados com os links certos.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterator
from dataclasses import dataclass

from .config import Dictionary
from .model import Bot, CallBot, If, Loop, Node, Step, TryCatch, walk
from .render import (
    Diagram,
    Section,
    bot_diagram,
    section_diagram,
    sections_dirname,
)

#: Step menor que isto não vale virar arquivo: a navegação ganharia um salto
#: para economizar quase nada no desenho.
MINIMO_PARA_VIRAR_SECAO = 4

#: Limite do nome de arquivo gerado a partir do título do Step.
TAMANHO_DO_SLUG = 48


@dataclass(frozen=True)
class Layout:
    """O desenho principal de um bot e as seções que saíram dele."""

    diagram: Diagram
    sections: tuple[Section, ...] = ()


def split_bot(bot: Bot, dic: Dictionary, *, budget: int | None = None) -> Layout:
    """Desenha o bot, tirando Steps para arquivos próprios até caber."""
    orcamento = budget if budget is not None else dic.node_budget

    # Fase 1: quais Steps saem de cada desenho.
    extraidos: dict[str, list[Step]] = {}
    raiz: list[Step] = _planejar(
        lambda externos: bot_diagram(bot, dic, externalize=externos),
        bot.body,
        dic,
        orcamento,
    )
    extraidos[""] = raiz

    pendentes = list(raiz)
    while pendentes:
        passo = pendentes.pop(0)
        filhos = _planejar(
            lambda externos, p=passo: section_diagram(p, dic, externalize=externos),
            passo.body,
            dic,
            orcamento,
        )
        extraidos[passo.uid] = filhos
        pendentes.extend(filhos)

    todos = [passo for lista in extraidos.values() for passo in lista]
    if not todos:
        return Layout(diagram=bot_diagram(bot, dic))

    # Fase 2: ordem de leitura e nome de arquivo.
    #
    # A extração é gulosa, então sai na ordem de tamanho. Numerar por isso
    # daria "01" ao maior passo e não ao primeiro, o que é exatamente o
    # contrário do que alguém espera ao percorrer a pasta.
    ordem = {node.uid: posicao for posicao, node in enumerate(walk(bot.body))}
    todos.sort(key=lambda passo: ordem.get(passo.uid, len(ordem)))
    nomes = {
        passo.uid: f"{posicao:02d}-{_slug(passo.title)}.md"
        for posicao, passo in enumerate(todos, 1)
    }

    # Fase 3: desenhar com os links definitivos.
    pasta = sections_dirname(bot)
    principal = bot_diagram(
        bot,
        dic,
        externalize={passo.uid: f"{pasta}/{nomes[passo.uid]}" for passo in raiz},
    )

    secoes = [
        Section(
            step_uid=passo.uid,
            title=passo.title or "Passo",
            # Seção aponta para seção na mesma pasta, então o link é só o nome.
            diagram=section_diagram(
                passo,
                dic,
                externalize={
                    filho.uid: nomes[filho.uid] for filho in extraidos[passo.uid]
                },
            ),
            filename=nomes[passo.uid],
        )
        for passo in todos
    ]

    return Layout(diagram=principal, sections=tuple(secoes))


def _planejar(
    desenhar: Callable[[dict[str, str]], Diagram],
    corpo: tuple[Node, ...],
    dic: Dictionary,
    orcamento: int,
) -> list[Step]:
    """Quais Steps precisam sair deste desenho para ele caber no orçamento.

    Guloso: tira o maior ainda desenhado por inteiro, redesenha e repete. O
    valor do mapa é provisório nesta fase — o que importa aqui é só quais
    uids saem, não para onde apontam.
    """
    externos: dict[str, str] = {}
    escolhidos: list[Step] = []

    while True:
        if desenhar(externos).node_count <= orcamento:
            return escolhidos
        candidato = _maior_candidato(corpo, dic, externos)
        if candidato is None:
            # Nada mais a tirar: o desenho sai grande, mas sai.
            return escolhidos
        externos[candidato.uid] = ""
        escolhidos.append(candidato)


def _maior_candidato(
    corpo: tuple[Node, ...], dic: Dictionary, ja_externalizados: dict[str, str]
) -> Step | None:
    """O Step mais caro que ainda está desenhado por inteiro.

    Só os Steps superficiais entram: tirar um Step de dentro de outro que
    continua no desenho deixaria um arquivo que ninguém alcança pelo caminho
    de leitura natural.
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
    navegação ganharia um salto para economizar dois nós.
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


def _slug(titulo: str) -> str:
    """Nome de arquivo legível a partir do título do Step.

    Sem acento e sem maiúscula, para o caminho ficar igual em qualquer
    sistema de arquivos e dentro de uma URL. A numeração que vem antes é que
    garante unicidade, então truncar aqui não cria colisão.
    """
    sem_acento = unicodedata.normalize("NFKD", titulo or "")
    ascii_puro = sem_acento.encode("ascii", "ignore").decode("ascii")
    limpo = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_puro).strip("-").lower()

    if len(limpo) > TAMANHO_DO_SLUG:
        cortado = limpo[:TAMANHO_DO_SLUG]
        # Volta até a última palavra inteira, para o nome não terminar num
        # pedaço de palavra. Só se ainda sobrar metade do limite.
        fronteira = cortado.rfind("-")
        if fronteira >= TAMANHO_DO_SLUG // 2:
            cortado = cortado[:fronteira]
        limpo = cortado

    return limpo.strip("-") or "passo"
