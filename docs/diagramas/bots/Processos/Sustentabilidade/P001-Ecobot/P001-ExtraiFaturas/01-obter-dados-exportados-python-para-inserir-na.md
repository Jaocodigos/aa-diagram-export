# Obter Dados Exportados Python Para Inserir na Fila Processamento

Passo de [P001-ExtraiFaturas](../P001-ExtraiFaturas.md).

```mermaid
flowchart TD
  n74e64b3c(["Obter Dados Exportados Python Para Inserir na Fila Processa…"])
  subgraph ncc3f9c85["Recupera Id Criado Por"]
  n1257acab[["CommonTask/Database/ObterIDUsuario"]]
  end
  subgraph n8baf8126["Bot: Processos/Sustentabilidade/P001-Ecobot/Tarefas/P001_Re…"]
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
  subgraph n71177279["Valida Se tem arquivo na pasta"]
  n117654d2{"Se: pasta não existe: ReturnPadhy"}
  n4e76647c["Pasta: criar"]
  ncf419e6b{"Se: arquivo não existe: ReturnPadhy"}
  n467ddc12["Lançar erro"]
  end
  n035cf381[["Faz loop em cada fatura na pasta"]]
  n671cce4d(["fim do passo"])
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
  n1257acab --> n20622a21
  n117654d2 -->|sim| n4e76647c
  ncf419e6b -->|sim| n467ddc12
  n4e76647c --> ncf419e6b
  n117654d2 -->|não| ncf419e6b
  nde00f30b -->|fim| n117654d2
  n23f41da0 -->|não| n117654d2
  n942d0ee7 --> n117654d2
  nbd6f9525 -->|não| n117654d2
  n467ddc12 --> n035cf381
  ncf419e6b -->|não| n035cf381
  n74e64b3c --> n1257acab
  n035cf381 --> n671cce4d
  classDef acoes stroke:#4c6ef5,stroke-width:1px
  class n2ff971f3,n467ddc12,n4e76647c,n5f9ea6f0,n8c342949,n942d0ee7,nde475e3a acoes
  classDef biblioteca stroke:#1098ad,stroke-width:2px
  class n1257acab,n20622a21,n6932bc92,nc301bf6c biblioteca
  classDef controle stroke:#b26a00,stroke-width:2px
  class n117654d2,n23f41da0,n7af4c5b3,n82eae53b,nbd6f9525,ncf419e6b,nde00f30b controle
  classDef secao stroke:#5f3dc4,stroke-width:2px
  class n035cf381 secao
  click n035cf381 "02-faz-loop-em-cada-fatura-na-pasta.md"
```

---

[Faz loop em cada fatura na pasta](02-faz-loop-em-cada-fatura-na-pasta.md) →
