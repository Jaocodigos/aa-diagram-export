# P001-ExtraiFaturas

| | |
|---|---|
| Caminho no export | `Processos/Sustentabilidade/P001-Ecobot/P001-ExtraiFaturas` |
| Ações | 34 |
| Profundidade de expansão | 3 |

```mermaid
flowchart TD
  nf646c753(["Início: P001-ExtraiFaturas"])
  subgraph n389f8609["Obtem Parametros Padhy"]
  ndd750360[["CommonTask/Inicializar/InicializarConfig"]]
  ncf25640e[["CommonTask/Log/GravarLogBanco"]]
  end
  n86d93f88[["Obter Dados Exportados Python Para Inserir na Fila Processa…"]]
  subgraph n05c9d0ec["Chama Bootstrap com a Automacao P001"]
  subgraph n5f836ae5["Associa Parametros Padhy pra Iniciar Bootstrap"]
  nff34cbc7["Dicionário: gravar chave, Dicionário: gravar chave, Dicioná…"]
  nf3f8ce7b[["CommonTask/Log/GravarLogBanco"]]
  nb7efe7dc["JSON: converter dicionário, Python: abrir script, Python: e…"]
  n95a30dc5[["CommonTask/Log/GravarLogBanco"]]
  end
  end
  n48d5ecc3[["Obter Dados Exportados Python Para Atualizar Fila Processam…"]]
  subgraph n0968cf17["Bot: Processos/Sustentabilidade/P001-Ecobot/Tarefas/P001_Re…"]
  subgraph n5c7b404b["Revisa a fila de procesamento, se ficou item iniciado e nao…"]
  n20622a21[["CommonTask/Database/ObterRegistroFilaDeProcessamento"]]
  n5f9ea6f0["Tabela: contar linhas"]
  n23f41da0{"Se: numRows > ⋯"}
  nde00f30b{"Loop: para cada linha de ReturnFilaProcessamento"}
  nc301bf6c[["CommonTask/Database/AtualizaRegistroProcessamentoAtividade_…"]]
  nde475e3a["Finalizando Fila Processamento"]
  n6932bc92[["CommonTask/Database/ExecutaProcedureGenerica"]]
  n7af4c5b3{"Se: statusExecutaProcedureGenerica = falso ou statusAtualiz…"}
  n2ff971f3["Lançar erro"]
  end
  subgraph nc0eddb24["TRATAR STACK TRACER"]
  n82eae53b{"Se: ErroMensagem contém ⋯"}
  n8c342949["Texto: atribuir"]
  nbd6f9525{"Se: ErroMensagem não contém ⋯"}
  n942d0ee7["Texto: atribuir"]
  end
  end
  subgraph n535e538b["TRATAR STACK TRACER"]
  ne34af22b{"Se: ErroMensagem contém ⋯"}
  n65fc1862["Texto: atribuir"]
  n42e01098{"Se: ErroMensagem não contém ⋯"}
  n9ae7d399["Texto: atribuir"]
  end
  naa17df17["Caixa de mensagem"]
  neee7fd12[["CommonTask/Log/GravarLogBanco"]]
  nb8789d72[["CommonTask/Log/GravarLogBanco"]]
  ned2e05e8(["Fim"])
  ndd750360 --> ncf25640e
  ncf25640e --> n86d93f88
  nff34cbc7 --> nf3f8ce7b
  nf3f8ce7b --> nb7efe7dc
  nb7efe7dc --> n95a30dc5
  n86d93f88 --> nff34cbc7
  n95a30dc5 --> n48d5ecc3
  n20622a21 --> n5f9ea6f0
  nc301bf6c --> nde475e3a
  nde475e3a --> n6932bc92
  n7af4c5b3 -->|sim| n2ff971f3
  n6932bc92 --> n7af4c5b3
  nde00f30b -->|iteração| nc301bf6c
  n2ff971f3 -.->|próxima| nde00f30b
  n7af4c5b3 -.->|próxima| nde00f30b
  n23f41da0 -->|sim| nde00f30b
  n5f9ea6f0 --> n23f41da0
  n82eae53b -->|sim| n8c342949
  nbd6f9525 -->|sim| n942d0ee7
  n8c342949 --> nbd6f9525
  n82eae53b -->|não| nbd6f9525
  n20622a21 -.->|erro| n82eae53b
  n48d5ecc3 --> n20622a21
  ne34af22b -->|sim| n65fc1862
  n42e01098 -->|sim| n9ae7d399
  n65fc1862 --> n42e01098
  ne34af22b -->|não| n42e01098
  n9ae7d399 --> naa17df17
  n42e01098 -->|não| naa17df17
  naa17df17 --> neee7fd12
  ndd750360 -.->|erro| ne34af22b
  nde00f30b -->|fim| nb8789d72
  n23f41da0 -->|não| nb8789d72
  n942d0ee7 --> nb8789d72
  nbd6f9525 -->|não| nb8789d72
  neee7fd12 --> nb8789d72
  nf646c753 --> ndd750360
  nb8789d72 --> ned2e05e8
  classDef acoes stroke:#4c6ef5,stroke-width:1px
  class n2ff971f3,n5f9ea6f0,n65fc1862,n8c342949,n942d0ee7,n9ae7d399,naa17df17,nb7efe7dc,nde475e3a,nff34cbc7 acoes
  classDef biblioteca stroke:#1098ad,stroke-width:2px
  class n20622a21,n6932bc92,n95a30dc5,nb8789d72,nc301bf6c,ncf25640e,ndd750360,neee7fd12,nf3f8ce7b biblioteca
  classDef controle stroke:#b26a00,stroke-width:2px
  class n23f41da0,n42e01098,n7af4c5b3,n82eae53b,nbd6f9525,nde00f30b,ne34af22b controle
  classDef secao stroke:#5f3dc4,stroke-width:2px
  class n48d5ecc3,n86d93f88 secao
  click n86d93f88 "Subtasks/01-obter-dados-exportados-python-para-inserir-na.md"
  click n48d5ecc3 "Subtasks/03-obter-dados-exportados-python-para-atualizar.md"
```

## Passos detalhados

| | Passo | Nós |
|---|---|---|
| 1 | [Obter Dados Exportados Python Para Inserir na Fila Processamento](Subtasks/01-obter-dados-exportados-python-para-inserir-na.md) | 21 |
| 2 | [Faz loop em cada fatura na pasta](Subtasks/02-faz-loop-em-cada-fatura-na-pasta.md) | 22 |
| 3 | [Obter Dados Exportados Python Para Atualizar Fila Processamento](Subtasks/03-obter-dados-exportados-python-para-atualizar.md) | 24 |
| 4 | [Obtem Item Fila Processamento e intera sobre o excel exportado](Subtasks/04-obtem-item-fila-processamento-e-intera-sobre-o.md) | 12 |

## Variáveis

| Nome | Tipo | Entrada | Saída |
|---|---|---|---|
| `InputParametrosPython` | Dictionary | — | — |
| `ReturnPadhy` | Dictionary | — | — |
| `JsonPythonOutput` | String | — | — |
| `statusGestaoAtividade` | Boolean | — | — |
| `ValuesInsertFilaProcessamento` | String | — | — |
| `FilesInFolder` | Dictionary | — | — |
| `IdUser` | String | — | — |
| `NomeArquivo` | String | — | — |
| `MesAno` | String | — | — |
| `TipoFatura` | String | — | — |
| `IdRegistroAtividadeFilaProcessamento` | String | — | — |
| `IdFilaProcessamento` | String | — | — |
| `ReturnFilaProcessamento` | Table | — | — |
| `rowFilaProcessamento` | Record | — | — |
| `ListIdFilaProcessamento` | List | — | — |
| `ErroMensagem` | String | — | — |
| `EncontrouRegistros` | Boolean | — | — |
| `ErroLinha` | Number | — | — |
| `TableExcelExport` | Table | — | — |
| `rowExcelExport` | Record | — | — |
| `rowIndexFilaProcessamento` | Number | — | — |
| `TableAuxiliarFilaProcessamento` | Table | — | — |
| `rowTableAuxiliarFilaProcessamento` | Record | — | — |
| `statusAtualizarAtividade` | Boolean | — | — |
| `Query` | String | — | — |
| `InputsTask` | String | — | — |
| `JsonPythonInput` | String | — | — |
| `returnPython` | Dictionary | — | — |
| `status_execucao` | Number | — | — |

## Chamadas

Nome e tipo dos parâmetros. O valor passado não aparece: numa entrada ele é uma expressão que pode carregar literal (§9).

| Bot | Direção | Parâmetro | Tipo | Variável no chamador |
|---|---|---|---|---|
| `CommonTask/Inicializar/InicializarConfig` | entrada | `BotName` | String | ⋯ |
|  | saída | `Return` | Dictionary | `ReturnPadhy` |
| `CommonTask/Log/GravarLogBanco` | entrada | `NomeBot` | String | `ReturnPadhy` |
|  | entrada | `IdProcesso` | String | `ReturnPadhy` |
|  | entrada | `Mensagem` | String | ⋯ |
|  | entrada | `IdArea` | String | `ReturnPadhy` |
|  | entrada | `TipoLog` | Boolean | ⋯ |
| `CommonTask/Database/ObterIDUsuario` | entrada | `ObterViaEmailHypera` | Boolean | ⋯ |
|  | saída | `IdUser` | String | `IdUser` |
| `Processos/Sustentabilidade/P001-Ecobot/Tarefas/P001_RevisaFilaProcessamento` | entrada | `ReturnPadhy` | Dictionary | `ReturnPadhy` |
|  | entrada | `IdUser` | String | `IdUser` |
|  | entrada | `ReturnFilaProcessamento` | Table | `ReturnFilaProcessamento` |
|  | entrada | `TableAuxiliarFilaProcessamento` | Table | `TableAuxiliarFilaProcessamento` |
|  | entrada | `IdStatusExecucao` | String | ⋯ |
|  | entrada | `DescricaoErro` | String | ⋯ |
| `CommonTask/Database/InserirItemFilaProcessamento` | entrada | `ReturnTablePadhy` | Dictionary | `ReturnPadhy` |
|  | entrada | `QueryCallProcedure` | String | `ReturnPadhy` |
|  | saída | `ErroMensagem` | String | `ErroMensagem` |
| `CommonTask/Database/ObterRegistroFilaDeProcessamento` | entrada | `ProcedureNome` | String | `ReturnPadhy` |
|  | entrada | `DiretorioTemp` | String | `ReturnPadhy` |
|  | saída | `EncontrouRegistros` | Boolean | `EncontrouRegistros` |
|  | saída | `Return` | Table | `ReturnFilaProcessamento` |
| `CommonTask/Log/GravarLogBanco` | entrada | `NomeBot` | String | `ReturnPadhy` |
|  | entrada | `IdProcesso` | String | `ReturnPadhy` |
|  | entrada | `Mensagem` | String | `NomeArquivo` |
|  | entrada | `IdArea` | String | `ReturnPadhy` |
|  | entrada | `TipoLog` | Boolean | ⋯ |
| `CommonTask/Database/CriaRegistroProcessamentoAtividade` | entrada | `IdFilaProcessamento` | String | `IdFilaProcessamento` |
|  | entrada | `CodigoAtividade` | String | `ReturnPadhy` |
|  | saída | `IdRegistroAtividadeFilaProcessamento` | String | `IdRegistroAtividadeFilaProcessamento` |
| `CommonTask/Log/GravarLogBanco` | entrada | `NomeBot` | String | `ReturnPadhy` |
|  | entrada | `IdProcesso` | String | `ReturnPadhy` |
|  | entrada | `Mensagem` | String | `InputParametrosPython` |
|  | entrada | `IdArea` | String | `ReturnPadhy` |
|  | entrada | `TipoLog` | Boolean | ⋯ |
| `CommonTask/Log/GravarLogBanco` | entrada | `NomeBot` | String | `ReturnPadhy` |
|  | entrada | `IdProcesso` | String | `ReturnPadhy` |
|  | entrada | `Mensagem` | String | `returnPython` |
|  | entrada | `IdArea` | String | `ReturnPadhy` |
|  | entrada | `TipoLog` | Boolean | ⋯ |
| `CommonTask/Log/GravarLogBanco` | entrada | `NomeBot` | String | `ReturnPadhy` |
|  | entrada | `IdProcesso` | String | `ReturnPadhy` |
|  | entrada | `Mensagem` | String | `ReturnPadhy` |
|  | entrada | `IdArea` | String | `ReturnPadhy` |
|  | entrada | `TipoLog` | Boolean | ⋯ |
| `CommonTask/Database/AtualizaRegistroProcessamentoAtividade_v2` | entrada | `IdRegistroAtividadeFilaProcessamento` | String | `rowTableAuxiliarFilaProcessamento` |
|  | entrada | `IdStatusExecucaoAtividade` | String | ⋯ |
|  | entrada | `AtividadeStatusMensagem` | String | ⋯ |
|  | saída | `statusAtualizarAtividade` | Boolean | `statusAtualizarAtividade` |
| `CommonTask/Database/ExecutaProcedureGenerica` | entrada | `NomeProcedure` | String | `ReturnPadhy` |
|  | entrada | `ParamentrosProcedure` | String | `ValuesInsertFilaProcessamento` |
| `Processos/Sustentabilidade/P001-Ecobot/Tarefas/P001_RevisaFilaProcessamento` | entrada | `ReturnPadhy` | Dictionary | `ReturnPadhy` |
|  | entrada | `IdUser` | String | `IdUser` |
|  | entrada | `ReturnFilaProcessamento` | Table | `ReturnFilaProcessamento` |
|  | entrada | `TableAuxiliarFilaProcessamento` | Table | `TableAuxiliarFilaProcessamento` |
|  | entrada | `IdStatusExecucao` | String | ⋯ |
|  | entrada | `DescricaoErro` | String | `returnPython` |
| `Processos/Sustentabilidade/P001-Ecobot/Tarefas/P001_RevisaFilaProcessamento` | entrada | `ReturnPadhy` | Dictionary | `ReturnPadhy` |
|  | entrada | `IdUser` | String | `IdUser` |
|  | entrada | `ReturnFilaProcessamento` | Table | `ReturnFilaProcessamento` |
|  | entrada | `TableAuxiliarFilaProcessamento` | Table | `TableAuxiliarFilaProcessamento` |
|  | entrada | `IdStatusExecucao` | String | ⋯ |
|  | entrada | `DescricaoErro` | String | ⋯ |
| `CommonTask/Log/GravarLogBanco` | entrada | `NomeBot` | String | `ReturnPadhy` |
|  | entrada | `IdProcesso` | String | `ReturnPadhy` |
|  | entrada | `Mensagem` | String | `ErroMensagem` |
|  | entrada | `IdArea` | String | `ReturnPadhy` |
|  | entrada | `TipoLog` | Boolean | ⋯ |
| `CommonTask/Log/GravarLogBanco` | entrada | `NomeBot` | String | `ReturnPadhy` |
|  | entrada | `IdProcesso` | String | `ReturnPadhy` |
|  | entrada | `Mensagem` | String | `System` |
|  | entrada | `IdArea` | String | `ReturnPadhy` |
|  | entrada | `TipoLog` | Boolean | ⋯ |

## Dependências

Bots chamados:

- `CommonTask/Inicializar/InicializarConfig`
- `CommonTask/Log/GravarLogBanco`
- `CommonTask/Database/ObterIDUsuario`
- `Processos/Sustentabilidade/P001-Ecobot/Tarefas/P001_RevisaFilaProcessamento`
- `CommonTask/Database/InserirItemFilaProcessamento`
- `CommonTask/Database/ObterRegistroFilaDeProcessamento`
- `CommonTask/Database/CriaRegistroProcessamentoAtividade`
- `CommonTask/Database/AtualizaRegistroProcessamentoAtividade_v2`
- `CommonTask/Database/ExecutaProcedureGenerica`

Pacotes usados: `Comment`, `DataTable`, `Dictionary`, `ErrorHandler`, `Excel`, `File`, `Folder`, `If`, `JSONParser`, `LegacyAutomation`, `List`, `Loop`, `MessageBox`, `Number`, `Python`, `Step`, `String`, `System`, `TaskBot`
