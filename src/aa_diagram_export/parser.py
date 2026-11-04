"""JSON do A360 → modelo. **Ainda não implementado, de propósito.**

Este é o único módulo inteiramente dependente do formato do export, e as
premissas 3 a 9 da §11 da spec não foram validadas contra um export real:

3. o campo que guarda a árvore de ações e o nome do campo de filhos;
4. como If / Else If / Else guardam os ramos e a condição;
5. como Loop guarda o tipo de iteração e a coleção iterada;
6. como Try / Catch / Finally delimitam os blocos;
7. em que parâmetro do Run Task fica o caminho do bot chamado, e em que forma;
8. onde fica o label ou a descrição que o dev digita numa ação;
9. onde fica a lista de variáveis, com tipo e marcação de entrada e saída.

Escrever este arquivo agora seria adivinhar. O resto do pipeline — modelo,
resolver, render, CLI — não depende dessas respostas e já está pronto e
testado, então quando o `.zip` chegar o trabalho que falta é só este módulo.
"""

from __future__ import annotations

from typing import Any

from .model import Bot

MENSAGEM = (
    "O parser do A360 ainda não foi escrito: as premissas 3 a 9 da §11 da spec "
    "precisam ser validadas contra um export real do Control Room. "
    "Com o .zip em mãos, é o único módulo que falta."
)


def parse_bot(data: dict[str, Any], logical_path: str) -> Bot:
    """Converte o JSON de um bot do A360 no modelo intermediário."""
    raise NotImplementedError(MENSAGEM)
