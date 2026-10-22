"""Envia mensagens ao chat público da CLARA (webhook do Chat Trigger)."""
import json
import urllib.error
import urllib.request

from scripts import wf_clara
from scripts.n8n_api import BASE_URL

URL_CHAT = f"{BASE_URL}/webhook/{wf_clara.WEBHOOK_CHAT}/chat"


class ErroChat(Exception):
    pass


def enviar(session_id, mensagem):
    corpo = json.dumps({"action": "sendMessage", "sessionId": session_id, "chatInput": mensagem}).encode("utf-8")
    requisicao = urllib.request.Request(URL_CHAT, data=corpo, method="POST",
                                        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(requisicao, timeout=180) as resposta:
            texto = resposta.read().decode("utf-8")
    except urllib.error.HTTPError as erro:
        raise ErroChat(f"{erro.code}: {erro.read().decode('utf-8', 'replace')[:300]}") from None
    try:
        return json.loads(texto)["output"]
    except (ValueError, KeyError):
        return texto
