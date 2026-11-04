"""Testes da costura de caminhos (paths.py) e da leitura do dicionario.toml."""

from __future__ import annotations

from pathlib import Path

import pytest
from aa_diagram_export import config, paths

RAIZ = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("bruto", "esperado"),
    [
        ("Bots/Financeiro/X", "Financeiro/X"),
        (r"Bots\Financeiro\X", "Financeiro/X"),
        ("/Bots/Financeiro/X.json", "Financeiro/X"),
        ("Bots//Financeiro//X", "Financeiro/X"),
        ("  Financeiro/X.atmx  ", "Financeiro/X"),
        ("Financeiro/X", "Financeiro/X"),
    ],
)
def test_normalize(bruto, esperado):
    assert paths.normalize(bruto) == esperado


def test_normalize_e_idempotente():
    uma_vez = paths.normalize("Bots/Financeiro/X.json")
    assert paths.normalize(uma_vez) == uma_vez


@pytest.mark.parametrize(
    ("bruto", "esperado"),
    [("Bots/$sNome$", True), ("Bots/Fixo", False)],
)
def test_is_dynamic(bruto, esperado):
    assert paths.is_dynamic(bruto) is esperado


def test_looks_like_bot_file():
    assert paths.looks_like_bot_file("ConciliacaoDiaria.json")
    assert paths.looks_like_bot_file("Antigo.ATMX")
    assert not paths.looks_like_bot_file("manifest.xml")


def test_dicionario_do_repo_e_valido():
    """O dicionario.toml que vai pro git tem que parsear e ter as seções."""
    dic = config.load(RAIZ / "dicionario.toml")
    assert dic.max_depth == 3
    assert dic.friendly("Excel advanced:Open") == "Excel: abrir planilha"
    assert "If" in dic.control_packages
    assert "controle" in dic.style


def test_padroes_quando_nao_ha_arquivo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    dic = config.load()
    assert dic.max_depth == 3
    assert dic.friendly("qualquer:coisa") is None


def test_arquivo_pedido_e_inexistente_falha(tmp_path):
    with pytest.raises(FileNotFoundError):
        config.load(tmp_path / "nao_existe.toml")


def test_toml_invalido_da_mensagem_clara(tmp_path):
    ruim = tmp_path / "dicionario.toml"
    ruim.write_text("[geral\nprofundidade = 1", encoding="utf-8")
    with pytest.raises(ValueError, match="sintaxe TOML"):
        config.load(ruim)
