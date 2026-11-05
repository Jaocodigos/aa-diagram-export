"""Testes do parser do A360.

As formas usadas aqui são as que o export real do Control Room mostrou em
2026-11-05, reduzidas ao mínimo. O bot de exemplo é sintético de propósito:
export de verdade carrega nome de processo, de variável e de procedure do
cliente, e isso não entra no repositório.
"""

from __future__ import annotations

import pytest
from aa_diagram_export.model import (
    ActionBlock,
    Break,
    CallBot,
    If,
    Loop,
    LoopKind,
    Step,
    TryCatch,
)
from aa_diagram_export.parser import VALOR_OMITIDO, parse_bot


def _acao(uid: str, pacote: str, comando: str, **extra) -> dict:
    return {
        "uid": uid,
        "commandName": comando,
        "packageName": pacote,
        "disabled": False,
        **extra,
    }


def _comparacao(variavel: str, operador: str, valor: dict) -> dict:
    return {
        "name": "condition",
        "attributes": [
            {"name": "variable", "value": {"type": "STRING", "expression": f"${variavel}$"}},
            {"name": "operator", "value": {"type": "STRING", "string": operador}},
            {"name": "value", "value": valor},
        ],
        "value": {"type": "CONDITIONAL", "conditionalName": "stringVariable"},
    }


BOT = {
    "variables": [
        {"name": "sEntrada", "type": "STRING", "input": True, "output": False},
        {"name": "nSaida", "type": "NUMBER", "input": False, "output": True},
        {"name": "semNome"},
    ],
    "packages": [{"name": "Database", "version": "5.6.3"}, {"name": "If"}],
    "nodes": [
        _acao("c1", "Comment", "Comment",
              attributes=[{"name": "comment", "value": {"type": "STRING", "string": "Preparação"}}]),
        _acao("a1", "Database", "connect"),
        _acao("a2", "String", "assign"),
        _acao("x1", "String", "trim", disabled=True),
        _acao("s1", "Step", "step",
              attributes=[{"name": "title", "value": {"type": "STRING", "string": "Processar"}}],
              children=[_acao("a3", "DataTable", "setCellValue")]),
        _acao("i1", "If", "if",
              attributes=[_comparacao("sEntrada", "INCLUDE", {"type": "STRING", "string": "SEGREDO"})],
              children=[_acao("a4", "Number", "increment")],
              branches=[
                  _acao("e1", "If", "elseIf",
                        attributes=[_comparacao("sEntrada", "EQ", {"type": "BOOLEAN", "boolean": True})],
                        children=[_acao("a5", "String", "replace")]),
                  _acao("e2", "If", "else", children=[_acao("a6", "String", "length")]),
              ]),
        _acao("l1", "Loop", "loop.commands.start",
              attributes=[
                  {"name": "loopType", "value": {"type": "STRING", "string": "ITERATOR"}},
                  {"name": "iterator",
                   "returnTo": {"type": "VARIABLE", "variableName": "linha"},
                   "attributes": [{"name": "sourceTable",
                                   "value": {"type": "VARIABLE", "variableName": "tabela"}}],
                   "value": {"type": "ITERATOR", "iteratorName": "iteratorTableRow"}},
              ],
              children=[_acao("b1", "Loop", "loop.commands.break")]),
        _acao("t1", "ErrorHandler", "try",
              children=[_acao("a7", "File", "createFile")],
              branches=[
                  _acao("k1", "ErrorHandler", "catch", children=[_acao("a8", "ErrorHandler", "throw")]),
                  _acao("f1", "ErrorHandler", "finally", children=[_acao("a9", "Database", "disconnect")]),
              ]),
        _acao("r1", "TaskBot", "runTask",
              attributes=[{"name": "taskbot", "value": {
                  "type": "TASKBOT",
                  "taskbotFile": {"type": "FILE",
                                  "string": "repository:///Automation%20Anywhere/Bots/Comum/Enviar"},
              }}]),
    ],
}


@pytest.fixture
def bot():
    return parse_bot(BOT, "Processos/Exemplo")


def test_metadados(bot):
    assert bot.path == "Processos/Exemplo"
    assert bot.name == "Exemplo"
    assert bot.packages == ("Database", "If")


def test_variaveis(bot):
    assert [(v.name, v.type, v.is_input, v.is_output) for v in bot.variables] == [
        ("sEntrada", "String", True, False),
        ("nSaida", "Number", False, True),
        ("semNome", "", False, False),
    ]


def test_comentario_vira_rotulo_do_bloco_seguinte(bot):
    primeiro = bot.body[0]
    assert isinstance(primeiro, ActionBlock)
    assert primeiro.label == "Preparação"
    assert primeiro.commands == ("Database:connect", "String:assign")


def test_acao_desabilitada_e_ignorada(bot):
    """Ação desabilitada no A360 não roda, então não entra no diagrama."""
    todos = [c for no in bot.body if isinstance(no, ActionBlock) for c in no.commands]
    assert "String:trim" not in todos


def test_step_vira_agrupador(bot):
    step = next(n for n in bot.body if isinstance(n, Step))
    assert step.title == "Processar"
    assert step.body[0].commands == ("DataTable:setCellValue",)


def test_if_com_elseif_e_else(bot):
    bloco = next(n for n in bot.body if isinstance(n, If))
    assert len(bloco.branches) == 2
    assert bloco.branches[0].condition == f"sEntrada contém {VALOR_OMITIDO}"
    assert bloco.branches[1].condition == "sEntrada = verdadeiro"
    assert bloco.else_body[0].commands == ("String:length",)


def test_condicao_nao_vaza_literal(bot):
    """§9 na prática: o texto comparado não pode aparecer no diagrama."""
    bloco = next(n for n in bot.body if isinstance(n, If))
    assert "SEGREDO" not in bloco.branches[0].condition


def test_loop_de_tabela(bot):
    laco = next(n for n in bot.body if isinstance(n, Loop))
    assert laco.kind is LoopKind.FOR_EACH
    assert laco.expression == "linha de tabela"
    assert isinstance(laco.body[0], Break)


def test_try_catch_finally(bot):
    bloco = next(n for n in bot.body if isinstance(n, TryCatch))
    assert bloco.try_body[0].commands == ("File:createFile",)
    assert bloco.catch_body[0].commands == ("ErrorHandler:throw",)
    assert bloco.finally_body[0].commands == ("Database:disconnect",)


def test_run_task_normaliza_o_alvo(bot):
    """O alvo vem como URL percent-encoded e precisa casar com o inventário."""
    chamada = next(n for n in bot.body if isinstance(n, CallBot))
    assert chamada.target_path == "Comum/Enviar"


def test_json_que_nao_e_bot():
    with pytest.raises(ValueError, match="não parece um Task Bot"):
        parse_bot({"qualquer": "coisa"}, "X")


# --- variantes de loop e de condição vistas no export real ---


def _loop_com(iterador: dict, tipo: str = "ITERATOR", condicao: dict | None = None):
    atributos: list[dict] = [
        {"name": "loopType", "value": {"type": "STRING", "string": tipo}}
    ]
    if iterador:
        atributos.append(iterador)
    if condicao:
        atributos.append(condicao)
    no = _acao("l", "Loop", "loop.commands.start", attributes=atributos, children=[])
    return parse_bot({"nodes": [no]}, "X").body[0]


def test_loop_n_vezes():
    laco = _loop_com({
        "name": "iterator",
        "attributes": [{"name": "times", "value": {"type": "NUMBER", "expression": "$tentativas$"}}],
        "value": {"type": "ITERATOR", "iteratorName": "loop.iterators.times"},
    })
    assert laco.kind is LoopKind.N_TIMES
    assert laco.expression == "tentativas vezes"


def test_loop_de_arquivos():
    laco = _loop_com({
        "name": "iterator",
        "attributes": [{"name": "folderPath", "value": {"type": "STRING", "expression": "$pasta$/x"}}],
        "value": {"type": "ITERATOR", "iteratorName": "loop.iterators.files"},
    })
    assert laco.expression == "arquivo de pasta"


def test_loop_while():
    laco = _loop_com(
        {},
        tipo="WHILE",
        condicao=_comparacao("tentativa", "LTE", {"type": "NUMBER", "number": "3"}),
    )
    assert laco.kind is LoopKind.WHILE
    assert laco.expression == f"tentativa ≤ {VALOR_OMITIDO}"


def test_condicao_de_predicado():
    """fileExists e afins não comparam nada: o sentido está no nome."""
    no = _acao("i", "If", "if", attributes=[{
        "name": "condition",
        "attributes": [{"name": "sourceFilePath",
                        "value": {"type": "FILE", "expression": "file://$pasta$/tmp.csv"}}],
        "value": {"type": "CONDITIONAL", "conditionalName": "fileExists"},
    }], children=[])
    bloco = parse_bot({"nodes": [no]}, "X").body[0]
    assert bloco.branches[0].condition == "arquivo existe: pasta"
    assert "tmp.csv" not in bloco.branches[0].condition


def test_condicoes_encadeadas():
    no = _acao("i", "If", "if", attributes=[{
        "name": "condition",
        "attributes": [
            {"name": "variable", "value": {"type": "NUMBER", "expression": "$a$"}},
            {"name": "operator", "value": {"type": "STRING", "string": "EQ"}},
            {"name": "value", "value": {"type": "NUMBER", "number": "0"}},
        ],
        "operatorAttribute": {
            "operator": "OR",
            "attributes": [
                {"name": "variable", "value": {"type": "NUMBER", "expression": "$b$"}},
                {"name": "operator", "value": {"type": "STRING", "string": "GT"}},
                {"name": "value", "value": {"type": "NUMBER", "number": "9"}},
            ],
        },
        "value": {"type": "CONDITIONAL", "conditionalName": "numberVariable"},
    }], children=[])
    bloco = parse_bot({"nodes": [no]}, "X").body[0]
    assert bloco.branches[0].condition == f"a = {VALOR_OMITIDO} ou b > {VALOR_OMITIDO}"


def test_comando_desconhecido_com_filhos_nao_perde_as_acoes():
    no = _acao("z", "Futuro", "comandoNovo", children=[_acao("a", "String", "assign")])
    agrupador = parse_bot({"nodes": [no]}, "X").body[0]
    assert isinstance(agrupador, Step)
    assert agrupador.title == "Futuro:comandoNovo"
    assert agrupador.body[0].commands == ("String:assign",)
