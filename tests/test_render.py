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


def _desenho():
    return render.bot_diagram(_expandido()[0], dicionario_de_teste())


def test_diagrama_do_bot(snapshot):
    snapshot("conciliacao_diaria.mmd", _desenho().mermaid)


def test_pagina_do_bot(snapshot):
    pagina = render.bot_page(
        bot_principal(),
        dicionario_de_teste(),
        diagram=_desenho(),
        depth_used=3,
        depth_requested=3,
    )
    snapshot("conciliacao_diaria.md", pagina)


def test_index(snapshot):
    _, relatorio = _expandido()
    pagina = render.index_page(
        sorted([bot_principal(), bot_relatorio()], key=lambda b: b.path),
        dicionario_de_teste(),
        unresolved=relatorio.as_lists(),
        unknown_commands={"Excel advanced:SetCell", "Browser:Download"},
        ignored_files=2,
    )
    snapshot("index.md", pagina)


def test_render_e_deterministico():
    """Critério 7 de aceite da §12: rodar duas vezes dá o mesmo byte."""
    assert _desenho().mermaid == _desenho().mermaid


def test_id_de_no_nao_depende_da_posicao():
    """O diff do git tem que ficar restrito ao que mudou (§7, IDs de nó)."""
    antes = model.ActionBlock("a1", commands=("Email:Send",))
    assert antes.node_id == model.ActionBlock("a1", commands=("Outro:Comando",)).node_id
    assert antes.node_id != model.ActionBlock("a2").node_id


def test_comandos_sem_rotulo_sao_reportados():
    faltantes = _desenho().unknown_commands
    assert "Excel advanced:SetCell" in faltantes
    assert "Browser:Download" in faltantes
    assert "Email:Send" not in faltantes


def test_rotulo_do_dev_nao_gera_pendencia():
    """Bloco nomeado pelo dev não mostra nome de comando, logo nada a cadastrar."""
    dic = dicionario_de_teste()
    bot = model.Bot(
        path="X",
        name="X",
        body=(model.ActionBlock("a", commands=("Sem:Rotulo",), label="Passo nomeado"),),
    )
    assert render.bot_diagram(bot, dic).unknown_commands == frozenset()


def test_bot_ausente_aparece_no_diagrama_e_no_grafo():
    _, relatorio = _expandido()
    assert "não encontrado no export" in _desenho().mermaid
    assert "Comum/Auditoria" in relatorio.unresolved

    grafo = render.call_graph([bot_principal(), bot_relatorio()], dicionario_de_teste())
    assert CAMINHO_AUSENTE in grafo


def test_estado_de_chamada_tem_forma_propria():
    mermaid = _desenho().mermaid
    assert "recursão:" in mermaid
    assert "alvo dinâmico:" in mermaid
    assert "subgraph" in mermaid


# --- limite de arestas do Mermaid ---


def test_conta_arestas():
    desenho = _desenho()
    arestas = [
        linha
        for linha in desenho.mermaid.splitlines()
        if "-->" in linha or "-.->" in linha
    ]
    assert desenho.edge_count == len(arestas)


def test_too_big_usa_o_limite(monkeypatch):
    monkeypatch.setattr(render, "LIMITE_DE_ARESTAS", 1)
    assert _desenho().too_big
    monkeypatch.setattr(render, "LIMITE_DE_ARESTAS", 10_000)
    assert not _desenho().too_big


def test_pagina_avisa_quando_reduziu():
    pagina = render.bot_page(
        bot_principal(),
        dicionario_de_teste(),
        diagram=_desenho(),
        depth_used=1,
        depth_requested=3,
    )
    assert "Expandido até a profundidade 1" in pagina
    assert "| Profundidade de expansão | 1 |" in pagina


def test_index_lista_bots_reduzidos():
    pagina = render.index_page(
        [bot_principal()],
        dicionario_de_teste(),
        depth_reduced={"Bots/X": (1, 3)},
    )
    assert "Bots com expansão reduzida" in pagina
    assert "expandido até 1, e não 3" in pagina


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
