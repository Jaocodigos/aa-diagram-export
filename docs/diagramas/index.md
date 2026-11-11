# Diagramas dos bots

2 bot(s) no export.

Outros 8 bot(s) casam com os padrões de biblioteca (`CommonTask/**`): aparecem mencionados nos fluxos de quem os chama, com os parâmetros na tabela de Chamadas de cada página, mas não têm diagrama próprio.

## Grafo de chamadas

```mermaid
flowchart LR
  n0429a380["P001-ExtraiFaturas"]
  n564aef6b["P001_RevisaFilaProcessamento"]
  n0429a380 --> n564aef6b
```

## Inventário

| Bot | Ações | Chama | Diagrama |
|---|---|---|---|
| `Processos/Sustentabilidade/P001-Ecobot/P001-ExtraiFaturas` | 34 | 9 | [abrir](P001-ExtraiFaturas/README.md) |
| `Processos/Sustentabilidade/P001-Ecobot/Tarefas/P001_RevisaFilaProcessamento` | 5 | 3 | [abrir](P001_RevisaFilaProcessamento/README.md) |

## Pendências

- 2 arquivo(s) do export ignorado(s) por não serem bots.
