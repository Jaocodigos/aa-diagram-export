"""Bots de exemplo montados à mão, no modelo.

Enquanto o parser não existe (premissas da §11), é com estes que o render e o
resolver são testados. Eles exercitam de propósito todas as construções da §7:
bloco linear, Step, Loop, If com Senão se e Senão, Try/Catch/Finally e chamada
de bot nos quatro estados possíveis.
"""

from __future__ import annotations

from aa_diagram_export.config import Dictionary
from aa_diagram_export.model import (
    ActionBlock,
    Bot,
    Branch,
    CallBot,
    If,
    Loop,
    LoopKind,
    Step,
    TryCatch,
    Variable,
)

CAMINHO_PRINCIPAL = "Bots/Financeiro/ConciliacaoDiaria"
CAMINHO_RELATORIO = "Bots/Comum/EnviarRelatorio"
CAMINHO_AUSENTE = "Bots/Comum/Auditoria"


def dicionario_de_teste() -> Dictionary:
    """Dicionário fixo, para o snapshot não quebrar quando o do repo mudar.

    De propósito, `Excel advanced:SetCell` e `Browser:Download` ficam de fora:
    é assim que o teste cobre o caminho de comando sem rótulo cadastrado.
    """
    return Dictionary(
        max_depth=3,
        friendly_commands={
            "Excel advanced:Open": "Excel: abrir planilha",
            "Excel advanced:GetMultipleCells": "Excel: ler intervalo",
            "Excel advanced:Close": "Excel: fechar planilha",
            "Browser:Launch": "Navegador: abrir",
            "Browser:Close": "Navegador: fechar",
            "Email:Send": "E-mail: enviar",
        },
    )


def bot_principal() -> Bot:
    return Bot(
        path=CAMINHO_PRINCIPAL,
        name="Conciliação Diária",
        variables=(
            Variable("dtExtrato", "Table", is_input=True),
            Variable("nQtdDivergencias", "Number", is_output=True),
            Variable("sCaminhoArquivo", "String"),
        ),
        packages=("Excel advanced", "Browser", "Email"),
        body=(
            ActionBlock(
                "a1",
                commands=("Excel advanced:Open", "Excel advanced:GetMultipleCells"),
            ),
            Step(
                "s1",
                title="Preparar ambiente",
                body=(ActionBlock("a2", commands=("Browser:Launch",)),),
            ),
            Loop(
                "l1",
                kind=LoopKind.FOR_EACH,
                expression="linha de dtExtrato",
                body=(
                    If(
                        "i1",
                        branches=(
                            Branch(
                                "linha está conciliada",
                                (ActionBlock("a3", commands=("Excel advanced:SetCell",)),),
                            ),
                            Branch(
                                "valor divergente",
                                (ActionBlock("a4", commands=("Email:Send",)),),
                            ),
                        ),
                        else_body=(
                            ActionBlock("a5", commands=("Excel advanced:SetCell",)),
                        ),
                    ),
                    TryCatch(
                        "t1",
                        try_body=(ActionBlock("a6", commands=("Browser:Download",)),),
                        catch_body=(ActionBlock("a7", commands=("Email:Send",)),),
                        finally_body=(ActionBlock("a8", commands=("Browser:Close",)),),
                    ),
                ),
            ),
            CallBot("c1", target_path=CAMINHO_RELATORIO),
            CallBot("c2", target_path=CAMINHO_AUSENTE),
            CallBot("c3", target_path="Bots/Comum/$sBotDinamico$"),
            ActionBlock(
                "a9",
                commands=(
                    "Excel advanced:Close",
                    "Browser:Close",
                    "Email:Send",
                    "Excel advanced:Open",
                ),
                label="Encerrar e notificar",
            ),
        ),
    )


def bot_relatorio() -> Bot:
    """O bot chamado. Chama o principal de volta, então gera ciclo."""
    return Bot(
        path=CAMINHO_RELATORIO,
        name="Enviar Relatório",
        variables=(Variable("sDestinatario", "String", is_input=True),),
        packages=("Email",),
        body=(
            ActionBlock("r1", commands=("Email:Send",)),
            CallBot("r2", target_path=CAMINHO_PRINCIPAL),
        ),
    )


def corrente_de_bots(quantidade: int) -> list[Bot]:
    """Cadeia A → B → C → ... para testar o limite de profundidade."""
    bots: list[Bot] = []
    for i in range(quantidade):
        chamadas = ()
        if i + 1 < quantidade:
            chamadas = (CallBot(f"call{i}", target_path=f"Bots/Cadeia/N{i + 1}"),)
        bots.append(
            Bot(
                path=f"Bots/Cadeia/N{i}",
                name=f"Nível {i}",
                body=(ActionBlock(f"act{i}", commands=("Email:Send",)), *chamadas),
            )
        )
    return bots
