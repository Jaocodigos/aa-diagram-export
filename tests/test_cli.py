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

    pagina = (saida / "bots" / "Processos" / "Exemplo.md").read_text(encoding="utf-8")
    assert "```mermaid" in pagina
    # A chamada foi resolvida e expandida, então o bot chamado está no desenho.
    assert "Bot: Comum/Enviar" in pagina
    assert (saida / "bots" / "Comum" / "Enviar.md").is_file()


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


# --- orçamento de arestas ---


def test_reduz_profundidade_para_caber_no_mermaid(monkeypatch):
    """O Mermaid recusa mais de 500 arestas, então o render cede profundidade.

    Entregar o diagrama completo seria entregar um arquivo que não aparece
    para ninguém no GitHub.
    """
    monkeypatch.setattr(render, "LIMITE_DE_ARESTAS", 3)
    bots = [bot_principal(), bot_relatorio()]
    inventario = resolver.build_inventory(bots)

    diagrama, _, usada = cli._desenhar_dentro_do_limite(
        bot_principal(), inventario, config.Dictionary(), 3
    )
    assert usada < 3


def test_nao_reduz_quando_cabe(monkeypatch):
    monkeypatch.setattr(render, "LIMITE_DE_ARESTAS", 10_000)
    bots = [bot_principal(), bot_relatorio()]
    inventario = resolver.build_inventory(bots)

    _, _, usada = cli._desenhar_dentro_do_limite(
        bot_principal(), inventario, config.Dictionary(), 3
    )
    assert usada == 3


def test_profundidade_zero_sempre_entrega_algo(monkeypatch):
    """Mesmo um bot sozinho grande demais sai com diagrama, mais o aviso."""
    monkeypatch.setattr(render, "LIMITE_DE_ARESTAS", 0)
    inventario = resolver.build_inventory([bot_principal()])
    diagrama, _, usada = cli._desenhar_dentro_do_limite(
        bot_principal(), inventario, config.Dictionary(), 3
    )
    assert usada == 0
    assert diagrama.mermaid.startswith("flowchart TD")
    assert diagrama.too_big
