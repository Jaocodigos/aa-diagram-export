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


def test_passo_grande_vira_arquivo():
    resultado = layout.split_bot(_bot_com_passo_grande(), Dictionary(), budget=8)
    assert len(resultado.sections) == 1

    secao = resultado.sections[0]
    assert secao.title == "Passo grande"
    assert secao.filename == "01-passo-grande.md"
    # O principal encolheu: o Step virou um nó só.
    assert resultado.diagram.node_count <= 8
    assert secao.diagram.node_count > 8


def test_o_principal_referencia_o_arquivo_da_secao():
    bot = _bot_com_passo_grande()
    resultado = layout.split_bot(bot, Dictionary(), budget=8)
    mermaid = resultado.diagram.mermaid
    assert "Passo grande" in mermaid
    assert "subgraph" not in mermaid, "o Step externalizado não é mais desenhado"
    # O click é bônus: o GitHub usa securityLevel strict e o ignora. A
    # navegação confiável são os links Markdown que a página escreve.
    assert f'click ' in mermaid
    assert f"{render.sections_dirname(bot)}/01-passo-grande.md" in mermaid


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


def test_titulos_iguais_nao_colidem_de_arquivo():
    """A numeração é o que garante unicidade quando dois Steps têm o mesmo nome."""
    bot = Bot(
        path="P",
        name="P",
        body=(
            Step("uid-a", title="Mesmo nome", body=_acoes("a", 12)),
            Step("uid-b", title="Mesmo nome", body=_acoes("b", 12)),
        ),
    )
    resultado = layout.split_bot(bot, Dictionary(), budget=8)
    arquivos = {s.filename for s in resultado.sections}
    assert len(arquivos) == len(resultado.sections) == 2
    assert arquivos == {"01-mesmo-nome.md", "02-mesmo-nome.md"}


def test_numeracao_segue_a_ordem_de_leitura():
    """A extração é gulosa, por tamanho; os arquivos saem na ordem do fluxo."""
    bot = Bot(
        path="P",
        name="P",
        body=(
            Step("primeiro", title="Primeiro passo", body=_acoes("p", 6)),
            Step("segundo", title="Segundo passo", body=_acoes("s", 20)),
        ),
    )
    resultado = layout.split_bot(bot, Dictionary(), budget=8)
    assert [s.filename for s in resultado.sections] == [
        "01-primeiro-passo.md",
        "02-segundo-passo.md",
    ]


def test_pagina_do_bot_lista_os_arquivos():
    bot = _bot_com_passo_grande()
    resultado = layout.split_bot(bot, Dictionary(), budget=8)
    pagina = render.bot_page(
        bot,
        Dictionary(),
        diagram=resultado.diagram,
        sections=resultado.sections,
        depth_used=3,
    )
    assert "## Passos detalhados" in pagina
    assert f"]({render.sections_dirname(bot)}/01-passo-grande.md)" in pagina
    assert pagina.count("```mermaid") == 1, "a seção não fica mais no mesmo arquivo"


def test_pagina_da_secao_tem_volta_e_vizinhos():
    bot = Bot(
        path="Processos/Grande",
        name="Grande",
        body=(
            Step("a", title="Passo um", body=_acoes("a", 12)),
            Step("b", title="Passo dois", body=_acoes("b", 12)),
            Step("c", title="Passo tres", body=_acoes("c", 12)),
        ),
    )
    resultado = layout.split_bot(bot, Dictionary(), budget=8)
    meio = resultado.sections[1]
    pagina = render.section_page(
        meio,
        bot,
        previous=resultado.sections[0],
        following=resultado.sections[2],
    )
    assert pagina.startswith("# Passo dois")
    assert "](../Grande.md)" in pagina
    assert "](01-passo-um.md)" in pagina
    assert "](03-passo-tres.md)" in pagina


def test_primeira_secao_nao_tem_anterior():
    bot = _bot_com_passo_grande()
    resultado = layout.split_bot(bot, Dictionary(), budget=8)
    pagina = render.section_page(resultado.sections[0], bot)
    assert "←" not in pagina.split("```")[-1]


def test_caminho_do_arquivo_da_secao():
    bot = _bot_com_passo_grande()
    resultado = layout.split_bot(bot, Dictionary(), budget=8)
    caminho = render.section_relpath(bot, resultado.sections[0])
    assert caminho == "bots/Processos/Grande/01-passo-grande.md"
