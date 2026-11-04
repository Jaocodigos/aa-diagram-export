"""Testes da expansão inline das subtarefas (§8)."""

from __future__ import annotations

from aa_diagram_export import resolver
from aa_diagram_export.model import CallBot, CallState, walk
from example_model import (
    CAMINHO_PRINCIPAL,
    CAMINHO_RELATORIO,
    bot_principal,
    bot_relatorio,
    corrente_de_bots,
)


def _chamadas(bot) -> dict[str, CallState]:
    return {
        node.target_path: node.state
        for node in walk(bot.body)
        if isinstance(node, CallBot)
    }


def _expandir(max_depth: int = 3):
    bots = [bot_principal(), bot_relatorio()]
    inventario = resolver.build_inventory(bots)
    return resolver.expand(bot_principal(), inventario, max_depth=max_depth)


def test_subtarefa_presente_e_expandida():
    expandido, _ = _expandir()
    assert _chamadas(expandido)[CAMINHO_RELATORIO] is CallState.EXPANDED
    chamada = next(
        node
        for node in walk(expandido.body)
        if isinstance(node, CallBot) and node.target_path == CAMINHO_RELATORIO
    )
    assert chamada.body, "a chamada expandida tem que trazer o corpo do bot chamado"


def test_ciclo_nao_recursa_infinitamente():
    """O bot chamado chama o chamador de volta (§8, item 3)."""
    expandido, relatorio = _expandir()
    assert _chamadas(expandido)[CAMINHO_PRINCIPAL] is CallState.CYCLE
    assert "Financeiro/ConciliacaoDiaria" in relatorio.cycles


def test_bot_fora_do_export_fica_nao_resolvido():
    expandido, relatorio = _expandir()
    assert _chamadas(expandido)["Bots/Comum/Auditoria"] is CallState.UNRESOLVED
    assert relatorio.as_lists() == {
        "Comum/Auditoria": [CAMINHO_PRINCIPAL],
    }


def test_alvo_dinamico_nao_e_resolvido():
    expandido, relatorio = _expandir()
    assert _chamadas(expandido)["Bots/Comum/$sBotDinamico$"] is CallState.DYNAMIC_TARGET
    assert relatorio.dynamic == {"Bots/Comum/$sBotDinamico$"}


def test_limite_de_profundidade():
    bots = corrente_de_bots(5)
    inventario = resolver.build_inventory(bots)
    expandido, relatorio = resolver.expand(bots[0], inventario, max_depth=2)

    estados = [
        node.state for node in walk(expandido.body) if isinstance(node, CallBot)
    ]
    assert estados.count(CallState.EXPANDED) == 2
    assert CallState.DEPTH_LIMIT in estados
    assert relatorio.depth_limited


def test_expansao_nao_muta_o_original():
    """O modelo é imutável: a expansão reconstrói a árvore."""
    original = bot_principal()
    bots = [original, bot_relatorio()]
    resolver.expand(original, resolver.build_inventory(bots), max_depth=3)
    assert _chamadas(original)[CAMINHO_RELATORIO] is CallState.UNRESOLVED
    assert original == bot_principal()
