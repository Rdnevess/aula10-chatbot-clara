"""Cria ou atualiza um workflow da aula no n8n e o publica.

Uso: python -m scripts.implantar ingestao|clara [--chat-publico]
"""
import sys

from scripts import wf_clara, wf_ingestao
from scripts.configurar_n8n import obter_ids
from scripts.n8n_api import api


def buscar_workflow(nome):
    for wf in api("GET", "/workflows?limit=250")["data"]:
        if wf["name"] == nome and not wf.get("isArchived"):
            return wf
    return None


def implantar(definicao):
    existente = buscar_workflow(definicao["name"])
    if existente:
        wf = api("PUT", f"/workflows/{existente['id']}", definicao)
    else:
        wf = api("POST", "/workflows", definicao)
    api("POST", f"/workflows/{wf['id']}/publish", {"versionId": wf["versionId"]})
    return wf["id"]


def main(argumentos):
    ids = obter_ids()
    if argumentos[:1] == ["ingestao"]:
        definicao = wf_ingestao.construir(ids)
    elif argumentos[:1] == ["clara"]:
        definicao = wf_clara.construir(ids, chat_publico="--chat-publico" in argumentos)
    else:
        sys.exit(__doc__)
    print(f"{definicao['name']}: {implantar(definicao)} publicado")


if __name__ == "__main__":
    main(sys.argv[1:])
