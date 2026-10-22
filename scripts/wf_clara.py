"""Workflow "Aula 10 - CLARA multiagente" (apostila, seção 5)."""
from scripts.n8n_api import RAIZ
from scripts.wf_util import cred_groq, cred_ollama, ligar, no

NOME = "Aula 10 - CLARA multiagente"
WEBHOOK_CHAT = "5d2e7b63-9e1f-4c50-8b7f-2b0d20000001"
SUB_AGENTES = ("Sub-agente INFO", "Sub-agente CONVENIOS", "Sub-agente ATENDIMENTO")

PEDIDO = ("={{ $fromAI('Prompt__User_Message_', `Pedido em linguagem natural, com os dados que o "
          "sub-agente precisa`, 'string') }}")

DESCRICOES = {
    "Sub-agente INFO": "Responde sobre endereço, horário, telefone, e-mail e serviços do Núcleo de Convênios.",
    "Sub-agente CONVENIOS": ("Consulta os documentos dos convênios: partes, representantes, objeto, valor e data. "
                             "Envie a pergunta completa, com o número do convênio e o dado pedido."),
    "Sub-agente ATENDIMENTO": ("Registra um chamado para a equipe humana. Envie na mensagem o nome completo, "
                               "o e-mail e a descrição do problema."),
}
PROMPTS = {"Sub-agente INFO": "info", "Sub-agente CONVENIOS": "convenios", "Sub-agente ATENDIMENTO": "atendimento"}
COLUNAS = ("protocolo", "nome", "email", "descricao", "registrado_em")


def prompt(nome):
    return (RAIZ / "prompts" / f"{nome}.txt").read_text(encoding="utf-8").strip()


def _modelo(nome, modelo, posicao, ids):
    return no(nome, "@n8n/n8n-nodes-langchain.lmChatGroq", 1, posicao,
              {"model": modelo, "options": {"temperature": 0.2}}, credenciais=cred_groq(ids))


def _sub_agente(nome, posicao):
    return no(nome, "@n8n/n8n-nodes-langchain.agentTool", 3, posicao, {
        "toolDescription": DESCRICOES[nome],
        "text": PEDIDO,
        "options": {"systemMessage": prompt(PROMPTS[nome]), "maxIterations": 4},
    })


def _registrar_chamado(ids):
    valores = {
        "protocolo": "={{ 'CH-' + $now.toFormat('yyyyMMdd-HHmmss') }}",
        "nome": "={{ $fromAI('nome', `Nome completo da pessoa`, 'string') }}",
        "email": "={{ $fromAI('email', `E-mail da pessoa`, 'string') }}",
        "descricao": "={{ $fromAI('descricao', `Descrição do problema`, 'string') }}",
        "registrado_em": "={{ $now.toISO() }}",
    }
    esquema = [{"id": c, "displayName": c, "required": False, "defaultMatch": False, "display": True,
                "type": "string", "readOnly": False, "removed": False} for c in COLUNAS]
    return no("Registrar chamado", "n8n-nodes-base.dataTableTool", 1.1, (1000, 440), {
        "descriptionType": "manual",
        "toolDescription": "Grava um chamado na tabela chamados e devolve o protocolo.",
        "resource": "row",
        "operation": "insert",
        "dataTableId": {"__rl": True, "mode": "list", "value": ids["chamados"], "cachedResultName": "chamados"},
        "columns": {"mappingMode": "defineBelow", "value": valores, "matchingColumns": [], "schema": esquema,
                    "attemptToConvertTypes": False, "convertFieldsToString": False},
        "options": {},
    })


def construir(ids, chat_publico=False):
    gatilho = {"public": True, "mode": "hostedChat", "options": {"responseMode": "lastNode"}} if chat_publico \
        else {"options": {}}
    nos = [
        no("Mensagem recebida", "@n8n/n8n-nodes-langchain.chatTrigger", 1.4, (0, 0), gatilho,
           webhook_id=WEBHOOK_CHAT),
        no("CLARA", "@n8n/n8n-nodes-langchain.agent", 3.1, (260, 0), {"options": {"systemMessage": prompt("clara")}}),
        _modelo("Modelo da CLARA", "openai/gpt-oss-120b", (120, 220), ids),
        no("Memória", "@n8n/n8n-nodes-langchain.memoryBufferWindow", 1.3, (280, 220), {"contextWindowLength": 10}),
        _sub_agente("Sub-agente INFO", (440, 220)),
        _sub_agente("Sub-agente CONVENIOS", (640, 220)),
        _sub_agente("Sub-agente ATENDIMENTO", (840, 220)),
        _modelo("Modelo dos sub-agentes", "openai/gpt-oss-20b", (440, 440), ids),
        no("Base de convenios", "@n8n/n8n-nodes-langchain.vectorStoreInMemory", 1.3, (660, 440), {
            "mode": "retrieve-as-tool",
            "toolDescription": ("Busca por semelhança nos trechos dos convênios. Devolve os trechos mais "
                                "próximos da consulta, com o arquivo de origem."),
            "memoryKey": {"__rl": True, "mode": "id", "value": "convenios"},
            "topK": 4,
            "includeDocumentMetadata": True,
        }),
        no("Embeddings", "@n8n/n8n-nodes-langchain.embeddingsOllama", 1, (660, 640),
           {"model": "nomic-embed-text:latest"}, credenciais=cred_ollama(ids)),
        _registrar_chamado(ids),
    ]
    conexoes = {}
    ligar(conexoes, "Mensagem recebida", "CLARA")
    ligar(conexoes, "Modelo da CLARA", "CLARA", "ai_languageModel")
    ligar(conexoes, "Memória", "CLARA", "ai_memory")
    for sub in SUB_AGENTES:
        ligar(conexoes, sub, "CLARA", "ai_tool")
        ligar(conexoes, "Modelo dos sub-agentes", sub, "ai_languageModel")
    ligar(conexoes, "Base de convenios", "Sub-agente CONVENIOS", "ai_tool")
    ligar(conexoes, "Embeddings", "Base de convenios", "ai_embedding")
    ligar(conexoes, "Registrar chamado", "Sub-agente ATENDIMENTO", "ai_tool")
    return {"name": NOME, "nodes": nos, "connections": conexoes, "settings": {"executionOrder": "v1"}}
