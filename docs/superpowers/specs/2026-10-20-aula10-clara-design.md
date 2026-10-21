# Aula 10 — CLARA multiagente no n8n: design

Data: 2026-10-20
Referência: apostila *IA Generativa e Agentes Autônomos, v. 10 — ChatBot multiagente com n8n*
(`Aula-10-ChatBot-Multiagente-n8n.pdf`, não versionado). Seções citadas como "§".

## Objetivo

Executar o laboratório da Aula 10 de ponta a ponta nesta pasta: ambiente (§1), workflow de
ingestão (§4), workflow da CLARA (§5), testes por cenário (§6) e entrega (Laboratório e entrega).
A apostila é a fonte de verdade para nomes de nós, parâmetros e prompts; este documento registra
apenas o que ela deixa em aberto e os desvios necessários para automatizar o trabalho.

## Ambiente

| Item | Estado / decisão |
| --- | --- |
| n8n | 2.42.5 em Docker (`n8nio/n8n`), porta `127.0.0.1:5678`, iniciado a partir de `aula09` |
| Ollama | Instalado via `winget install Ollama.Ollama`; modelo `nomic-embed-text` (`ollama pull`) |
| Segredos | `.env` na raiz (ignorado pelo git) com `N8N_API_KEY` e `GROQ_API_KEY`; lidos por script, nunca impressos |
| Projeto | Esta pasta (`Aula10-chatbot`) é o repositório da §1.1 |

Estrutura do repositório:

```
.gitignore  .gitattributes  .env (não versionado)  LEIA-ME.md
convenios/convenio_0{1,2,3}.pdf
workflows/ingestao-convenios.json  workflows/clara-multiagente.json
testes.md
docs/superpowers/specs/  docs/superpowers/plans/
```

O `.gitignore` do material recebe também o PDF da apostila e o `aula10-chatbot.zip`.
O `.gitattributes` marca `*.pdf` e `*.zip` como binários (o git local usa `core.autocrlf=true`).

## Configuração no n8n (via API pública, `X-N8N-API-KEY`)

| Recurso | Configuração |
| --- | --- |
| Credencial `Groq` | tipo Groq API, chave de `GROQ_API_KEY` |
| Credencial `Ollama` | tipo Ollama, Base URL `http://host.docker.internal:11434` (n8n em Docker, §1.5) |
| Data table `chamados` | colunas texto `protocolo`, `nome`, `email`, `descricao`, `registrado_em` (§1.6) |

Se a API pública da 2.42.5 não expuser Data tables, a tabela é criada pelo usuário na interface
(aba Data tables), e o restante segue automatizado.

## Workflow 1 — `Aula 10 - Ingestão dos convênios` (§4)

Fluxo principal, com os nomes exatos: **Enviar convênios** (Form Trigger, path `base-convenios`,
campo File `documentos`, múltiplos, `.pdf`, obrigatório) → **Um item por arquivo** (Code, script
da §4.2) → **Extrair texto** (Extract From PDF, campo `data`) → **Inserir na base** (Simple Vector
Store, Insert, Memory Key `convenios`, Batch Size 50, Clear Store ligado) → **Base atualizada**
(Form Ending, mensagem da §4.6).

Sub-nós do Inserir na base: **Embeddings** (Embeddings Ollama, `nomic-embed-text:latest`),
**Carregar documento** (Default Data Loader, JSON, Load Specific Data `{{ $json.text }}`,
Text Splitting Custom, metadados `arquivo` e `convenio` da §4.5) e **Dividir em trechos**
(Recursive Character Text Splitter, 1000 / 150).

Verificação: publicar e enviar os três PDFs por POST multipart a
`http://localhost:5678/form/base-convenios`; a página de conclusão deve conter
`3 arquivo(s) indexado(s) em 3 trecho(s).`

## Workflow 2 — `Aula 10 - CLARA multiagente` (§5)

- **Mensagem recebida** (Chat Trigger) → **CLARA** (AI Agent, System Message = prompt da §5.2, literal).
- Sub-nós da CLARA: **Modelo da CLARA** (Groq, `openai/gpt-oss-120b`, temperatura 0.2) e
  **Memória** (Simple Memory, janela 10).
- Ferramentas da CLARA, três AI Agent Tool com Prompt (User Message) via `$fromAI`, Max Iterations 4,
  Description e System Message literais da apostila, todos ligados a um único
  **Modelo dos sub-agentes** (Groq, `openai/gpt-oss-20b`, temperatura 0.2):
  - **Sub-agente INFO** (§5.3): sem ferramenta.
  - **Sub-agente CONVENIOS** (§5.4): ferramenta **Base de convenios** (Simple Vector Store,
    Retrieve as Tool, Memory Key `convenios`, Limit 4, Include Metadata ligado) com sub-nó
    **Embeddings** (Ollama, mesmo modelo da ingestão).
  - **Sub-agente ATENDIMENTO** (§5.5): ferramenta **Registrar chamado** (Data table, Insert row
    em `chamados`, mapeamento manual: `protocolo` e `registrado_em` por expressão do n8n;
    `nome`, `email`, `descricao` por `$fromAI`).
- Nomes de nó sem acento, para que as ferramentas se chamem `Sub-agente_INFO`,
  `Sub-agente_CONVENIOS`, `Sub-agente_ATENDIMENTO`, `Base_de_convenios`, `Registrar_chamado` (§3.2).

Tipos de nó e `typeVersion` são os da 2.42.5. Os workflows são criados pela API e validados por
execução; divergência de parâmetros é resolvida comparando com um nó equivalente criado no editor
(Playwright).

### Desvio da apostila: chat público durante os testes

O teste da §6 usa o *Open chat* do editor, inacessível pela API. Durante os testes, o Chat Trigger
fica com **Make Chat Publicly Available** ligado e o workflow publicado; as mensagens vão por POST a
`/webhook/<webhookId>/chat` com `{"action":"sendMessage","sessionId":...,"chatInput":...}`.
O n8n escuta só em `127.0.0.1`, então o endpoint não fica exposto na rede. **A opção é desligada
antes da exportação**, e o JSON entregue corresponde ao da apostila.

## Testes (§6)

- Os oito cenários da §6.2, cada um com `sessionId` próprio; 3, 4 e 5 compartilham a sessão.
  O cenário 7 usa dados fictícios ("Carlos Mendes, carlos.mendes@exemplo.example").
- Intervalo de ~20 s entre mensagens (limite de 8000 tokens/min do Groq, §3.4); em 429,
  aguardar 60 s e reenviar.
- Pré-condição: a ingestão rodou depois do último reinício do n8n (base em memória, §2.5).
- Para cada mensagem, o caminho é lido em `GET /api/v1/executions/{id}?includeData=true`
  (nós executados em `runData`), equivalente ao painel Logs. No cenário 7, confirmar a nova linha
  em `chamados`.
- O cenário passa quando a resposta tem o conteúdo esperado **e** o caminho esperado.

`testes.md` contém a tabela do passo 3:

| # | Mensagem(ns) | Resposta obtida | Sub-agente (registro) | Esperado | OK? |

### Ajustes (passo 4)

Cenário que falhar não é corrigido automaticamente. O usuário recebe o sintoma, o trecho do
registro e a alteração de prompt proposta; com aprovação, o prompt é alterado, o cenário é
repetido, e `testes.md` ganha uma segunda tabela: cenário, instrução anterior, instrução nova,
resultado do novo teste.

## Entrega

1. Desligar o chat público; exportar os dois workflows pela API para
   `workflows/ingestao-convenios.json` e `workflows/clara-multiagente.json`, normalizados para o
   formato do *Export JSON* da interface (`name`, `nodes`, `connections`, `settings`, `pinData`,
   `meta`), sem campos internos da API. Credenciais aparecem só como referência (`id`, `name`).
2. Commits: um ao fim de cada workflow e um com `testes.md`.
3. Gerar o `.zip` de entrega com `workflows/` e `testes.md`.
4. Fica com o usuário: `git push` para o GitHub e o link do Git (o conector GitHub não está
   disponível nesta sessão).

## Fora do escopo

Variante com Google Drive (§7, opcional), troca da base vetorial por PGVector/Qdrant,
modelo de linguagem local.
