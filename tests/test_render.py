"""Testes do render: snapshot do desenho, determinismo e a regra da §9."""

from __future__ import annotations

import dataclasses

import pytest
from aa_diagram_export import model, render, resolver
from example_model import (
    CAMINHO_AUSENTE,
    bot_principal,
    bot_relatorio,
    dicionario_de_teste,
)


def _expandido():
    bots = [bot_principal(), bot_relatorio()]
    inventario = resolver.build_inventory(bots)
    return resolver.expand(bot_principal(), inventario, max_depth=3)


def test_diagrama_do_bot(snapshot):
    expandido, _ = _expandido()
    diagrama, _ = render.bot_diagram(expandido, dicionario_de_teste())
    snapshot("conciliacao_diaria.mmd", diagrama)


def test_pagina_do_bot(snapshot):
    expandido, _ = _expandido()
    dic = dicionario_de_teste()
    diagrama, _ = render.bot_diagram(expandido, dic)
    pagina = render.bot_page(bot_principal(), dic, diagram=diagrama, max_depth=3)
    snapshot("conciliacao_diaria.md", pagina)


def test_index(snapshot):
    dic = dicionario_de_teste()
    bots = sorted([bot_principal(), bot_relatorio()], key=lambda b: b.path)
    _, relatorio = _expandido()
    pagina = render.index_page(
        bots,
        dic,
        unresolved=relatorio.as_lists(),
        unknown_commands={"Excel advanced:SetCell", "Browser:Download"},
        ignored_files=2,
    )
    snapshot("index.md", pagina)


def test_render_e_deterministico():
    """Critério 7 de aceite da §12: rodar duas vezes dá o mesmo byte."""
    dic = dicionario_de_teste()
    primeiro, _ = render.bot_diagram(_expandido()[0], dic)
    segundo, _ = render.bot_diagram(_expandido()[0], dic)
    assert primeiro == segundo


def test_id_de_no_nao_depende_da_posicao():
    """O diff do git tem que ficar restrito ao que mudou (§7, IDs de nó)."""
    antes = model.ActionBlock("a1", commands=("Email:Send",))
    assert antes.node_id == model.ActionBlock("a1", commands=("Outro:Comando",)).node_id
    assert antes.node_id != model.ActionBlock("a2").node_id


def test_comandos_sem_rotulo_sao_reportados():
    expandido, _ = _expandido()
    _, faltantes = render.bot_diagram(expandido, dicionario_de_teste())
    assert "Excel advanced:SetCell" in faltantes
    assert "Browser:Download" in faltantes
    assert "Email:Send" not in faltantes


def test_bot_ausente_aparece_no_diagrama_e_no_grafo():
    expandido, relatorio = _expandido()
    diagrama, _ = render.bot_diagram(expandido, dicionario_de_teste())
    assert "não encontrado no export" in diagrama
    assert "Comum/Auditoria" in relatorio.unresolved

    grafo = render.call_graph(
        [bot_principal(), bot_relatorio()], dicionario_de_teste()
    )
    assert CAMINHO_AUSENTE in grafo


def test_estado_de_chamada_tem_forma_propria():
    expandido, _ = _expandido()
    diagrama, _ = render.bot_diagram(expandido, dicionario_de_teste())
    assert "recursão:" in diagrama
    assert "alvo dinâmico:" in diagrama
    assert "subgraph" in diagrama


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ('diz "oi"', "diz #quot;oi#quot;"),
        ("conta #1", "conta #35;1"),
        ("a\nb", "a b"),
        ("a | b", "a / b"),
        ("  espaços   demais ", "espaços demais"),
    ],
)
def test_escape(entrada, esperado):
    assert render.escape(entrada) == esperado


def test_escape_trunca():
    resultado = render.escape("x" * 200)
    assert len(resultado) == render.LIMITE_ROTULO
    assert resultado.endswith("…")


# --- guardas da §9: nenhum valor literal entra no modelo ---

CAMPOS_PROIBIDOS = {
    "value",
    "values",
    "literal",
    "param",
    "params",
    "parameters",
    "arguments",
    "args",
}


def test_modelo_nao_tem_campo_de_valor_literal():
    """Guarda deliberada da §9.

    Se alguém adicionar ao modelo um campo que carregue o valor configurado
    numa ação, este teste quebra. É assim que a regra de não vazar senha,
    token e caminho de rede para um arquivo versionado deixa de depender de
    alguém lembrar dela na revisão.
    """
    for nome in dir(model):
        classe = getattr(model, nome)
        if not dataclasses.is_dataclass(classe) or not isinstance(classe, type):
            continue
        campos = {campo.name for campo in dataclasses.fields(classe)}
        proibidos = campos & CAMPOS_PROIBIDOS
        assert not proibidos, f"{nome} carrega campo de valor literal: {proibidos}"


def test_bloco_de_acoes_so_guarda_nome_de_comando():
    campos = {campo.name for campo in dataclasses.fields(model.ActionBlock)}
    assert campos == {"uid", "commands", "label"}
