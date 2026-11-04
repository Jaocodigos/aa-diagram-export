"""Expande as chamadas Run Task, com proteção de ciclo e profundidade (§8).

Opera só sobre o modelo, então não depende do formato do export — a única
costura dependente de formato é a comparação de caminhos, que mora em
`paths.py`.

A travessia reconstrói a árvore em vez de mutá-la, porque o modelo é imutável:
cada nó visitado devolve um nó novo com o corpo já expandido.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from . import paths
from .model import (
    ActionBlock,
    Bot,
    Branch,
    Break,
    CallBot,
    CallState,
    Continue,
    If,
    Loop,
    Node,
    Step,
    TryCatch,
)


@dataclass
class ResolveReport:
    """O que a expansão encontrou pelo caminho, para o relatório do index.md."""

    unresolved: dict[str, set[str]] = field(default_factory=dict)
    cycles: set[str] = field(default_factory=set)
    depth_limited: set[str] = field(default_factory=set)
    dynamic: set[str] = field(default_factory=set)

    def add_unresolved(self, alvo: str, quem_chamou: str) -> None:
        self.unresolved.setdefault(alvo, set()).add(quem_chamou)

    def as_lists(self) -> dict[str, list[str]]:
        """Versão ordenada, para o render montar a seção de pendências."""
        return {alvo: sorted(quem) for alvo, quem in sorted(self.unresolved.items())}


def build_inventory(bots: list[Bot]) -> dict[str, Bot]:
    """Indexa os bots pelo caminho canônico, para o resolver procurar."""
    return {paths.normalize(bot.path): bot for bot in bots}


def expand(
    bot: Bot,
    inventory: dict[str, Bot],
    *,
    max_depth: int = 3,
    report: ResolveReport | None = None,
) -> tuple[Bot, ResolveReport]:
    """Devolve o bot com as subtarefas expandidas inline, mais o relatório."""
    report = report if report is not None else ResolveReport()
    corpo = _expand_body(
        bot.body,
        inventory=inventory,
        max_depth=max_depth,
        chain=(paths.normalize(bot.path),),
        caller=bot.path,
        report=report,
    )
    return replace(bot, body=corpo), report


def _expand_body(
    nodes: tuple[Node, ...],
    *,
    inventory: dict[str, Bot],
    max_depth: int,
    chain: tuple[str, ...],
    caller: str,
    report: ResolveReport,
) -> tuple[Node, ...]:
    recursao = dict(
        inventory=inventory,
        max_depth=max_depth,
        chain=chain,
        caller=caller,
        report=report,
    )
    saida: list[Node] = []

    for node in nodes:
        match node:
            case CallBot():
                saida.append(_expand_call(node, **recursao))
            case If(branches=branches, else_body=else_body):
                ramos = tuple(
                    Branch(
                        condition=branch.condition,
                        body=_expand_body(branch.body, **recursao),
                    )
                    for branch in branches
                )
                saida.append(
                    replace(
                        node,
                        branches=ramos,
                        else_body=_expand_body(else_body, **recursao),
                    )
                )
            case Loop(body=body) | Step(body=body):
                saida.append(replace(node, body=_expand_body(body, **recursao)))
            case TryCatch(try_body=t, catch_body=c, finally_body=f):
                saida.append(
                    replace(
                        node,
                        try_body=_expand_body(t, **recursao),
                        catch_body=_expand_body(c, **recursao),
                        finally_body=_expand_body(f, **recursao),
                    )
                )
            case ActionBlock() | Break() | Continue():
                saida.append(node)
            case _:
                saida.append(node)

    return tuple(saida)


def _expand_call(
    call: CallBot,
    *,
    inventory: dict[str, Bot],
    max_depth: int,
    chain: tuple[str, ...],
    caller: str,
    report: ResolveReport,
) -> CallBot:
    """Decide o estado de uma chamada, na ordem de precedência da §8."""
    if paths.is_dynamic(call.target_path):
        report.dynamic.add(call.target_path)
        return replace(call, state=CallState.DYNAMIC_TARGET, body=())

    alvo = paths.normalize(call.target_path)

    if alvo in chain:
        report.cycles.add(alvo)
        return replace(call, state=CallState.CYCLE, body=())

    if alvo not in inventory:
        report.add_unresolved(alvo, caller)
        return replace(call, state=CallState.UNRESOLVED, body=())

    # profundidade já aplicada = quantos bots entraram na cadeia depois da raiz
    if len(chain) - 1 >= max_depth:
        report.depth_limited.add(alvo)
        return replace(call, state=CallState.DEPTH_LIMIT, body=())

    chamado = inventory[alvo]
    corpo = _expand_body(
        chamado.body,
        inventory=inventory,
        max_depth=max_depth,
        chain=chain + (alvo,),
        caller=chamado.path,
        report=report,
    )
    return replace(call, state=CallState.EXPANDED, body=corpo)
