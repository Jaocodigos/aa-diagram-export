"""Transforma a entrada (.zip ou pasta) num inventário de bots (§3).

Quem decide o que é bot é o `manifest.json` do export, pelo `contentType`
`application/vnd.aa.taskbot` — não a extensão do arquivo, que no A360 não
existe. Sem manifest (export parcial, pasta montada à mão), cai para um
reconhecimento por conteúdo: JSON de objeto com a chave `nodes`.

Os `.jar` do export são os pacotes do A360, não bots. Num export real eles
respondem por quase todo o tamanho — 190 MB de 195 MB no que foi usado para
validar isto —, então nunca são lidos para a memória.
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path

from . import paths

MANIFEST = "manifest.json"
EXTENSOES_IGNORADAS = (".jar", ".py", ".xml", ".zip", ".dll", ".exe")


@dataclass(frozen=True)
class BotFile:
    """Um bot do export, com o caminho já canônico e o conteúdo cru."""

    logical_path: str
    source: str
    content: bytes


@dataclass(frozen=True)
class Export:
    files: tuple[BotFile, ...]
    ignored: int
    used_manifest: bool


def load_export(entrada: Path) -> Export:
    """Abre o export, seja `.zip` ou pasta já extraída, e devolve o inventário."""
    if not entrada.exists():
        raise FileNotFoundError(f"entrada não encontrada: {entrada}")
    if entrada.is_dir():
        return _de_pasta(entrada)
    if entrada.suffix.lower() == ".zip":
        return _de_zip(entrada)
    raise ValueError(
        f"{entrada} não é pasta nem .zip. A entrada esperada é o .zip do "
        "Control Room ou a pasta já extraída."
    )


# --- zip ---


def _de_zip(entrada: Path) -> Export:
    with zipfile.ZipFile(entrada) as arquivo_zip:
        nomes = [i.filename for i in arquivo_zip.infolist() if not i.is_dir()]
        indice = {paths.normalize(nome): nome for nome in nomes}

        manifesto = _ler_manifest(lambda n: arquivo_zip.read(n), indice)
        if manifesto is not None:
            achados = _pelo_manifest(
                manifesto, indice, lambda n: arquivo_zip.read(n)
            )
            return Export(
                files=achados,
                ignored=len(nomes) - len(achados),
                used_manifest=True,
            )

        achados, ignorados = _por_conteudo(
            nomes, lambda n: arquivo_zip.read(n)
        )
        return Export(files=achados, ignored=ignorados, used_manifest=False)


# --- pasta ---


def _de_pasta(raiz: Path) -> Export:
    arquivos = [p for p in sorted(raiz.rglob("*")) if p.is_file()]
    indice = {
        paths.normalize(p.relative_to(raiz).as_posix()): p.relative_to(raiz).as_posix()
        for p in arquivos
    }
    ler = lambda nome: (raiz / nome).read_bytes()  # noqa: E731

    manifesto = _ler_manifest(ler, indice)
    if manifesto is not None:
        achados = _pelo_manifest(manifesto, indice, ler)
        return Export(
            files=achados, ignored=len(arquivos) - len(achados), used_manifest=True
        )

    achados, ignorados = _por_conteudo(list(indice.values()), ler)
    return Export(files=achados, ignored=ignorados, used_manifest=False)


# --- comum ---


def _ler_manifest(ler, indice: dict[str, str]) -> dict | None:
    nome = indice.get(paths.normalize(MANIFEST))
    if nome is None:
        return None
    try:
        dados = json.loads(ler(nome))
    except (ValueError, OSError):
        return None
    return dados if isinstance(dados, dict) and "files" in dados else None


def _pelo_manifest(manifesto: dict, indice: dict[str, str], ler) -> tuple[BotFile, ...]:
    achados: list[BotFile] = []
    for entrada in manifesto.get("files") or []:
        if entrada.get("contentType") != paths.CONTENT_TYPE_TASKBOT:
            continue
        if entrada.get("excluded"):
            continue
        bruto = entrada.get("newPath") or entrada.get("path") or ""
        canonico = paths.normalize(bruto)
        nome_real = indice.get(canonico)
        if nome_real is None:
            # O manifest lista um bot que não veio no pacote. Não é erro
            # fatal: vira pendência quando algum runTask apontar para ele.
            continue
        achados.append(
            BotFile(logical_path=canonico, source=bruto, content=ler(nome_real))
        )
    return tuple(sorted(achados, key=lambda b: b.logical_path))


def _por_conteudo(nomes: list[str], ler) -> tuple[tuple[BotFile, ...], int]:
    achados: list[BotFile] = []
    ignorados = 0
    for nome in nomes:
        if nome.lower().endswith(EXTENSOES_IGNORADAS):
            ignorados += 1
            continue
        try:
            dados = json.loads(ler(nome))
        except (ValueError, OSError, UnicodeDecodeError):
            ignorados += 1
            continue
        if not isinstance(dados, dict) or "nodes" not in dados:
            ignorados += 1
            continue
        achados.append(
            BotFile(
                logical_path=paths.normalize(nome),
                source=nome,
                content=json.dumps(dados).encode("utf-8"),
            )
        )
    return tuple(sorted(achados, key=lambda b: b.logical_path)), ignorados
