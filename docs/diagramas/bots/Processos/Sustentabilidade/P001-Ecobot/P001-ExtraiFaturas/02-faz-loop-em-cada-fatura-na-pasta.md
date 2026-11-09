# Faz loop em cada fatura na pasta

Passo de [P001-ExtraiFaturas](../P001-ExtraiFaturas.md).

```mermaid
flowchart TD
  n444fa39d(["Faz loop em cada fatura na pasta"])
  n3bde74c9{"Loop: para cada arquivo de ReturnPadhy"}
  subgraph n42fc8bfb["Validacao Nome Arquivo"]
  n73a70c08["Texto: limpar espaços"]
  n68c06ace{"Se: NomeArquivo contém ⋯"}
  n573761a7["Texto: atribuir"]
  ndd106be1{"Senão se: NomeArquivo contém ⋯ ou NomeArquivo contém ⋯"}
  nf999bcbb["Texto: atribuir"]
  end
  subgraph na8598d30["Validacao MesAno"]
  n002aebad["Texto: substituir"]
  end
  subgraph n093ac98f["Insere Item Fila de Processamento"]
  n23398e74["Insere fila por cada conta que deve ser lida (arquivos de b…"]
  nb9f82b68[["CommonTask/Database/InserirItemFilaProcessamento"]]
  n8f9c2126[["CommonTask/Database/ObterRegistroFilaDeProcessamento"]]
  end
  subgraph n0faaa1d6["Cria Atividade"]
  n3531aa6a{"Loop: para cada linha de ReturnFilaProcessamento"}
  nb9916ddf["Texto: atribuir"]
  nea5b2c61{"Se: ListIdFilaProcessamento"}
  n7be02ab2(["próxima iteração"])
  nb3d198a8{"Se: IdFilaProcessamento ≠ ⋯"}
  n5431338f["Como ativiade sera fechada fora do loop depois de rodar o s…"]
  n6c2cc169[["CommonTask/Log/GravarLogBanco"]]
  subgraph ndce81c3b["Abre atividade"]
  na8151f40[["CommonTask/Database/CriaRegistroProcessamentoAtividade"]]
  ncf7287b0["Tabela: gravar célula, Tabela: gravar célula, Número: incre…"]
  end
  nb9328446(["sair do loop"])
  end
  n4fbe64b4(["fim do passo"])
  n68c06ace -->|sim| n573761a7
  n68c06ace -->|não| ndd106be1
  ndd106be1 -->|sim| nf999bcbb
  n73a70c08 --> n68c06ace
  n573761a7 --> n002aebad
  nf999bcbb --> n002aebad
  ndd106be1 -->|não| n002aebad
  n23398e74 --> nb9f82b68
  nb9f82b68 --> n8f9c2126
  n002aebad --> n23398e74
  nea5b2c61 -->|sim| n7be02ab2
  nb9916ddf --> nea5b2c61
  n5431338f --> n6c2cc169
  na8151f40 --> ncf7287b0
  n6c2cc169 --> na8151f40
  ncf7287b0 --> nb9328446
  nb3d198a8 -->|sim| n5431338f
  nea5b2c61 -->|não| nb3d198a8
  n3531aa6a -->|iteração| nb9916ddf
  nb3d198a8 -.->|próxima| n3531aa6a
  n8f9c2126 --> n3531aa6a
  n3bde74c9 -->|iteração| n73a70c08
  n3531aa6a -.->|próxima| n3bde74c9
  n444fa39d --> n3bde74c9
  n3bde74c9 -->|fim| n4fbe64b4
  classDef acoes stroke:#4c6ef5,stroke-width:1px
  class n002aebad,n23398e74,n5431338f,n573761a7,n73a70c08,nb9916ddf,ncf7287b0,nf999bcbb acoes
  classDef biblioteca stroke:#1098ad,stroke-width:2px
  class n6c2cc169,n8f9c2126,na8151f40,nb9f82b68 biblioteca
  classDef controle stroke:#b26a00,stroke-width:2px
  class n3531aa6a,n3bde74c9,n68c06ace,n7be02ab2,nb3d198a8,nb9328446,ndd106be1,nea5b2c61 controle
```

---

← [Obter Dados Exportados Python Para Inserir na Fila Processamento](01-obter-dados-exportados-python-para-inserir-na.md) · [Obter Dados Exportados Python Para Atualizar Fila Processamento](03-obter-dados-exportados-python-para-atualizar.md) →
