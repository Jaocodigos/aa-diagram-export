# Obter Dados Exportados Python Para Atualizar Fila Processamento

Passo de [P001-ExtraiFaturas](../P001-ExtraiFaturas.md).

```mermaid
flowchart TD
  n82a07a49(["Obter Dados Exportados Python Para Atualizar Fila Processam…"])
  nbc1b569f{"Se: dicionário tem a chave: returnPython"}
  n4e4c02bb["Número: atribuir"]
  subgraph ne0169f49["Copia do Local para Rede"]
  n73e3d4cd{"Se: arquivo existe: ReturnPadhy"}
  n1bc4cb28["Arquivo: copiar, Pasta: copiar"]
  n023c842f[["CommonTask/Log/GravarLogBanco"]]
  end
  subgraph n43de4adf["Obtem DataTable do excel exportado"]
  n443dda21{"Se: arquivo não existe: ReturnPadhy"}
  n73cc3693["Lançar erro"]
  n21c59285["Excel: abrir planilha, Excel: ler intervalo, Excel: fechar…"]
  end
  nf953f845[["Obtem Item Fila Processamento e intera sobre o excel export…"]]
  subgraph n02ab4f44["Bot: Processos/Sustentabilidade/P001-Ecobot/Tarefas/P001_Re…"]
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
  n9c576c09(["fim do passo"])
  n1bc4cb28 --> n023c842f
  n73e3d4cd -->|sim| n1bc4cb28
  n4e4c02bb --> n73e3d4cd
  n443dda21 -->|sim| n73cc3693
  n73cc3693 --> n21c59285
  n443dda21 -->|não| n21c59285
  n023c842f --> n443dda21
  n73e3d4cd -->|não| n443dda21
  n21c59285 --> nf953f845
  nbc1b569f -->|sim| n4e4c02bb
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
  nbc1b569f -->|não| n20622a21
  n82a07a49 --> nbc1b569f
  nf953f845 --> n9c576c09
  nde00f30b -->|fim| n9c576c09
  n23f41da0 -->|não| n9c576c09
  n942d0ee7 --> n9c576c09
  nbd6f9525 -->|não| n9c576c09
  classDef acoes stroke:#4c6ef5,stroke-width:1px
  class n1bc4cb28,n21c59285,n2ff971f3,n4e4c02bb,n5f9ea6f0,n73cc3693,n8c342949,n942d0ee7,nde475e3a acoes
  classDef biblioteca stroke:#1098ad,stroke-width:2px
  class n023c842f,n20622a21,n6932bc92,nc301bf6c biblioteca
  classDef controle stroke:#b26a00,stroke-width:2px
  class n23f41da0,n443dda21,n73e3d4cd,n7af4c5b3,n82eae53b,nbc1b569f,nbd6f9525,nde00f30b controle
  classDef secao stroke:#5f3dc4,stroke-width:2px
  class nf953f845 secao
  click nf953f845 "04-obtem-item-fila-processamento-e-intera-sobre-o.md"
```

---

← [Faz loop em cada fatura na pasta](02-faz-loop-em-cada-fatura-na-pasta.md) · [Obtem Item Fila Processamento e intera sobre o excel exportado](04-obtem-item-fila-processamento-e-intera-sobre-o.md) →
