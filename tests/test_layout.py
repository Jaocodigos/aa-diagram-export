"""Testes da quebra de um bot grande em seções (§8.2)."""

from __future__ import annotations

from aa_diagram_export import layout, render
from aa_diagram_export.config import Dictionary
from aa_diagram_export.model import ActionBlock, Bot, If, Branch, Step


def _acoes(prefixo: str, quantidade: int) -> tuple[ActionBlock, ...]:
    return tuple(
        ActionBlock(f"{prefixo}{i}", commands=("Pacote:comando",))
        for i in range(quantidade)
    )


def _bot_com_passo_grande(tamanho: int = 12) -> Bot:
    return Bot(
        path="Processos/Grande",
        name="Grande",
        body=(
            ActionBlock("topo", commands=("Pacote:comando",)),
            Step("s1", title="Passo grande", body=_acoes("g", tamanho)),
            ActionBlock("base", commands=("Pacote:comando",)),
        ),
    )


def test_bot_pequeno_nao_quebra():
    bot = Bot(path="P", name="P", body=_acoes("a", 3))
    resultado = layout.split_bot(bot, Dictionary(), budget=30)
    assert resultado.sections == ()


def test_passo_grande_vira_secao():
    resultado = layout.split_bot(_bot_com_passo_grande(), Dictionary(), budget=8)
    assert len(resultado.sections) == 1

    secao = resultado.sections[0]
    assert secao.title == "Passo grande"
    assert secao.anchor.startswith("secao-")
    # O principal encolheu: o Step virou um nó só.
    assert resultado.diagram.node_count <= 8
    assert secao.diagram.node_count > 8


def test_o_principal_referencia_a_secao():
    resultado = layout.split_bot(_bot_com_passo_grande(), Dictionary(), budget=8)
    mermaid = resultado.diagram.mermaid
    assert "Passo grande" in mermaid
    assert "subgraph" not in mermaid, "o Step externalizado não é mais desenhado"
    # O click é bônus: o GitHub usa securityLevel strict e o ignora. A
    # navegação confiável são os links Markdown que a página escreve.
    assert f'click ' in mermaid
    assert resultado.sections[0].anchor in mermaid


def test_passo_pequeno_demais_nao_vira_secao():
    """Seção que economiza quase nada só custa um salto de navegação."""
    bot = Bot(
        path="P",
        name="P",
        body=(*_acoes("a", 20), Step("s", title="Mínimo", body=_acoes("b", 2))),
    )
    resultado = layout.split_bot(bot, Dictionary(), budget=5)
    assert resultado.sections == ()


def test_sem_candidato_entrega_o_diagrama_inteiro():
    """Bot sem Step nenhum não tem onde cortar: sai grande, mas sai."""
    bot = Bot(path="P", name="P", body=_acoes("a", 40))
    resultado = layout.split_bot(bot, Dictionary(), budget=5)
    assert resultado.sections == ()
    assert resultado.diagram.node_count > 5


def test_quebra_recursiva():
    """Seção que ainda passa do orçamento quebra de novo."""
    interno = Step("dentro", title="Parte interna", body=_acoes("i", 10))
    bot = Bot(
        path="P",
        name="P",
        body=(
            ActionBlock("topo", commands=("Pacote:comando",)),
            Step("fora", title="Parte externa", body=(*_acoes("e", 8), interno)),
        ),
    )
    resultado = layout.split_bot(bot, Dictionary(), budget=8)
    titulos = {s.title for s in resultado.sections}
    assert titulos == {"Parte externa", "Parte interna"}


def test_step_dentro_de_if_tambem_e_candidato():
    bot = Bot(
        path="P",
        name="P",
        body=(
            If(
                "i1",
                branches=(
                    Branch("x", (Step("s", title="Dentro do se", body=_acoes("d", 12)),)),
                ),
            ),
        ),
    )
    resultado = layout.split_bot(bot, Dictionary(), budget=8)
    assert [s.title for s in resultado.sections] == ["Dentro do se"]


def test_ancora_vem_do_uid_e_nao_do_titulo():
    """Dois Steps com o mesmo título não podem colidir de âncora."""
    a = Step("uid-a", title="Mesmo nome", body=_acoes("a", 12))
    b = Step("uid-b", title="Mesmo nome", body=_acoes("b", 12))
    bot = Bot(path="P", name="P", body=(a, b))
    resultado = layout.split_bot(bot, Dictionary(), budget=8)
    ancoras = {s.anchor for s in resultado.sections}
    assert len(ancoras) == len(resultado.sections) == 2


def test_secoes_entram_na_pagina_com_ancora_explicita():
    resultado = layout.split_bot(_bot_com_passo_grande(), Dictionary(), budget=8)
    pagina = render.bot_page(
        _bot_com_passo_grande(),
        Dictionary(),
        diagram=resultado.diagram,
        sections=resultado.sections,
        depth_used=3,
    )
    ancora = resultado.sections[0].anchor
    assert f'<a id="{ancora}"></a>' in pagina
    assert f"](#{ancora})" in pagina, "o atalho em Markdown é a navegação confiável"
    assert pagina.count("```mermaid") == 2
