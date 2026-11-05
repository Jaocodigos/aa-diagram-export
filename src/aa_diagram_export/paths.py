"""Como um caminho de bot é escrito e comparado.

Validado contra um export real do Control Room (A360) em 2026-11-05. O export
traz o mesmo bot escrito de duas formas, e elas precisam casar:

- no `manifest.json` e no nome das entradas do zip:
  ``Automation Anywhere\\Bots\\CommonTask\\Log\\GravarLogBanco``
- no atributo `taskbotFile` de um `runTask`:
  ``repository:///Automation%20Anywhere/Bots/CommonTask/Log/GravarLogBanco``

`normalize` leva as duas à mesma string: ``CommonTask/Log/GravarLogBanco``.

Arquivo de bot do A360 **não tem extensão**. Quem é bot e quem não é vem do
`contentType` no manifest, não do nome do arquivo.
"""

from __future__ import annotations

from urllib.parse import unquote

PREFIXO_REPOSITORIO = "repository:///"
RAIZES_DO_REPOSITORIO = ("automation anywhere/", "bots/")
# Bots do A360 não têm extensão; isto cobre export de outras versões.
EXTENSOES_DE_BOT = (".json", ".atmx")

CONTENT_TYPE_TASKBOT = "application/vnd.aa.taskbot"


def normalize(bruto: str) -> str:
    """Forma canônica de um caminho de bot, usada como chave de inventário."""
    caminho = (bruto or "").strip()

    if caminho.lower().startswith(PREFIXO_REPOSITORIO):
        caminho = caminho[len(PREFIXO_REPOSITORIO) :]

    caminho = unquote(caminho).replace("\\", "/")
    while "//" in caminho:
        caminho = caminho.replace("//", "/")
    caminho = caminho.strip("/")

    for raiz in RAIZES_DO_REPOSITORIO:
        if caminho.lower().startswith(raiz):
            caminho = caminho[len(raiz) :]

    for extensao in EXTENSOES_DE_BOT:
        if caminho.lower().endswith(extensao):
            caminho = caminho[: -len(extensao)]
            break

    return caminho


def is_dynamic(bruto: str) -> bool:
    """O alvo do Run Task vem de variável, então não dá pra resolver parado.

    No A360 a variável aparece entre `$`, como em `$sNomeDoBot$`.
    """
    return "$" in (bruto or "")


def bot_name(logical_path: str) -> str:
    """Nome de exibição do bot: o último segmento do caminho."""
    return logical_path.rsplit("/", 1)[-1] or logical_path
