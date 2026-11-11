# Obtem Item Fila Processamento e intera sobre o excel exportado

Passo de [P001-ExtraiFaturas](../README.md).

```mermaid
flowchart TD
  na1e7d966(["Obtem Item Fila Processamento e intera sobre o excel export…"])
  nce42b9a8{"Loop: para cada linha de ReturnFilaProcessamento"}
  n11329eb9["Texto: atribuir"]
  nac866925{"Loop: para cada linha de TableExcelExport"}
  n97fb33a8{"Se: rowFilaProcessamento = ⋯"}
  n08c85177{"Loop: para cada linha de TableAuxiliarFilaProcessamento"}
  nd7505c56{"Se: rowTableAuxiliarFilaProcessamento = ⋯"}
  n7e4a79eb[["CommonTask/Database/AtualizaRegistroProcessamentoAtividade_…"]]
  n21b5058c["Finalizando Fila Processamento"]
  n2b762f18[["CommonTask/Database/ExecutaProcedureGenerica"]]
  nc316a5e5(["sair do loop"])
  nef78bb1e(["fim do passo"])
  n7e4a79eb --> n21b5058c
  n21b5058c --> n2b762f18
  n2b762f18 --> nc316a5e5
  nd7505c56 -->|sim| n7e4a79eb
  n08c85177 -->|iteração| nd7505c56
  nd7505c56 -.->|próxima| n08c85177
  n97fb33a8 -->|sim| n08c85177
  nac866925 -->|iteração| n97fb33a8
  n08c85177 -.->|próxima| nac866925
  n97fb33a8 -.->|próxima| nac866925
  n11329eb9 --> nac866925
  nce42b9a8 -->|iteração| n11329eb9
  nac866925 -.->|próxima| nce42b9a8
  na1e7d966 --> nce42b9a8
  nce42b9a8 -->|fim| nef78bb1e
  classDef acoes stroke:#4c6ef5,stroke-width:1px
  class n11329eb9,n21b5058c acoes
  classDef biblioteca stroke:#1098ad,stroke-width:2px
  class n2b762f18,n7e4a79eb biblioteca
  classDef controle stroke:#b26a00,stroke-width:2px
  class n08c85177,n97fb33a8,nac866925,nc316a5e5,nce42b9a8,nd7505c56 controle
```

---

← [Obter Dados Exportados Python Para Atualizar Fila Processamento](03-obter-dados-exportados-python-para-atualizar.md)
