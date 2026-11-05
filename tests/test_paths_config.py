"""Testes da costura de caminhos, da leitura do dicionário e do loader."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest
from aa_diagram_export import config, loader, paths

RAIZ = Path(__file__).resolve().parents[1]

# As duas formas em que o mesmo bot aparece num export real do A360.
NO_MANIFEST = "Automation Anywhere\\Bots\\CommonTask\\Log\\GravarLogBanco"
NO_RUN_TASK = "repository:///Automation%20Anywhere/Bots/CommonTask/Log/GravarLogBanco"
CANONICO = "CommonTask/Log/GravarLogBanco"


@pytest.mark.parametrize(
    ("bruto", "esperado"),
    [
        (NO_MANIFEST, CANONICO),
        (NO_RUN_TASK, CANONICO),
        ("Bots/Financeiro/X", "Financeiro/X"),
        ("/Bots/Financeiro/X.json", "Financeiro/X"),
        ("Bots//Financeiro//X", "Financeiro/X"),
        ("  Financeiro/X.atmx  ", "Financeiro/X"),
        ("Financeiro/X", "Financeiro/X"),
        ("", ""),
    ],
)
def test_normalize(bruto, esperado):
    assert paths.normalize(bruto) == esperado


def test_as_duas_formas_do_export_casam():
    """Sem isto, todo runTask viraria 'bot não encontrado'."""
    assert paths.normalize(NO_MANIFEST) == paths.normalize(NO_RUN_TASK)


def test_normalize_e_idempotente():
    uma_vez = paths.normalize(NO_RUN_TASK)
    assert paths.normalize(uma_vez) == uma_vez


@pytest.mark.parametrize(
    ("bruto", "esperado"), [("Bots/$sNome$", True), ("Bots/Fixo", False), ("", False)]
)
def test_is_dynamic(bruto, esperado):
    assert paths.is_dynamic(bruto) is esperado


def test_bot_name():
    assert paths.bot_name(CANONICO) == "GravarLogBanco"


# --- loader ---


def _bot_minimo(nome: str) -> bytes:
    return json.dumps({"nodes": [], "variables": [], "packages": []}).encode()


def _zip_de_export(entradas: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for nome, conteudo in entradas.items():
            z.writestr(nome, conteudo)
    return buffer.getvalue()


def test_loader_usa_o_manifest(tmp_path):
    """Bot do A360 não tem extensão: quem diz o que é bot é o contentType."""
    manifesto = {
        "files": [
            {"path": NO_MANIFEST, "contentType": "application/vnd.aa.taskbot"},
            {"path": "Automation Anywhere\\Bots\\x.py", "contentType": "text/x-python"},
        ]
    }
    bruto = _zip_de_export({
        "manifest.json": json.dumps(manifesto).encode(),
        NO_MANIFEST: _bot_minimo("GravarLogBanco"),
        "Automation Anywhere\\Bots\\x.py": b"print('oi')",
        "bot-command-if-3.8.0.jar": b"PK-falso",
    })
    caminho = tmp_path / "export.zip"
    caminho.write_bytes(bruto)

    export = loader.load_export(caminho)
    assert export.used_manifest
    assert [b.logical_path for b in export.files] == [CANONICO]
    assert export.ignored == 3


def test_loader_sem_manifest_reconhece_por_conteudo(tmp_path):
    bruto = _zip_de_export({
        "Bots/Um": _bot_minimo("Um"),
        "Bots/leiame.txt": b"nao sou json",
        "pacote.jar": b"PK-falso",
    })
    caminho = tmp_path / "export.zip"
    caminho.write_bytes(bruto)

    export = loader.load_export(caminho)
    assert not export.used_manifest
    assert [b.logical_path for b in export.files] == ["Um"]
    assert export.ignored == 2


def test_loader_aceita_pasta(tmp_path):
    pasta = tmp_path / "export"
    (pasta / "Bots").mkdir(parents=True)
    (pasta / "Bots" / "Um").write_bytes(_bot_minimo("Um"))
    export = loader.load_export(pasta)
    assert [b.logical_path for b in export.files] == ["Um"]


def test_loader_recusa_entrada_estranha(tmp_path):
    arquivo = tmp_path / "coisa.txt"
    arquivo.write_text("nada")
    with pytest.raises(ValueError, match="não é pasta nem .zip"):
        loader.load_export(arquivo)


def test_loader_entrada_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        loader.load_export(tmp_path / "nao_existe.zip")


# --- dicionário ---


def test_dicionario_do_repo_e_valido():
    """O dicionario.toml que vai pro git tem que parsear e ter as seções."""
    dic = config.load(RAIZ / "dicionario.toml")
    assert dic.max_depth == 3
    assert dic.friendly("Database:connect") == "Banco: conectar"
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
