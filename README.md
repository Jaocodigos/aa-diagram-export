# aa-diagram-export

Gera documentação em Markdown, com diagramas Mermaid, a partir de um export de
bots do Automation Anywhere A360.

A ideia é a documentação dos bots viver no git: texto, diffável, renderizando
direto no GitHub sem ferramenta externa.

O desenho completo está em [`docs/spec.md`](docs/spec.md).

## Estado atual

O pipeline `loader → parser → resolver → render` está completo e validado
contra um export real do Control Room. O formato do arquivo exportado está
documentado na §11 da spec.

## Como rodar

O pacote está em `src/`, então precisa ser instalado uma vez:

```
pip install -e .
```

Depois, de qualquer lugar:

```
python -m aa_diagram_export --input <zip ou pasta> --out docs/diagramas
```

Sem instalar, dá para rodar da raiz do repositório apontando o `PYTHONPATH`:

```
# Windows (PowerShell)
$env:PYTHONPATH="src"; python -m aa_diagram_export --input .\bot.zip --out .\docs\diagramas
```

Atenção: `python -m` recebe **nome de módulo**, não caminho de pasta.
`python -m .\src\aa_diagram_export\` falha com "Relative module names not
supported".

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

## Um limite que vale conhecer

O Mermaid recusa diagrama com mais de 500 arestas, e o GitHub usa essa
configuração padrão — não dá para elevar o limite de dentro do arquivo. Um bot
orquestrador com várias subtarefas expandidas passa disso com facilidade.

Quando isso acontece, o gerador refaz o diagrama com um nível a menos de
expansão, até caber, e escreve na página do bot que reduziu. Cada bot chamado
continua tendo o diagrama próprio, então nada se perde — só deixa de estar
tudo no mesmo desenho.

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
