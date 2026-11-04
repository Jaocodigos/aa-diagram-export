"""Como o caminho de um bot é escrito e comparado.

Este arquivo existe sozinho de propósito: é a costura que depende do formato
do export. As premissas 7 e 10 da §11 da spec — em que forma o `Run Task`
guarda o caminho do bot chamado, e se o export preserva esse caminho de modo
consistente — ainda não foram validadas contra um export real.

Quando o `.zip` chegar, é aqui que a correção entra. Nenhuma outra camada
precisa mudar, porque loader e resolver comparam caminhos só por estas
funções.
"""

from __future__ import annotations

EXTENSOES_DE_BOT = (".json", ".atmx")
PREFIXOS_IGNORADOS = ("bots/",)


def normalize(bruto: str) -> str:
    """Forma canônica de um caminho de bot, usada como chave de inventário.

    Tira separador de Windows, barra sobrando, prefixo de repositório e
    extensão, para que o caminho que o `Run Task` referencia e o caminho do
    arquivo no export cheguem à mesma string.
    """
    caminho = bruto.strip().replace("\\", "/")
    while "//" in caminho:
        caminho = caminho.replace("//", "/")
    caminho = caminho.strip("/")

    for prefixo in PREFIXOS_IGNORADOS:
        if caminho.lower().startswith(prefixo):
            caminho = caminho[len(prefixo) :]
            break

    for extensao in EXTENSOES_DE_BOT:
        if caminho.lower().endswith(extensao):
            caminho = caminho[: -len(extensao)]
            break

    return caminho


def is_dynamic(bruto: str) -> bool:
    """O alvo do Run Task vem de variável, então não dá pra resolver parado.

    No A360 a variável aparece entre `$`. Heurística, e também pendente de
    confirmação contra o export real.
    """
    return "$" in bruto


def looks_like_bot_file(nome: str) -> bool:
    """O arquivo tem cara de bot, pelo nome.

    Distinguir Task Bot de Form bot e de API task exige olhar o conteúdo, e é
    a premissa 2 da §11 — ainda aberta. Por ora o filtro é só a extensão, e o
    loader conta como ignorado tudo que não passa.
    """
    return nome.lower().endswith(EXTENSOES_DE_BOT)
