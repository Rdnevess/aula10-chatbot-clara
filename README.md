# CLARA: chatbot multiagente com n8n (Aula 10)

Laboratório da Aula 10 de *IA Generativa e Agentes Autônomos* (Tópicos Especiais em Programação, Bacharelado em Sistemas de Informação, UNEMAT Sinop), feito a partir da apostila *ChatBot multiagente com n8n*, do Prof. Benevid Felix da Silva.

A CLARA é a assistente virtual de um Núcleo de Convênios hipotético. Uma agente orquestradora entende o pedido e o repassa a três sub-agentes:

| Sub-agente | Responde por | Usa |
| --- | --- | --- |
| INFO | endereço, horário, contato e serviços do Núcleo | dados fixos no prompt |
| CONVENIOS | partes, objeto, valor e data de um convênio | base vetorial (RAG) com os PDFs dos convênios |
| ATENDIMENTO | pedido de atendimento humano | Data table `chamados`, que devolve um protocolo |

Os modelos de linguagem rodam no Groq: `openai/gpt-oss-120b` na CLARA e `openai/gpt-oss-20b` nos sub-agentes. Os embeddings saem do Ollama local (`nomic-embed-text`).

## Entrega

| Item da apostila ("O que entregar") | Onde está |
| --- | --- |
| Workflows exportados | [`workflows/ingestao-convenios.json`](workflows/ingestao-convenios.json) e [`workflows/clara-multiagente.json`](workflows/clara-multiagente.json) |
| Tabela de testes | [`testes.md`](testes.md): os 8 cenários da seção 6.2, com a resposta e o sub-agente acionado em cada um |
| Link do Git | este repositório |

**Resultado dos testes:** os 8 cenários passaram (10 de 10 mensagens), sem ajuste de prompt. Os dados brutos, com o ID de cada execução, estão em [`testes/resultados.json`](testes/resultados.json).

## Os dois workflows

**Aula 10 - Ingestão dos convênios** (seção 4)
- Fluxo: formulário em `/form/base-convenios` → um item por PDF → extração do texto → trechos de 1000 caracteres (sobreposição de 150) com os metadados `arquivo` e `convenio` → embeddings → base vetorial em memória `convenios`.
- Resultado com os três PDFs de `convenios/`: *3 arquivo(s) indexado(s) em 3 trecho(s).*

**Aula 10 - CLARA multiagente** (seção 5)
- Gatilho de chat → CLARA (com memória de 10 mensagens) → sub-agentes como ferramentas, com no máximo 4 iterações cada.
- Os prompts de sistema, copiados literalmente da apostila, estão em [`prompts/`](prompts/).

## Pré-requisitos (seção 1 da apostila)

- n8n da Aula 09 em execução (`http://localhost:5678`). Aqui foi a versão 2.42.5, em Docker.
- Ollama com o modelo de embeddings: `ollama pull nomic-embed-text`.
- Chave da API do Groq.

## Importar os workflows pela interface

1. No n8n, crie as credenciais `Groq` (Groq API) e `Ollama`, com Base URL `http://host.docker.internal:11434` (n8n em Docker) ou `http://127.0.0.1:11434` (n8n pelo npm).
2. Crie a Data table `chamados` com as colunas de texto `protocolo`, `nome`, `email`, `descricao` e `registrado_em`.
3. Importe os dois arquivos de `workflows/` (*Import from File*). Os JSON apontam para credenciais e para uma tabela de outra instalação: selecione de novo as credenciais nos nós de modelo e de embeddings, e a tabela no nó *Registrar chamado*.
4. Publique a ingestão e envie os PDFs de `convenios/` em `http://localhost:5678/form/base-convenios`. Depois converse com a CLARA pelo *Open chat* do editor.

## Reproduzir pelos scripts

Os scripts em `scripts/` usam só a biblioteca padrão do Python 3 e falam com a API pública do n8n. Antes de rodar, crie na raiz um arquivo `.env` (ignorado pelo git) com as chaves:

```
N8N_API_KEY=...   # n8n: Settings › n8n API
GROQ_API_KEY=...
```

Depois, rode a partir da raiz do repositório:

```bash
python -m scripts.configurar_n8n               # credenciais Groq e Ollama e Data table chamados
python -m scripts.implantar ingestao           # cria e publica o workflow de ingestão
python -m scripts.ingerir                      # envia os PDFs ao formulário e confere a execução
python -m scripts.implantar clara --chat-publico   # publica a CLARA com o chat aberto para os testes
python -m scripts.cenarios                     # roda os cenários da seção 6.2 → testes/resultados.json
python -m scripts.gerar_testes_md              # gera testes.md
python -m scripts.exportar                     # desliga o chat público, exporta workflows/ e gera entrega-aula10.zip
python -m unittest discover -s tests -t . -v   # testes unitários dos scripts
```

O chat público fica disponível só durante os testes. O n8n escuta apenas em `127.0.0.1`, e os workflows exportados saem com a opção desligada.

**Atenção:** o `gerar_testes_md` reescreve o `testes.md` inteiro, inclusive a seção "Observações da revisão", que foi escrita à mão.

## Observações

- **A base vetorial e a memória das conversas ficam na memória do n8n.** Depois de reiniciar o n8n, rode a ingestão de novo antes de usar o chatbot (Quadro 5).
- **Dados fictícios:** os convênios e os dados de teste (nome e e-mail do cenário 7) são fictícios. A cada mensagem, os trechos recuperados e a conversa vão para o Groq, por isso a base só deve receber documentos fictícios ou públicos (seção 8).

## Estrutura

```
convenios/      PDFs fictícios dos convênios (material da disciplina)
prompts/        prompts de sistema da CLARA e dos sub-agentes
scripts/        construção, implantação, ingestão, testes e exportação dos workflows
tests/          testes unitários (unittest)
testes/         resultados brutos dos cenários
workflows/      workflows exportados (entrega)
testes.md       tabela de testes (entrega)
LEIA-ME.md      descrição dos insumos, vinda do material da disciplina
```

## Créditos

A apostila e os convênios de exemplo são do Prof. Benevid Felix da Silva (UNEMAT), sob licença CC BY-SA 4.0.
