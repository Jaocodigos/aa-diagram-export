"""Modelo intermediário do fluxo de um bot — o IR descrito na §6.2 da spec.

São dataclasses imutáveis. Os únicos métodos que moram aqui são os que
respondem igual para qualquer renderer (`node_id`, `is_control_flow`), porque
são intrínsecos ao nó. Nada específico de Mermaid entra neste arquivo: é isso
que mantém a porta do DrawIO aberta (§6.1).

Nenhum nó guarda valor literal de parâmetro. Isso não é descuido, é a regra da
§9: o renderer nunca tem acesso ao valor configurado na ação, então senha,
token, URL interna e caminho de rede não têm por onde vazar para um arquivo
versionado.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum


def stable_node_id(seed: str) -> str:
    """ID de nó estável, derivado do uid da ação no A360.

    Hash em vez de índice sequencial: inserir uma ação no começo do bot não
    renumera o diagrama inteiro, então o diff no git fica restrito ao que
    mudou de fato (§7, "IDs de nó").
    """
    return "n" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]


@dataclass(frozen=True)
class Node:
    """Base dos nós: carrega o uid e o que se deriva dele."""

    uid: str

    @property
    def node_id(self) -> str:
        return stable_node_id(self.uid)

    def is_control_flow(self) -> bool:
        return True


@dataclass(frozen=True)
class ActionBlock(Node):
    """Sequência linear de ações colapsada num nó só (§5, granularidade).

    `commands` guarda os nomes no formato "Pacote:Comando" e `label` o texto
    que o dev escreveu no A360, quando existe. Nenhum valor de parâmetro.
    """

    commands: tuple[str, ...] = ()
    label: str | None = None

    def is_control_flow(self) -> bool:
        return False


@dataclass(frozen=True)
class Branch:
    """Um ramo de um If: a condição e o corpo que ela guarda."""

    condition: str
    body: tuple[Node, ...] = ()


@dataclass(frozen=True)
class If(Node):
    branches: tuple[Branch, ...] = ()
    else_body: tuple[Node, ...] = ()


class LoopKind(StrEnum):
    FOR_EACH = "for_each"
    N_TIMES = "n_times"
    WHILE = "while"


@dataclass(frozen=True)
class Loop(Node):
    kind: LoopKind = LoopKind.FOR_EACH
    expression: str = ""
    body: tuple[Node, ...] = ()


@dataclass(frozen=True)
class TryCatch(Node):
    try_body: tuple[Node, ...] = ()
    catch_body: tuple[Node, ...] = ()
    finally_body: tuple[Node, ...] = ()


@dataclass(frozen=True)
class Step(Node):
    """Agrupador do A360: não muda o fluxo, só organiza."""

    title: str = ""
    body: tuple[Node, ...] = ()


class CallState(StrEnum):
    """Por que uma chamada apareceu desse jeito no diagrama (§8)."""

    EXPANDED = "expanded"
    UNRESOLVED = "unresolved"
    CYCLE = "cycle"
    DEPTH_LIMIT = "depth_limit"
    DYNAMIC_TARGET = "dynamic_target"


@dataclass(frozen=True)
class CallBot(Node):
    """Chamada a outro bot. `body` só vem preenchido quando foi expandida."""

    target_path: str = ""
    state: CallState = CallState.UNRESOLVED
    body: tuple[Node, ...] = ()


@dataclass(frozen=True)
class Break(Node):
    pass


@dataclass(frozen=True)
class Continue(Node):
    pass


AnyNode = ActionBlock | If | Loop | TryCatch | Step | CallBot | Break | Continue


@dataclass(frozen=True)
class Variable:
    name: str
    type: str = ""
    is_input: bool = False
    is_output: bool = False


@dataclass(frozen=True)
class Bot:
    path: str
    name: str
    variables: tuple[Variable, ...] = ()
    packages: tuple[str, ...] = ()
    body: tuple[Node, ...] = ()


def walk(nodes: Iterable[Node]) -> Iterator[Node]:
    """Percorre a árvore em profundidade, na ordem do fluxo.

    Esta é a forma canônica de travessia do projeto: uma função recursiva com
    `match`, não um método por tipo de nó. A razão está na §6.1 — os tipos de
    nó são fechados, vêm da linguagem do A360, enquanto as operações sobre
    eles vão crescer.
    """
    for node in nodes:
        yield node
        match node:
            case If(branches=branches, else_body=else_body):
                for branch in branches:
                    yield from walk(branch.body)
                yield from walk(else_body)
            case Loop(body=body) | Step(body=body) | CallBot(body=body):
                yield from walk(body)
            case TryCatch(try_body=t, catch_body=c, finally_body=f):
                yield from walk(t)
                yield from walk(c)
                yield from walk(f)
            case _:
                pass


def called_bots(bot: Bot) -> tuple[str, ...]:
    """Caminhos dos bots chamados, na ordem em que aparecem, sem repetir.

    Atenção: chamar isto num bot já expandido pelo resolver devolve também as
    chamadas que vieram de dentro das subtarefas. O grafo de chamadas do
    index.md tem que ser montado a partir dos bots como saíram do parser.
    """
    found: list[str] = []
    for node in walk(bot.body):
        if isinstance(node, CallBot) and node.target_path not in found:
            found.append(node.target_path)
    return tuple(found)


def action_count(bot: Bot) -> int:
    """Quantas ações do A360 o bot tem, somando os blocos colapsados."""
    return sum(
        len(node.commands) for node in walk(bot.body) if isinstance(node, ActionBlock)
    )
