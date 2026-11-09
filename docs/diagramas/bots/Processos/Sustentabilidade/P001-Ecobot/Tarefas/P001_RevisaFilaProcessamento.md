# P001_RevisaFilaProcessamento

| | |
|---|---|
| Caminho no export | `Processos/Sustentabilidade/P001-Ecobot/Tarefas/P001_RevisaFilaProcessamento` |
| Ações | 5 |
| Profundidade de expansão | 3 |

```mermaid
flowchart TD
  nb64b7c7f(["Início: P001_RevisaFilaProcessamento"])
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
  n65d1c76f(["Fim"])
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
  nb64b7c7f --> n20622a21
  nde00f30b -->|fim| n65d1c76f
  n23f41da0 -->|não| n65d1c76f
  n942d0ee7 --> n65d1c76f
  nbd6f9525 -->|não| n65d1c76f
  classDef acoes stroke:#4c6ef5,stroke-width:1px
  class n2ff971f3,n5f9ea6f0,n8c342949,n942d0ee7,nde475e3a acoes
  classDef biblioteca stroke:#1098ad,stroke-width:2px
  class n20622a21,n6932bc92,nc301bf6c biblioteca
  classDef controle stroke:#b26a00,stroke-width:2px
  class n23f41da0,n7af4c5b3,n82eae53b,nbd6f9525,nde00f30b controle
```

## Variáveis

| Nome | Tipo | Entrada | Saída |
|---|---|---|---|
| `SampleNumber` | Number | — | — |
| `SampleString` | String | — | — |
| `ErroMensagem` | String | — | — |
| `ErroLinha` | Number | — | — |
| `Query` | String | — | — |
| `InputsTask` | String | — | — |
| `ReturnPadhy` | Dictionary | sim | — |
| `ValuesInsertFilaProcessamento` | String | — | — |
| `IdUser` | String | sim | — |
| `ReturnFilaProcessamento` | Table | sim | — |
| `rowFilaProcessamento` | Record | — | — |
| `EncontrouRegistros` | Boolean | — | — |
| `TableAuxiliarFilaProcessamento` | Table | sim | — |
| `rowTableAuxiliarFilaProcessamento` | Record | — | — |
| `statusAtualizarAtividade` | Boolean | — | — |
| `numRows` | Number | — | — |
| `statusExecutaProcedureGenerica` | Boolean | — | — |
| `MensagemOutput` | String | — | — |
| `TableExport` | Table | — | — |
| `IdStatusExecucao` | String | sim | — |
| `DescricaoErro` | String | sim | — |

## Chamadas

Nome e tipo dos parâmetros. O valor passado não aparece: numa entrada ele é uma expressão que pode carregar literal (§9).

| Bot | Direção | Parâmetro | Tipo | Variável no chamador |
|---|---|---|---|---|
| `CommonTask/Database/ObterRegistroFilaDeProcessamento` | entrada | `ProcedureNome` | String | `ReturnPadhy` |
|  | entrada | `DiretorioTemp` | String | `ReturnPadhy` |
|  | saída | `EncontrouRegistros` | Boolean | `EncontrouRegistros` |
|  | saída | `Return` | Table | `ReturnFilaProcessamento` |
| `CommonTask/Database/AtualizaRegistroProcessamentoAtividade_v2` | entrada | `IdRegistroAtividadeFilaProcessamento` | String | `rowFilaProcessamento` |
|  | entrada | `IdStatusExecucaoAtividade` | String | ⋯ |
|  | entrada | `AtividadeStatusMensagem` | String | ⋯ |
|  | saída | `statusAtualizarAtividade` | Boolean | `statusAtualizarAtividade` |
| `CommonTask/Database/ExecutaProcedureGenerica` | entrada | `NomeProcedure` | String | `ReturnPadhy` |
|  | entrada | `ParamentrosProcedure` | String | `ValuesInsertFilaProcessamento` |
|  | saída | `statusExecutaProcedureGenerica` | Boolean | `statusExecutaProcedureGenerica` |
|  | saída | `MensagemOutput` | String | `MensagemOutput` |
|  | saída | `TableExport` | Table | `TableExport` |

## Dependências

Bots chamados:

- `CommonTask/Database/ObterRegistroFilaDeProcessamento`
- `CommonTask/Database/AtualizaRegistroProcessamentoAtividade_v2`
- `CommonTask/Database/ExecutaProcedureGenerica`

Pacotes usados: `Boolean`, `Comment`, `DataTable`, `ErrorHandler`, `If`, `Loop`, `Number`, `Step`, `String`, `System`, `TaskBot`
