# aa-diagram-export

Gera documentação em Markdown, com diagramas Mermaid, a partir de um export de
bots do Automation Anywhere A360.

A ideia é a documentação dos bots viver no git: texto, diffável, renderizando
direto no GitHub sem ferramenta externa.

O desenho completo está em [`docs/spec.md`](docs/spec.md).

## Estado atual

O pipeline é `loader → parser → resolver → render`. Hoje:

| Módulo | Estado |
|---|---|
| `model.py`, `render.py`, `resolver.py`, `config.py`, `paths.py`, `loader.py`, `__main__.py` | prontos e testados |
| `parser.py` — JSON do A360 → modelo | **falta**, à espera de um export real |

O parser é o único módulo que depende do formato do arquivo exportado, e esse
formato ainda não foi validado contra um export de verdade (§11 da spec). Até
lá, rodar a CLI termina com uma mensagem dizendo exatamente isso.

Para destravar: um `.zip` do Control Room com pelo menos um bot usando `If`,
`Loop`, `Try/Catch` e um `Run Task` chamando outro bot do mesmo export. Pode
ser anonimizado.

## Como rodar

```
python -m aa_diagram_export --input <zip ou pasta> --out docs/diagramas
```

Opções:

| Flag | O que faz |
|---|---|
| `--max-depth N` | até quantos níveis de subtarefa expandir (padrão: o do dicionário) |
| `--dicionario <arquivo>` | usar outro dicionário que não o do diretório atual |
| `--no-call-graph` | não desenhar o grafo de chamadas no `index.md` |
| `--fail-on-missing` | terminar com erro se algum bot chamado não estiver no export |
| `--quiet` | não escrever no console |

## Como ajustar os diagramas

Tudo que o time normalmente quer mudar está no **`dicionario.toml`**, na raiz.
Não é preciso abrir nenhum `.py`:

- `[comandos_amigaveis]` — o rótulo que cada comando do A360 recebe no
  diagrama. Comando que não estiver aqui aparece com o nome cru e é listado na
  seção de pendências do `index.md`, para o time ir preenchendo.
- `[estilo]` — as cores de cada tipo de nó.
- `[geral] profundidade_maxima` — quantos níveis de subtarefa expandir.
- `[estruturas_de_controle] pacotes` — quais comandos contam como estrutura e
  não são colapsados no bloco de ações.

## Desenvolvimento

Quem só gera diagramas não instala nada: o script roda com a biblioteca padrão
do Python 3.14. As dependências abaixo são só para desenvolver.

```
pip install -r requirements-dev.txt
pytest
```

Os testes comparam o resultado com os arquivos de `tests/fixtures/esperado/`,
byte a byte. Quando a mudança no diagrama for intencional:

```
pytest --regenerar
```

Isso reescreve os esperados; o diff do git mostra exatamente o que mudou no
desenho antes de você commitar.
