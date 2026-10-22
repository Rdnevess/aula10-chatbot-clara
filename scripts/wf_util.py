"""Peças comuns para descrever workflows do n8n como dicionários."""
import re
import uuid


def no(nome, tipo, versao, posicao, parametros, credenciais=None, webhook_id=None):
    definicao = {
        "parameters": parametros,
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"aula10/{tipo}/{nome}")),
        "name": nome,
        "type": tipo,
        "typeVersion": versao,
        "position": list(posicao),
    }
    if credenciais:
        definicao["credentials"] = credenciais
    if webhook_id:
        definicao["webhookId"] = webhook_id
    return definicao


def ligar(conexoes, origem, destino, tipo="main"):
    ramos = conexoes.setdefault(origem, {}).setdefault(tipo, [[]])
    ramos[0].append({"node": destino, "type": tipo, "index": 0})


def nome_ferramenta(nome_no):
    # Regra do n8n (§3.2): tudo que não é letra sem acento, algarismo, hífen ou sublinhado vira _.
    return re.sub(r"[^A-Za-z0-9_-]", "_", nome_no)


def cred_groq(ids):
    return {"groqApi": {"id": ids["groq"], "name": "Groq"}}


def cred_ollama(ids):
    return {"ollamaApi": {"id": ids["ollama"], "name": "Ollama"}}
