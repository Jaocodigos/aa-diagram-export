"""Transforma a entrada (.zip ou pasta) num inventário de arquivos de bot (§3).

A detecção de qual dos dois foi passado e a extração do zip estão prontas. O
que ainda depende do export real é só decidir se um arquivo é um Task Bot —
ver `paths.looks_like_bot_file` e a premissa 2 da §11.
"""

from __future__ import annotations

import tempfile
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from . import paths


@dataclass(frozen=True)
class BotFile:
    """Um arquivo candidato a bot, com o caminho lógico já normalizado."""

    logical_path: str
    file: Path


@dataclass(frozen=True)
class Export:
    root: Path
    files: tuple[BotFile, ...]
    ignored: int


@contextmanager
def open_export(entrada: Path) -> Iterator[Export]:
    """Abre o export e devolve o inventário.

    Sendo `.zip`, extrai num temporário que é descartado na saída do `with`.
    Sendo pasta, lê no lugar.
    """
    if not entrada.exists():
        raise FileNotFoundError(f"entrada não encontrada: {entrada}")

    if entrada.is_dir():
        yield _varrer(entrada)
        return

    if entrada.suffix.lower() != ".zip":
        raise ValueError(
            f"{entrada} não é pasta nem .zip. A entrada esperada é o .zip do "
            "Control Room ou a pasta já extraída."
        )

    with tempfile.TemporaryDirectory(prefix="aa-export-") as temporario:
        destino = Path(temporario)
        with zipfile.ZipFile(entrada) as zip_do_export:
            _extrair_com_seguranca(zip_do_export, destino)
        yield _varrer(destino)


def _extrair_com_seguranca(arquivo_zip: zipfile.ZipFile, destino: Path) -> None:
    """Extrai recusando entrada que escape do destino.

    O export é arquivo de terceiro: um membro com `..` ou caminho absoluto
    escreveria fora da pasta temporária.
    """
    base = destino.resolve()
    for membro in arquivo_zip.infolist():
        alvo = (base / membro.filename).resolve()
        if not alvo.is_relative_to(base):
            raise ValueError(
                f"o zip tem uma entrada que aponta para fora da pasta de "
                f"extração: {membro.filename}"
            )
    arquivo_zip.extractall(base)


def _varrer(raiz: Path) -> Export:
    encontrados: list[BotFile] = []
    ignorados = 0

    for caminho in sorted(raiz.rglob("*")):
        if not caminho.is_file():
            continue
        if paths.looks_like_bot_file(caminho.name):
            relativo = caminho.relative_to(raiz).as_posix()
            encontrados.append(
                BotFile(logical_path=paths.normalize(relativo), file=caminho)
            )
        else:
            ignorados += 1

    return Export(root=raiz, files=tuple(encontrados), ignored=ignorados)
