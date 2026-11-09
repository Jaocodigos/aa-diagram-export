"""JSON do A360 → modelo intermediário.

Validado contra um export real do Control Room em 2026-11-05 (as premissas da
§11 da spec, agora respondidas). O que o formato mostrou:

- O bot é um objeto com `nodes`, `variables`, `packages`, `properties`.
- Cada nó tem `uid`, `commandName`, `packageName`, `disabled`, `attributes`,
  e aninha por `children` (corpo) e `branches` (else/elseIf, catch/finally).
- Não existe campo de rótulo na ação. O que o dev escreve são nós `Comment`
  separados, e é deles que sai o rótulo dos blocos (ver `_corpo`).
- `step` tem `title`; `runTask` guarda o alvo em `taskbot.taskbotFile`, numa
  URL `repository:///...` com os espaços percent-encoded.

Nenhum valor literal de parâmetro é lido para o modelo. Condições e loops
saem por nome de variável, com o valor comparado substituído por `⋯` (§9).
"""

from __future__ import annotations

import re
from typing import Any

from . import paths
from .model import (
    ActionBlock,
    Bot,
    Branch,
    Break,
    CallBinding,
    CallBot,
    Continue,
    If,
    Loop,
    LoopKind,
    Node,
    Step,
    TryCatch,
    Variable,
)

CMD_IF = "if"
CMD_ELSE_IF = "elseIf"
CMD_ELSE = "else"
CMD_TRY = "try"
CMD_CATCH = "catch"
CMD_FINALLY = "finally"
CMD_STEP = "step"
CMD_LOOP = "loop.commands.start"
CMD_BREAK = "loop.commands.break"
CMD_CONTINUE = "loop.commands.continue"
CMD_RUN_TASK = "runTask"
CMD_COMMENT = "Comment"

ESTRUTURAS = {CMD_IF, CMD_TRY, CMD_STEP, CMD_LOOP, CMD_BREAK, CMD_CONTINUE, CMD_RUN_TASK}

#: Fica no lugar do valor comparado, que nunca entra no diagrama (§9).
VALOR_OMITIDO = "⋯"

OPERADORES = {
    "EQ": "=",
    "NE": "≠",
    "NEQ": "≠",
    "GT": ">",
    "GTE": "≥",
    "LT": "<",
    "LTE": "≤",
    "INCLUDE": "contém",
    "NOTINCLUDE": "não contém",
    "NOT_INCLUDE": "não contém",
    "STARTS_WITH": "começa com",
    "ENDS_WITH": "termina com",
    "IS_EMPTY": "está vazio",
    "IS_NOT_EMPTY": "não está vazio",
}

#: Condições que não comparam duas pontas: o sentido está no nome do
#: condicional, e os atributos são os argumentos dele.
CONDICIONAIS = {
    "fileExists": "arquivo existe",
    "fileNotExists": "arquivo não existe",
    "folderExists": "pasta existe",
    "folderDoesNotExists": "pasta não existe",
    "valueExistsForKey": "dicionário tem a chave",
    "valueDoesNotExistForKey": "dicionário não tem a chave",
    "windowExists": "janela existe",
    "windowDoesNotExist": "janela não existe",
}

JUNCOES = {"OR": "ou", "AND": "e"}

_VARIAVEL = re.compile(r"\$([^$]+)\$")


def parse_bot(data: dict[str, Any], logical_path: str) -> Bot:
    """Converte o JSON de um bot do A360 no modelo intermediário."""
    if not isinstance(data, dict) or "nodes" not in data:
        raise ValueError(
            f"{logical_path}: não parece um Task Bot do A360 "
            "(objeto JSON sem a chave 'nodes')."
        )
    pacotes = {
        p.get("name")
        for p in (data.get("packages") or [])
        if isinstance(p, dict) and p.get("name")
    }
    return Bot(
        path=logical_path,
        name=paths.bot_name(logical_path),
        variables=_variaveis(data.get("variables") or []),
        packages=tuple(sorted(pacotes)),
        body=_corpo(data.get("nodes") or []),
    )


# --- travessia ---


def _corpo(nos: list[Any]) -> tuple[Node, ...]:
    """Converte uma lista de nós do A360, colapsando as ações lineares.

    Um nó `Comment` não vira nó no diagrama: ele guarda o texto para rotular
    o próximo bloco de ações. Comentário seguido direto de uma estrutura de
    controle é descartado — If e Loop já se explicam pela condição, e criar um
    nó só para o texto encheria o diagrama de caixa sem fluxo.
    """
    saida: list[Node] = []
    pendentes: list[dict] = []
    rotulo: str | None = None

    def descarregar() -> None:
        nonlocal pendentes, rotulo
        if not pendentes:
            return
        saida.append(
            ActionBlock(
                pendentes[0].get("uid") or "",
                commands=tuple(_nome_do_comando(n) for n in pendentes),
                label=rotulo,
            )
        )
        pendentes = []
        rotulo = None

    for no in nos:
        if not isinstance(no, dict) or no.get("disabled"):
            continue

        comando = no.get("commandName")
        if comando == CMD_COMMENT:
            descarregar()
            rotulo = _texto(_atributos(no).get("comment")) or None
            continue

        tem_filhos = bool(no.get("children") or no.get("branches"))
        if comando not in ESTRUTURAS and not tem_filhos:
            pendentes.append(no)
            continue

        descarregar()
        rotulo = None
        saida.append(_estrutura(no))

    descarregar()
    return tuple(saida)


def _estrutura(no: dict) -> Node:
    uid = no.get("uid") or ""
    filhos = no.get("children") or []
    ramos = [r for r in (no.get("branches") or []) if isinstance(r, dict) and not r.get("disabled")]

    match no.get("commandName"):
        case "if":
            ramificacoes = [Branch(condition=_condicao(no), body=_corpo(filhos))]
            senao: tuple[Node, ...] = ()
            for ramo in ramos:
                if ramo.get("commandName") == CMD_ELSE_IF:
                    ramificacoes.append(
                        Branch(_condicao(ramo), _corpo(ramo.get("children") or []))
                    )
                elif ramo.get("commandName") == CMD_ELSE:
                    senao = _corpo(ramo.get("children") or [])
            return If(uid, branches=tuple(ramificacoes), else_body=senao)

        case "try":
            captura: list[Node] = []
            finalmente: list[Node] = []
            for ramo in ramos:
                corpo = _corpo(ramo.get("children") or [])
                if ramo.get("commandName") == CMD_CATCH:
                    captura.extend(corpo)
                elif ramo.get("commandName") == CMD_FINALLY:
                    finalmente.extend(corpo)
            return TryCatch(
                uid,
                try_body=_corpo(filhos),
                catch_body=tuple(captura),
                finally_body=tuple(finalmente),
            )

        case "loop.commands.start":
            tipo, expressao = _loop(no)
            return Loop(uid, kind=tipo, expression=expressao, body=_corpo(filhos))

        case "step":
            titulo = _texto(_atributos(no).get("title")) or "Step"
            return Step(uid, title=titulo, body=_corpo(filhos))

        case "runTask":
            return CallBot(
                uid,
                target_path=paths.normalize(_alvo(no)),
                bindings=_ligacoes(no),
            )

        case "loop.commands.break":
            return Break(uid)

        case "loop.commands.continue":
            return Continue(uid)

        case _:
            # Comando desconhecido que tem filhos. Vira agrupador em vez de
            # ação, para as ações de dentro não sumirem do diagrama.
            return Step(uid, title=_nome_do_comando(no), body=_corpo(filhos))


# --- leitura de atributos ---


def _atributos(no: dict) -> dict[str, dict]:
    return {
        a["name"]: a
        for a in (no.get("attributes") or [])
        if isinstance(a, dict) and "name" in a
    }


def _texto(atributo: dict | None) -> str:
    return ((atributo or {}).get("value") or {}).get("string") or ""


def _nome_do_comando(no: dict) -> str:
    return f"{no.get('packageName') or '?'}:{no.get('commandName') or '?'}"


def _nome_de_variavel(valor: Any) -> str:
    """Nome da variável referenciada, ou `⋯` quando o campo é um literal.

    É aqui que a regra da §9 é aplicada na prática: se o atributo não aponta
    para uma variável, o conteúdo não é lido.
    """
    if not isinstance(valor, dict):
        return VALOR_OMITIDO
    if valor.get("variableName"):
        return str(valor["variableName"])

    expressao = valor.get("expression")
    if not expressao:
        return VALOR_OMITIDO
    achado = _VARIAVEL.search(str(expressao))
    if not achado:
        return VALOR_OMITIDO

    bruto = achado.group(1)
    for separador in ("{", ".", ":", "["):
        bruto = bruto.split(separador)[0]
    return bruto.strip() or VALOR_OMITIDO


def _comparacao(por_nome: dict[str, dict]) -> str:
    """Condição que compara duas pontas: `variable`, `operator` e `value`."""
    variavel = _nome_de_variavel((por_nome.get("variable") or {}).get("value"))
    operador = _texto(por_nome.get("operator"))
    if not operador:
        return variavel

    simbolo = OPERADORES.get(operador, operador.replace("_", " ").lower())
    if "value" not in por_nome:
        return f"{variavel} {simbolo}"

    comparado = (por_nome.get("value") or {}).get("value") or {}
    if comparado.get("type") == "BOOLEAN":
        # Literal booleano é a única exceção da §9: verdadeiro ou falso não
        # tem como carregar senha, caminho de rede ou qualquer outro segredo,
        # e esconder isso tornaria a condição ilegível.
        mostrado = "verdadeiro" if comparado.get("boolean") else "falso"
    else:
        mostrado = VALOR_OMITIDO
    return f"{variavel} {simbolo} {mostrado}"


def _predicado(bloco: dict, por_nome: dict[str, dict]) -> str:
    """Condição sem comparação: o sentido está no nome do condicional.

    É o caso de `fileExists`, `valueExistsForKey` e afins, cujos atributos são
    argumentos e não as duas pontas de uma comparação.
    """
    nome = (bloco.get("value") or {}).get("conditionalName") or ""
    texto = CONDICIONAIS.get(nome, nome or "condição")
    for atributo in por_nome.values():
        alvo = _nome_de_variavel(atributo.get("value"))
        if alvo != VALOR_OMITIDO:
            return f"{texto}: {alvo}"
    return texto


def _parte_de_condicao(bloco: dict) -> str:
    por_nome = {
        a.get("name"): a
        for a in (bloco.get("attributes") or [])
        if isinstance(a, dict)
    }
    if "variable" in por_nome:
        return _comparacao(por_nome)
    return _predicado(bloco, por_nome)


def _condicao(no: dict) -> str:
    condicao = _atributos(no).get("condition")
    if not condicao:
        return "condição"

    partes = [_parte_de_condicao(condicao)]
    proximo = condicao.get("operatorAttribute")
    while isinstance(proximo, dict):
        juncao = JUNCOES.get(proximo.get("operator"), proximo.get("operator") or "e")
        partes.append(f"{juncao} {_parte_de_condicao(proximo)}")
        proximo = proximo.get("operatorAttribute")

    return " ".join(p for p in partes if p).strip() or "condição"


def _loop(no: dict) -> tuple[LoopKind, str]:
    """Tipo e texto do loop. O texto completa o 'Loop: <para cada|repetir|enquanto>'."""
    atributos = _atributos(no)
    if _texto(atributos.get("loopType")).upper() == "WHILE":
        return LoopKind.WHILE, _condicao(no)

    iterador = atributos.get("iterator") or {}
    nome = (iterador.get("value") or {}).get("iteratorName") or ""
    internos = {
        a.get("name"): a
        for a in (iterador.get("attributes") or [])
        if isinstance(a, dict)
    }

    def variavel(chave: str) -> str:
        return _nome_de_variavel((internos.get(chave) or {}).get("value"))

    match nome:
        case "loop.iterators.times":
            return LoopKind.N_TIMES, f"{variavel('times')} vezes"
        case "loop.iterators.files":
            return LoopKind.FOR_EACH, f"arquivo de {variavel('folderPath')}"
        case "iteratorTableRow":
            return LoopKind.FOR_EACH, f"linha de {variavel('sourceTable')}"
        case _:
            if internos:
                primeira = next(iter(internos))
                return LoopKind.FOR_EACH, f"item de {variavel(primeira)}"
            return LoopKind.FOR_EACH, nome.rsplit(".", 1)[-1] or "item"


def _alvo(no: dict) -> str:
    valor = (_atributos(no).get("taskbot") or {}).get("value") or {}
    arquivo = valor.get("taskbotFile") or {}
    return arquivo.get("string") or arquivo.get("expression") or ""


def _ligacoes(no: dict) -> tuple[CallBinding, ...]:
    """Entradas e saídas declaradas na chamada.

    As entradas vivem em `taskbot.value.taskbotInput.dictionary`, onde a
    chave é o nome do parâmetro no bot chamado. As saídas vivem em `returnTo`
    no próprio nó, mapeando a saída do chamado para a variável do chamador.

    Só nome, tipo e a variável ligada entram. O valor de uma entrada é uma
    expressão que pode conter literal, e literal não vai para o diagrama nem
    para a página (§9) — daí só o nome da variável ser extraído dela.
    """
    ligacoes: list[CallBinding] = []

    valor = (_atributos(no).get("taskbot") or {}).get("value") or {}
    entradas = (valor.get("taskbotInput") or {}).get("dictionary") or []
    for item in entradas:
        if not isinstance(item, dict) or not item.get("key"):
            continue
        conteudo = item.get("value") or {}
        ligacoes.append(
            CallBinding(
                name=str(item["key"]),
                type=str(conteudo.get("type") or "").capitalize(),
                is_output=False,
                bound_to=_nome_de_variavel(conteudo),
            )
        )

    saidas = (no.get("returnTo") or {}).get("dictionary") or []
    for item in saidas:
        if not isinstance(item, dict) or not item.get("key"):
            continue
        conteudo = item.get("value") or {}
        ligacoes.append(
            CallBinding(
                name=str(item["key"]),
                # O tipo aqui é sempre VARIABLE: o tipo de verdade está
                # declarado no bot chamado, e o render cruza com ele.
                type="",
                is_output=True,
                bound_to=conteudo.get("variableName") or None,
            )
        )

    return tuple(ligacoes)


def _variaveis(brutas: list[Any]) -> tuple[Variable, ...]:
    saida: list[Variable] = []
    for v in brutas:
        if not isinstance(v, dict) or not v.get("name"):
            continue
        saida.append(
            Variable(
                name=str(v["name"]),
                type=str(v.get("type") or "").capitalize(),
                is_input=bool(v.get("input")),
                is_output=bool(v.get("output")),
            )
        )
    return tuple(saida)
