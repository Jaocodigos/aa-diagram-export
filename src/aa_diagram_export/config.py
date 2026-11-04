"""Leitura do dicionario.toml — o painel de ajustes do time (§6.4 e §10.2).

`tomllib` é biblioteca padrão desde o 3.11, então configuração em TOML não
custa dependência nenhuma. A vantagem sobre configuração escrita em Python é
que um erro de edição produz mensagem clara em vez de quebrar o programa.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

NOME_PADRAO = "dicionario.toml"

ESTILO_PADRAO: dict[str, str] = {
    "controle": "stroke:#b26a00,stroke-width:2px",
    "acoes": "stroke:#4c6ef5,stroke-width:1px",
    "chamada": "stroke:#2f9e44,stroke-width:2px",
    "nao_resolvido": "stroke:#e03131,stroke-width:2px,stroke-dasharray:4 3",
    "limite": "stroke:#862e9c,stroke-width:2px,stroke-dasharray:2 2",
}

PACOTES_DE_CONTROLE_PADRAO: tuple[str, ...] = (
    "If",
    "Loop",
    "ErrorHandler",
    "Step",
    "TaskBot",
)


@dataclass(frozen=True)
class Dictionary:
    """O conteúdo do dicionario.toml, já com os padrões aplicados."""

    max_depth: int = 3
    style: dict[str, str] = field(default_factory=lambda: dict(ESTILO_PADRAO))
    friendly_commands: dict[str, str] = field(default_factory=dict)
    control_packages: tuple[str, ...] = PACOTES_DE_CONTROLE_PADRAO

    def friendly(self, command: str) -> str | None:
        """Rótulo amigável do comando, ou None se o time ainda não cadastrou.

        Quem chama decide o que fazer com o None. O render usa o nome cru e
        registra a falta, para o index.md listar o que falta cadastrar.
        """
        return self.friendly_commands.get(command)


def load(path: Path | None = None) -> Dictionary:
    """Carrega o dicionário.

    Sem `path`, procura `dicionario.toml` no diretório atual e cai nos padrões
    se não achar. Com `path` apontando para arquivo que não existe, falha — aí
    foi o usuário que pediu um arquivo específico e errar em silêncio seria
    pior que parar.
    """
    if path is None:
        candidato = Path.cwd() / NOME_PADRAO
        if not candidato.is_file():
            return Dictionary()
        path = candidato
    elif not path.is_file():
        raise FileNotFoundError(f"dicionário não encontrado: {path}")

    try:
        with path.open("rb") as arquivo:
            bruto = tomllib.load(arquivo)
    except tomllib.TOMLDecodeError as erro:
        raise ValueError(f"{path} tem erro de sintaxe TOML: {erro}") from erro

    geral = bruto.get("geral", {})
    controle = bruto.get("estruturas_de_controle", {})
    return Dictionary(
        max_depth=int(geral.get("profundidade_maxima", 3)),
        style=ESTILO_PADRAO | bruto.get("estilo", {}),
        friendly_commands=dict(bruto.get("comandos_amigaveis", {})),
        control_packages=tuple(
            controle.get("pacotes", PACOTES_DE_CONTROLE_PADRAO)
        ),
    )
