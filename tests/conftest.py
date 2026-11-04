"""Infraestrutura dos testes de snapshot (§10.4).

O teste compara o que o render produziu com um arquivo esperado, byte a byte.
Quando a mudança no diagrama é intencional, `pytest --regenerar` reescreve os
esperados e o diff do git mostra exatamente o que mudou no desenho.
"""

from __future__ import annotations

from pathlib import Path

import pytest

ESPERADOS = Path(__file__).parent / "fixtures" / "esperado"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--regenerar",
        action="store_true",
        default=False,
        help="reescreve os arquivos esperados em tests/fixtures/esperado/",
    )


@pytest.fixture
def snapshot(request: pytest.FixtureRequest):
    """Compara `conteudo` com tests/fixtures/esperado/<nome>."""

    def comparar(nome: str, conteudo: str) -> None:
        caminho = ESPERADOS / nome
        if request.config.getoption("--regenerar"):
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(conteudo, encoding="utf-8", newline="\n")
            pytest.skip(f"esperado regenerado: {nome}")
        if not caminho.is_file():
            pytest.fail(
                f"falta o arquivo esperado {nome}. Rode `pytest --regenerar` "
                "para criá-lo e confira o resultado antes de commitar."
            )
        assert conteudo == caminho.read_text(encoding="utf-8")

    return comparar
