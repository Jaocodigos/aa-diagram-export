"""Testes da CLI: o pipeline inteiro, de um .zip até os .md na pasta."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest
from aa_diagram_export import __main__ as cli
from aa_diagram_export import config, render, resolver
from example_model import bot_principal, bot_relatorio
from test_parser import BOT, _acao

RAIZ = Path(__file__).resolve().parents[1]

CHAMADOR = "Automation Anywhere\\Bots\\Processos\\Exemplo"
CHAMADO = "Automation Anywhere\\Bots\\Comum\\Enviar"


def _export(tmp_path: Path) -> Path:
    """Um export mínimo com dois bots, um chamando o outro."""
    chamado = {"nodes": [_acao("a", "Email", "send")], "variables": [], "packages": []}
    manifesto = {
        "files": [
            {"path": CHAMADOR, "contentType": "application/vnd.aa.taskbot"},
            {"path": CHAMADO, "contentType": "application/vnd.aa.taskbot"},
        ]
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("manifest.json", json.dumps(manifesto))
        z.writestr(CHAMADOR, json.dumps(BOT))
        z.writestr(CHAMADO, json.dumps(chamado))
        z.writestr("bot-command-if.jar", b"PK-falso")
    destino = tmp_path / "export.zip"
    destino.write_bytes(buffer.getvalue())
    return destino


def test_ponta_a_ponta(tmp_path, capsys):
    saida = tmp_path / "docs"
    codigo = cli.main([
        "--input", str(_export(tmp_path)),
        "--out", str(saida),
        "--dicionario", str(RAIZ / "dicionario.toml"),
    ])
    assert codigo == 0

    index = (saida / "index.md").read_text(encoding="utf-8")
    assert "Grafo de chamadas" in index
    assert "2 bot(s) no export" in index

    pagina = (saida / "Exemplo" / "README.md").read_text(encoding="utf-8")
    assert "```mermaid" in pagina
    # A chamada foi resolvida e expandida, então o bot chamado está no desenho.
    assert "Bot: Comum/Enviar" in pagina
    assert (saida / "Enviar" / "README.md").is_file()


def test_rodar_duas_vezes_da_o_mesmo_byte(tmp_path):
    """Critério 7 de aceite da §12, agora de ponta a ponta."""
    export = _export(tmp_path)
    argumentos = ["--input", str(export), "--dicionario", str(RAIZ / "dicionario.toml")]

    primeira, segunda = tmp_path / "a", tmp_path / "b"
    cli.main([*argumentos, "--out", str(primeira), "--quiet"])
    cli.main([*argumentos, "--out", str(segunda), "--quiet"])

    arquivos = sorted(p.relative_to(primeira) for p in primeira.rglob("*.md"))
    assert arquivos
    for relativo in arquivos:
        assert (primeira / relativo).read_bytes() == (segunda / relativo).read_bytes()


def test_sem_grafo_de_chamadas(tmp_path):
    saida = tmp_path / "docs"
    cli.main([
        "--input", str(_export(tmp_path)), "--out", str(saida),
        "--no-call-graph", "--quiet",
    ])
    assert "Grafo de chamadas" not in (saida / "index.md").read_text(encoding="utf-8")


def test_entrada_inexistente_sai_com_erro(tmp_path, capsys):
    codigo = cli.main(["--input", str(tmp_path / "nada.zip"), "--out", str(tmp_path / "o")])
    assert codigo == 2
    assert "erro na entrada" in capsys.readouterr().err


def test_secoes_viram_arquivos_proprios(tmp_path):
    """Cada passo detalhado é um .md numa pasta irmã, não um trecho da página."""
    # Ação linear colapsa em bloco: sem os comentários separando, as dez
    # viriam num nó só e não haveria o que quebrar.
    miolo: list[dict] = []
    for i in range(10):
        miolo.append(_acao(f"c{i}", "Comment", "Comment", attributes=[
            {"name": "comment", "value": {"type": "STRING", "string": f"Parte {i}"}}
        ]))
        miolo.append(_acao(f"a{i}", "String", "assign"))

    passo = _acao("s1", "Step", "step",
                  attributes=[{"name": "title", "value": {"type": "STRING", "string": "Passo Longo"}}],
                  children=miolo)
    bot = {"nodes": [passo], "variables": [], "packages": []}
    manifesto = {"files": [{"path": CHAMADOR, "contentType": "application/vnd.aa.taskbot"}]}

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("manifest.json", json.dumps(manifesto))
        z.writestr(CHAMADOR, json.dumps(bot))
    export = tmp_path / "export.zip"
    export.write_bytes(buffer.getvalue())

    saida = tmp_path / "docs"
    assert cli.main([
        "--input", str(export), "--out", str(saida),
        "--node-budget", "6", "--quiet",
    ]) == 0

    pagina = saida / "Exemplo" / "README.md"
    secao = saida / "Exemplo" / "Subtasks" / "01-passo-longo.md"
    assert pagina.is_file() and secao.is_file()

    texto_da_pagina = pagina.read_text(encoding="utf-8")
    assert "Subtasks/01-passo-longo.md" in texto_da_pagina
    assert texto_da_pagina.count("```mermaid") == 1

    texto_da_secao = secao.read_text(encoding="utf-8")
    assert "](../README.md)" in texto_da_secao
    assert texto_da_secao.count("```mermaid") == 1


# --- orçamento de arestas ---


def test_reduz_profundidade_para_caber_no_mermaid(monkeypatch):
    """O Mermaid recusa mais de 500 arestas, então a expansão cede nível.

    Entregar o diagrama completo seria entregar um arquivo que não aparece
    para ninguém no GitHub.
    """
    monkeypatch.setattr(render, "LIMITE_DE_ARESTAS", 3)
    inventario = resolver.build_inventory([bot_principal(), bot_relatorio()])

    _, _, usada = cli._expandir_dentro_do_limite(
        bot_principal(), inventario, config.Dictionary(), 3
    )
    assert usada < 3


def test_nao_reduz_quando_cabe(monkeypatch):
    monkeypatch.setattr(render, "LIMITE_DE_ARESTAS", 10_000)
    inventario = resolver.build_inventory([bot_principal(), bot_relatorio()])

    _, _, usada = cli._expandir_dentro_do_limite(
        bot_principal(), inventario, config.Dictionary(), 3
    )
    assert usada == 3


def test_profundidade_zero_sempre_entrega_algo(monkeypatch):
    """Mesmo um bot sozinho grande demais sai com diagrama, mais o aviso."""
    monkeypatch.setattr(render, "LIMITE_DE_ARESTAS", 0)
    inventario = resolver.build_inventory([bot_principal()])
    expandido, _, usada = cli._expandir_dentro_do_limite(
        bot_principal(), inventario, config.Dictionary(), 3
    )
    assert usada == 0
    desenho = render.bot_diagram(expandido, config.Dictionary())
    assert desenho.mermaid.startswith("flowchart TD")
    assert desenho.too_big


# --- bibliotecas ---


def _dicionario_com_biblioteca(tmp_path: Path) -> Path:
    caminho = tmp_path / "dic.toml"
    caminho.write_text(
        '[geral]\nbibliotecas = ["Comum/**"]\n', encoding="utf-8"
    )
    return caminho


def test_biblioteca_nao_ganha_pagina_mas_e_mencionada(tmp_path):
    saida = tmp_path / "docs"
    codigo = cli.main([
        "--input", str(_export(tmp_path)),
        "--out", str(saida),
        "--dicionario", str(_dicionario_com_biblioteca(tmp_path)),
        "--quiet",
    ])
    assert codigo == 0

    assert not (saida / "Enviar" / "README.md").exists()
    assert (saida / "Exemplo" / "README.md").is_file()

    pagina = (saida / "Exemplo" / "README.md").read_text(encoding="utf-8")
    assert "Comum/Enviar" in pagina, "a chamada tem que continuar mencionada no fluxo"
    assert "Bot: Comum/Enviar" not in pagina, "biblioteca não pode ser expandida"

    index = (saida / "index.md").read_text(encoding="utf-8")
    assert "1 bot(s) no export" in index
    assert "padrões de biblioteca" in index


def test_biblioteca_nao_vira_pendencia(tmp_path):
    """Sem estado próprio, cada chamada a um utilitário viraria alarme falso."""
    saida = tmp_path / "docs"
    cli.main([
        "--input", str(_export(tmp_path)), "--out", str(saida),
        "--dicionario", str(_dicionario_com_biblioteca(tmp_path)), "--quiet",
    ])
    index = (saida / "index.md").read_text(encoding="utf-8")
    assert "não encontrado" not in index


def test_tabela_de_chamadas_traz_parametros(tmp_path):
    saida = tmp_path / "docs"
    cli.main([
        "--input", str(_export(tmp_path)), "--out", str(saida),
        "--dicionario", str(_dicionario_com_biblioteca(tmp_path)), "--quiet",
    ])
    pagina = (saida / "Exemplo" / "README.md").read_text(encoding="utf-8")
    assert "## Chamadas" in pagina
    assert "| Bot | Direção | Parâmetro | Tipo | Variável no chamador |" in pagina
