"""Workflow "Aula 10 - Ingestão dos convênios" (apostila, seção 4)."""
from scripts.wf_util import cred_ollama, ligar, no

NOME = "Aula 10 - Ingestão dos convênios"
WEBHOOK_FORM = "3c1f6a52-8d0e-4b4f-9a6e-1a0c10000001"
WEBHOOK_FIM = "3c1f6a52-8d0e-4b4f-9a6e-1a0c10000002"

CODIGO_UM_ITEM = """// O formulário entrega todos os PDFs num único item (Documentos_0, Documentos_1, ...).
// Aqui cada arquivo vira um item, com o binário em "data" e o nome do arquivo no JSON.
const saida = [];
for (const item of $input.all()) {
  for (const chave of Object.keys(item.binary ?? {})) {
    const arquivo = item.binary[chave];
    saida.push({ json: { arquivo: arquivo.fileName }, binary: { data: arquivo } });
  }
}
return saida;
"""

META_CONVENIO = r"={{ $json.text.match(/N[º°o]\s*(\d+\/\d{4})/)?.[1] ?? '' }}"


def construir(ids):
    nos = [
        no("Enviar convênios", "n8n-nodes-base.formTrigger", 2.5, (0, 0), {
            "formTitle": "Base de convênios",
            "formDescription": "Envie os PDFs dos convênios. O envio substitui a base anterior.",
            "formFields": {"values": [{
                "fieldLabel": "Documentos",
                "fieldName": "documentos",
                "fieldType": "file",
                "multipleFiles": True,
                "acceptFileTypes": ".pdf",
                "requiredField": True,
            }]},
            "options": {"path": "base-convenios"},
        }, webhook_id=WEBHOOK_FORM),
        no("Um item por arquivo", "n8n-nodes-base.code", 2, (220, 0), {"jsCode": CODIGO_UM_ITEM}),
        no("Extrair texto", "n8n-nodes-base.extractFromFile", 1.1, (440, 0), {"operation": "pdf", "options": {}}),
        no("Inserir na base", "@n8n/n8n-nodes-langchain.vectorStoreInMemory", 1.3, (680, 0), {
            "mode": "insert",
            "memoryKey": {"__rl": True, "mode": "id", "value": "convenios"},
            "embeddingBatchSize": 50,
            "clearStore": True,
        }),
        no("Base atualizada", "n8n-nodes-base.form", 2.5, (1040, 0), {
            "operation": "completion",
            "completionTitle": "Base atualizada",
            "completionMessage": "={{ $('Um item por arquivo').all().length }} arquivo(s) indexado(s) em "
                                 "{{ $input.all().length }} trecho(s).",
            "options": {},
        }, webhook_id=WEBHOOK_FIM),
        no("Embeddings", "@n8n/n8n-nodes-langchain.embeddingsOllama", 1, (580, 220),
           {"model": "nomic-embed-text:latest"}, credenciais=cred_ollama(ids)),
        no("Carregar documento", "@n8n/n8n-nodes-langchain.documentDefaultDataLoader", 1.1, (800, 220), {
            "dataType": "json",
            "jsonMode": "expressionData",
            "jsonData": "={{ $json.text }}",
            "textSplittingMode": "custom",
            "options": {"metadata": {"metadataValues": [
                {"name": "arquivo", "value": "={{ $('Um item por arquivo').item.json.arquivo }}"},
                {"name": "convenio", "value": META_CONVENIO},
            ]}},
        }),
        no("Dividir em trechos", "@n8n/n8n-nodes-langchain.textSplitterRecursiveCharacterTextSplitter", 1,
           (880, 420), {"chunkSize": 1000, "chunkOverlap": 150, "options": {}}),
    ]
    conexoes = {}
    ligar(conexoes, "Enviar convênios", "Um item por arquivo")
    ligar(conexoes, "Um item por arquivo", "Extrair texto")
    ligar(conexoes, "Extrair texto", "Inserir na base")
    ligar(conexoes, "Inserir na base", "Base atualizada")
    ligar(conexoes, "Embeddings", "Inserir na base", "ai_embedding")
    ligar(conexoes, "Carregar documento", "Inserir na base", "ai_document")
    ligar(conexoes, "Dividir em trechos", "Carregar documento", "ai_textSplitter")
    return {"name": NOME, "nodes": nos, "connections": conexoes, "settings": {"executionOrder": "v1"}}
