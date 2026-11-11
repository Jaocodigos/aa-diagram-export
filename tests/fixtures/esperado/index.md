# Diagramas dos bots

2 bot(s) no export.

## Grafo de chamadas

```mermaid
flowchart LR
  nfedca597["Enviar Relatório"]
  n4756c22e["Conciliação Diária"]
  n387c2bd9[/"Bots/Comum/$sBotDinamico$ — não encontrado"/]
  n13af1ced[/"Bots/Comum/Auditoria — não encontrado"/]
  nfedca597 --> n4756c22e
  n4756c22e --> nfedca597
  n4756c22e --> n13af1ced
  n4756c22e --> n387c2bd9
  classDef nao_resolvido stroke:#e03131,stroke-width:2px,stroke-dasharray:4 3
  class n387c2bd9,n13af1ced nao_resolvido
```

## Inventário

| Bot | Ações | Chama | Diagrama |
|---|---|---|---|
| `Bots/Comum/EnviarRelatorio` | 1 | 1 | [abrir](EnviarRelatorio/README.md) |
| `Bots/Financeiro/ConciliacaoDiaria` | 13 | 3 | [abrir](ConciliacaoDiaria/README.md) |

## Pendências

### Bots referenciados e não encontrados no export

- `Comum/Auditoria` — chamado por `Bots/Financeiro/ConciliacaoDiaria`

### Comandos sem rótulo no dicionario.toml

Aparecem no diagrama com o nome cru do A360. Cadastrar em `[comandos_amigaveis]`:

- `"Browser:Download"`
- `"Excel advanced:SetCell"`

- 2 arquivo(s) do export ignorado(s) por não serem bots.
