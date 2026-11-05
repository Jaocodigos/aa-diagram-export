"""Renderiza o modelo em Mermaid e nas páginas Markdown (§4 e §7 da spec).

Este arquivo é o único que conhece a sintaxe do Mermaid. Ele lê o modelo e não
escreve nada nele, então um renderer de DrawIO entra ao lado deste sem tocar
em nenhuma outra camada.

A travessia é uma função recursiva com `match` (§6.1). O contrato interno é:
cada nó devolve `(entrada, saidas)` — o id por onde o fluxo entra nele e a
lista de ids que ainda precisam de uma aresta para o que vem depois. Quem
monta a sequência é que liga as pontas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath

from .config import Dictionary
from .model import (
    ActionBlock,
    Bot,
    Break,
    CallBot,
    CallState,
    Continue,
    If,
    Loop,
    LoopKind,
    Node,
    Step,
    TryCatch,
    action_count,
    called_bots,
    stable_node_id,
)

LIMITE_ROTULO = 60
MAX_COMANDOS_NO_ROTULO = 3

TEXTO_DE_LOOP = {
    LoopKind.FOR_EACH: "para cada",
    LoopKind.N_TIMES: "repetir",
    LoopKind.WHILE: "enquanto",
}

# (id do nó, rótulo da aresta que sai dele)
Saida = tuple[str, str | None]


def escape(texto: str) -> str:
    """Deixa o texto seguro dentro de um rótulo Mermaid (§7, escape de rótulo).

    O `#` vem primeiro de propósito: ele é o prefixo de entidade do Mermaid, e
    trocá-lo depois estragaria o `#quot;` que a aspas gera.
    """
    limpo = " ".join(str(texto).split())
    limpo = limpo.replace("#", "#35;").replace('"', "#quot;").replace("|", "/")
    if len(limpo) > LIMITE_ROTULO:
        limpo = limpo[: LIMITE_ROTULO - 1].rstrip() + "…"
    return limpo


@dataclass
class _Canvas:
    """Acumula o diagrama de um bot enquanto a travessia acontece.

    Declarações e arestas vão para listas separadas porque `subgraph` precisa
    envolver só as declarações. Aresta dentro de subgraph faz o Mermaid
    agrupar o que não devia.
    """

    dic: Dictionary
    decls: list[str] = field(default_factory=list)
    edges: list[str] = field(default_factory=list)
    classes: dict[str, list[str]] = field(default_factory=dict)
    unknown_commands: set[str] = field(default_factory=set)

    # --- infraestrutura ---

    def classify(self, node_id: str, nome_da_classe: str) -> None:
        self.classes.setdefault(nome_da_classe, []).append(node_id)

    def link(self, saidas: list[Saida], destino: str) -> None:
        for origem, rotulo in saidas:
            if rotulo:
                self.edges.append(f"  {origem} -->|{rotulo}| {destino}")
            else:
                self.edges.append(f"  {origem} --> {destino}")

    def _placeholder(self, uid: str, texto: str) -> tuple[str, list[Saida]]:
        """Nó de preenchimento para bloco vazio, para o fluxo não quebrar."""
        nid = stable_node_id(uid)
        self.decls.append(f'  {nid}["{escape(texto)}"]')
        self.classify(nid, "acoes")
        return nid, [(nid, None)]

    # --- travessia ---

    def sequence(self, nodes) -> tuple[str | None, list[Saida]]:
        """Liga os nós de um corpo em sequência.

        Devolve (None, []) para corpo vazio; quem chama trata esse caso.
        """
        entrada: str | None = None
        pendentes: list[Saida] = []
        for node in nodes:
            no_entrada, no_saidas = self.node(node)
            if entrada is None:
                entrada = no_entrada
            else:
                self.link(pendentes, no_entrada)
            pendentes = no_saidas
        return entrada, pendentes

    def node(self, n: Node) -> tuple[str, list[Saida]]:
        match n:
            case ActionBlock():
                return self._action_block(n)
            case If():
                return self._if(n)
            case Loop():
                return self._loop(n)
            case TryCatch():
                return self._try(n)
            case Step():
                return self._step(n)
            case CallBot():
                return self._call(n)
            case Break():
                nid = n.node_id
                self.decls.append(f'  {nid}(["sair do loop"])')
                self.classify(nid, "controle")
                # Sem saída: o fluxo depois de um Break não continua na
                # sequência. Ligar na saída do loop exigiria carregar o
                # contexto do loop na travessia; ficou fora do MVP.
                return nid, []
            case Continue():
                nid = n.node_id
                self.decls.append(f'  {nid}(["próxima iteração"])')
                self.classify(nid, "controle")
                return nid, []
            case _:
                raise TypeError(
                    f"o render não conhece este tipo de nó: {type(n).__name__}. "
                    "Tipo novo no modelo pede um case novo aqui."
                )

    def _action_block(self, n: ActionBlock) -> tuple[str, list[Saida]]:
        nid = n.node_id
        self.decls.append(f'  {nid}["{escape(self._block_label(n))}"]')
        self.classify(nid, "acoes")
        return nid, [(nid, None)]

    def _block_label(self, n: ActionBlock) -> str:
        """Rótulo do bloco: o que o dev escreveu, ou os comandos resumidos.

        Só registra como "sem rótulo cadastrado" o comando que de fato vai
        aparecer cru no diagrama. Num bloco que o dev nomeou, nome de comando
        nenhum aparece, então listá-lo no index.md seria dizer ao time para
        cadastrar um rótulo que ninguém vai ver.
        """
        if n.label:
            return n.label

        amigaveis: list[str] = []
        for comando in n.commands[:MAX_COMANDOS_NO_ROTULO]:
            apelido = self.dic.friendly(comando)
            if apelido is None:
                self.unknown_commands.add(comando)
                apelido = comando
            amigaveis.append(apelido)

        if not amigaveis:
            return "ações"
        texto = ", ".join(amigaveis)
        resto = len(n.commands) - MAX_COMANDOS_NO_ROTULO
        return f"{texto} (+{resto})" if resto > 0 else texto

    def _if(self, n: If) -> tuple[str, list[Saida]]:
        if not n.branches:
            return self._placeholder(f"{n.uid}:if-vazio", "Se: (sem condição)")

        saidas: list[Saida] = []
        entrada: str | None = None
        falso_pendente: str | None = None

        for i, branch in enumerate(n.branches):
            did = stable_node_id(f"{n.uid}:branch{i}")
            prefixo = "Se" if i == 0 else "Senão se"
            self.decls.append(
                f'  {did}{{"{escape(f"{prefixo}: {branch.condition}")}"}}'
            )
            self.classify(did, "controle")
            if entrada is None:
                entrada = did
            if falso_pendente is not None:
                self.edges.append(f"  {falso_pendente} -->|não| {did}")

            corpo_entrada, corpo_saidas = self.sequence(branch.body)
            if corpo_entrada is None:
                saidas.append((did, "sim"))
            else:
                self.edges.append(f"  {did} -->|sim| {corpo_entrada}")
                saidas.extend(corpo_saidas)
            falso_pendente = did

        senao_entrada, senao_saidas = self.sequence(n.else_body)
        if senao_entrada is not None:
            self.edges.append(f"  {falso_pendente} -->|não| {senao_entrada}")
            saidas.extend(senao_saidas)
        else:
            saidas.append((falso_pendente, "não"))

        assert entrada is not None
        return entrada, saidas

    def _loop(self, n: Loop) -> tuple[str, list[Saida]]:
        cabeca = n.node_id
        texto = f"Loop: {TEXTO_DE_LOOP[n.kind]} {n.expression}".strip()
        self.decls.append(f'  {cabeca}{{"{escape(texto)}"}}')
        self.classify(cabeca, "controle")

        corpo_entrada, corpo_saidas = self.sequence(n.body)
        if corpo_entrada is not None:
            self.edges.append(f"  {cabeca} -->|iteração| {corpo_entrada}")
            for origem, _ in corpo_saidas:
                self.edges.append(f"  {origem} -.->|próxima| {cabeca}")
        return cabeca, [(cabeca, "fim")]

    def _try(self, n: TryCatch) -> tuple[str, list[Saida]]:
        try_entrada, try_saidas = self.sequence(n.try_body)
        if try_entrada is None:
            try_entrada, try_saidas = self._placeholder(
                f"{n.uid}:try-vazio", "Try: (vazio)"
            )

        catch_entrada, catch_saidas = self.sequence(n.catch_body)
        if catch_entrada is not None:
            self.edges.append(f"  {try_entrada} -.->|erro| {catch_entrada}")

        finally_entrada, finally_saidas = self.sequence(n.finally_body)
        if finally_entrada is not None:
            self.link(try_saidas, finally_entrada)
            self.link(catch_saidas, finally_entrada)
            return try_entrada, finally_saidas

        return try_entrada, try_saidas + catch_saidas

    def _step(self, n: Step) -> tuple[str, list[Saida]]:
        sid = stable_node_id(f"{n.uid}:step")
        self.decls.append(f'  subgraph {sid}["{escape(n.title or "Step")}"]')
        entrada, saidas = self.sequence(n.body)
        if entrada is None:
            entrada, saidas = self._placeholder(f"{n.uid}:step-vazio", "(step vazio)")
        self.decls.append("  end")
        return entrada, saidas

    def _call(self, n: CallBot) -> tuple[str, list[Saida]]:
        nid = n.node_id
        match n.state:
            case CallState.EXPANDED:
                sid = stable_node_id(f"{n.uid}:call")
                rotulo = escape(f"Bot: {n.target_path}")
                self.decls.append(f'  subgraph {sid}["{rotulo}"]')
                entrada, saidas = self.sequence(n.body)
                if entrada is None:
                    entrada, saidas = self._placeholder(
                        f"{n.uid}:call-vazio", "(bot sem ações)"
                    )
                self.decls.append("  end")
                return entrada, saidas
            case CallState.CYCLE:
                texto = f"recursão: {n.target_path}"
                self.decls.append(f'  {nid}[["{escape(texto)}"]]')
                self.classify(nid, "limite")
            case CallState.DEPTH_LIMIT:
                texto = f"limite de profundidade: {n.target_path}"
                self.decls.append(f'  {nid}[["{escape(texto)}"]]')
                self.classify(nid, "limite")
            case CallState.DYNAMIC_TARGET:
                texto = f"alvo dinâmico: {n.target_path}"
                self.decls.append(f'  {nid}[/"{escape(texto)}"/]')
                self.classify(nid, "nao_resolvido")
            case _:
                texto = f"{n.target_path} — não encontrado no export"
                self.decls.append(f'  {nid}[/"{escape(texto)}"/]')
                self.classify(nid, "nao_resolvido")
        return nid, [(nid, None)]

    def class_lines(self) -> list[str]:
        """Estilo por categoria, lido do dicionario.toml.

        Só contorno, sem `fill`: preenchimento forte com texto escuro é o modo
        mais comum de um diagrama Mermaid ficar ilegível em um dos dois temas
        do GitHub (§7, estilo).
        """
        linhas: list[str] = []
        for nome in sorted(self.classes):
            ids = sorted(set(self.classes[nome]))
            estilo = self.dic.style.get(nome)
            if not estilo or not ids:
                continue
            linhas.append(f"  classDef {nome} {estilo}")
            linhas.append(f"  class {','.join(ids)} {nome}")
        return linhas


#: O Mermaid recusa um diagrama com mais de 500 arestas, e `maxEdges` é
#: configuração segura: não dá para elevar de dentro do diagrama. Como o
#: GitHub renderiza com o padrão, passar disso significa diagrama que
#: simplesmente não aparece. A margem deixa espaço para as arestas de início
#: e fim. Medido num export real: o bot orquestrador passa de 500 ao expandir
#: as subtarefas em profundidade 2.
LIMITE_DE_ARESTAS = 480


@dataclass(frozen=True)
class Diagram:
    """O diagrama de um bot, com o que o chamador precisa saber sobre ele."""

    mermaid: str
    unknown_commands: frozenset[str]
    edge_count: int

    @property
    def too_big(self) -> bool:
        return self.edge_count > LIMITE_DE_ARESTAS


def bot_diagram(bot: Bot, dic: Dictionary) -> Diagram:
    """Diagrama de fluxo de um bot."""
    canvas = _Canvas(dic=dic)
    inicio = stable_node_id(f"{bot.path}:inicio")
    fim = stable_node_id(f"{bot.path}:fim")

    canvas.decls.append(f'  {inicio}(["{escape(f"Início: {bot.name}")}"])')
    entrada, saidas = canvas.sequence(bot.body)
    canvas.decls.append(f'  {fim}(["Fim"])')

    if entrada is None:
        canvas.edges.append(f"  {inicio} --> {fim}")
    else:
        canvas.edges.append(f"  {inicio} --> {entrada}")
        canvas.link(saidas, fim)

    linhas = ["flowchart TD", *canvas.decls, *canvas.edges, *canvas.class_lines()]
    return Diagram(
        mermaid="\n".join(linhas),
        unknown_commands=frozenset(canvas.unknown_commands),
        edge_count=len(canvas.edges),
    )


def call_graph(bots: list[Bot], dic: Dictionary) -> str:
    """Grafo de chamadas entre bots, para o index.md.

    Espera os bots como saíram do parser, antes da expansão do resolver. Com
    bots já expandidos, as chamadas das subtarefas apareceriam como se fossem
    do chamador.
    """
    ids: dict[str, str] = {}

    def nid(caminho: str) -> str:
        if caminho not in ids:
            ids[caminho] = stable_node_id(f"bot:{caminho}")
        return ids[caminho]

    conhecidos = {bot.path for bot in bots}
    arestas: list[str] = []
    externos: set[str] = set()

    for bot in bots:
        for alvo in called_bots(bot):
            if alvo not in conhecidos:
                externos.add(alvo)
            aresta = f"  {nid(bot.path)} --> {nid(alvo)}"
            if aresta not in arestas:
                arestas.append(aresta)

    linhas = ["flowchart LR"]
    for bot in bots:
        linhas.append(f'  {nid(bot.path)}["{escape(bot.name)}"]')
    for alvo in sorted(externos):
        linhas.append(f'  {nid(alvo)}[/"{escape(f"{alvo} — não encontrado")}"/]')
    linhas.extend(arestas)

    if externos:
        estilo = dic.style.get("nao_resolvido")
        if estilo:
            linhas.append(f"  classDef nao_resolvido {estilo}")
            ausentes = ",".join(nid(a) for a in sorted(externos))
            linhas.append(f"  class {ausentes} nao_resolvido")
    return "\n".join(linhas)


def page_relpath(bot: Bot) -> str:
    """Caminho do .md do bot dentro do diretório de saída, espelhando o export."""
    partes = [p for p in PurePosixPath(bot.path.replace("\\", "/")).parts if p not in (".", "/")]
    seguro = [_slug(p) for p in partes] or [_slug(bot.name)]
    return str(PurePosixPath("bots", *seguro)) + ".md"


def _slug(texto: str) -> str:
    proibidos = '<>:"|?*'
    return "".join("_" if c in proibidos else c for c in texto).strip() or "sem_nome"


def bot_page(
    bot: Bot,
    dic: Dictionary,
    *,
    diagram: Diagram,
    depth_used: int,
    depth_requested: int | None = None,
) -> str:
    """Página Markdown de um bot (§4)."""
    chamados = called_bots(bot)
    linhas = [
        f"# {bot.name}",
        "",
        "| | |",
        "|---|---|",
        f"| Caminho no export | `{bot.path}` |",
        f"| Ações | {action_count(bot)} |",
        f"| Profundidade de expansão | {depth_used} |",
        "",
    ]

    if depth_requested is not None and depth_requested > depth_used:
        linhas += [
            f"> Expandido até a profundidade {depth_used}, e não {depth_requested}: "
            f"o diagrama completo passava do limite de {LIMITE_DE_ARESTAS} arestas "
            "do Mermaid e não renderizaria. Os bots chamados têm diagrama próprio, "
            "linkado em Dependências.",
            "",
        ]
    elif diagram.too_big:
        linhas += [
            f"> Atenção: {diagram.edge_count} arestas, acima do limite do Mermaid. "
            "Este diagrama pode não renderizar no GitHub mesmo sem expansão.",
            "",
        ]

    linhas += [
        "```mermaid",
        diagram.mermaid,
        "```",
        "",
    ]

    if bot.variables:
        linhas += ["## Variáveis", "", "| Nome | Tipo | Entrada | Saída |", "|---|---|---|---|"]
        for v in bot.variables:
            linhas.append(
                f"| `{v.name}` | {v.type or '—'} | {'sim' if v.is_input else '—'} "
                f"| {'sim' if v.is_output else '—'} |"
            )
        linhas.append("")

    linhas += ["## Dependências", ""]
    if chamados:
        linhas.append("Bots chamados:")
        linhas.append("")
        for alvo in chamados:
            linhas.append(f"- `{alvo}`")
    else:
        linhas.append("Não chama outros bots.")
    linhas.append("")
    if bot.packages:
        linhas.append("Pacotes usados: " + ", ".join(f"`{p}`" for p in bot.packages))
        linhas.append("")

    return "\n".join(linhas)


def index_page(
    bots: list[Bot],
    dic: Dictionary,
    *,
    unresolved: dict[str, list[str]] | None = None,
    unknown_commands: set[str] | None = None,
    ignored_files: int = 0,
    include_call_graph: bool = True,
    depth_reduced: dict[str, tuple[int, int]] | None = None,
) -> str:
    """Página de entrada: grafo de chamadas, inventário e pendências (§4)."""
    unresolved = unresolved or {}
    unknown_commands = unknown_commands or set()

    linhas = [
        "# Diagramas dos bots",
        "",
        f"{len(bots)} bot(s) no export.",
        "",
    ]

    if include_call_graph:
        linhas += [
            "## Grafo de chamadas",
            "",
            "```mermaid",
            call_graph(bots, dic),
            "```",
            "",
        ]

    linhas += [
        "## Inventário",
        "",
        "| Bot | Ações | Chama | Diagrama |",
        "|---|---|---|---|",
    ]
    for bot in sorted(bots, key=lambda b: b.path):
        linhas.append(
            f"| `{bot.path}` | {action_count(bot)} | {len(called_bots(bot))} "
            f"| [abrir]({page_relpath(bot)}) |"
        )
    linhas.append("")

    linhas += ["## Pendências", ""]
    algo = False

    if unresolved:
        algo = True
        linhas += ["### Bots referenciados e não encontrados no export", ""]
        for alvo in sorted(unresolved):
            quem = ", ".join(f"`{c}`" for c in sorted(unresolved[alvo]))
            linhas.append(f"- `{alvo}` — chamado por {quem}")
        linhas.append("")

    if unknown_commands:
        algo = True
        linhas += [
            "### Comandos sem rótulo no dicionario.toml",
            "",
            "Aparecem no diagrama com o nome cru do A360. Cadastrar em "
            "`[comandos_amigaveis]`:",
            "",
        ]
        for comando in sorted(unknown_commands):
            linhas.append(f'- `"{comando}"`')
        linhas.append("")

    if depth_reduced:
        algo = True
        linhas += [
            "### Bots com expansão reduzida",
            "",
            f"O diagrama completo passava do limite de {LIMITE_DE_ARESTAS} arestas "
            "do Mermaid, que não renderiza acima disso. Cada bot chamado tem o "
            "diagrama próprio, linkado na página do chamador.",
            "",
        ]
        for caminho in sorted(depth_reduced):
            usada, pedida = depth_reduced[caminho]
            linhas.append(f"- `{caminho}` — expandido até {usada}, e não {pedida}")
        linhas.append("")

    if ignored_files:
        algo = True
        linhas.append(f"- {ignored_files} arquivo(s) do export ignorado(s) por não serem bots.")
        linhas.append("")

    if not algo:
        linhas += ["Nenhuma.", ""]

    return "\n".join(linhas)
