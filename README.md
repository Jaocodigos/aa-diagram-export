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
- `[geral] orcamento_de_nos` — quantos nós cabem num diagrama antes de ele ser
  quebrado em seções.
- `[geral] bibliotecas` — os bots utilitários, compartilhados entre processos.

## Bibliotecas

Bot que casa com um padrão de `[geral] bibliotecas` é tratado como utilitário:
aparece **mencionado** no fluxo de quem o chama, mas não ganha diagrama
próprio, nem entra no grafo de chamadas ou no inventário. Os parâmetros dele
continuam registrados na tabela de **Chamadas** de cada chamador.

Num export real, oito de dez bots eram utilitários de `CommonTask`. Sem isso,
o índice e os diagramas dos processos ficavam dominados por infraestrutura.

O padrão fica no `dicionario.toml` e não no código porque cada repositório tem
a sua convenção de pastas — `CommonTask` aqui pode ser `Shared` noutro.

## Dois limites que valem conhecer

**Arestas.** O Mermaid recusa diagrama com mais de 500 arestas e o GitHub usa
essa configuração padrão, que não dá para elevar de dentro do arquivo. Quando
um bot passa disso, o gerador refaz com um nível a menos de expansão até
caber, e escreve na página que reduziu.

**Legibilidade.** Esse é um limite bem mais baixo, e não tem nada a ver com o
Mermaid: o navegador encolhe o desenho para caber na largura da página, então
diagrama grande não vira diagrama grande, vira diagrama ilegível. Passando do
`orcamento_de_nos`, os `Step` maiores saem do desenho principal e viram seções
da mesma página, com um atalho em Markdown logo abaixo do panorama.

Os nós de seção também trazem um `click` do Mermaid, mas ele é só bônus para
quem abrir fora do GitHub: o `securityLevel` padrão é `strict`, que desliga o
clique e, como o `maxEdges`, não pode ser mudado de dentro do diagrama. A
navegação confiável são os links Markdown.

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
