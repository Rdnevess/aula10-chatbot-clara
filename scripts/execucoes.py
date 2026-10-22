"""Leitura das execuções de um workflow pela API pública (equivale ao painel Logs)."""
import time

from scripts.n8n_api import api

TERMINADAS = {"success", "error", "crashed", "canceled"}


def ultimo_id(workflow_id):
    dados = api("GET", f"/executions?workflowId={workflow_id}&limit=1")["data"]
    return int(dados[0]["id"]) if dados else 0


def esperar_execucao(workflow_id, depois_de, limite_s=120):
    fim = time.time() + limite_s
    while time.time() < fim:
        dados = api("GET", f"/executions?workflowId={workflow_id}&limit=1")["data"]
        if dados and int(dados[0]["id"]) > depois_de and dados[0]["status"] in TERMINADAS:
            return api("GET", f"/executions/{dados[0]['id']}?includeData=true")
        time.sleep(2)
    raise TimeoutError(f"nenhuma execução nova de {workflow_id} terminou em {limite_s} s")


def nos_executados(execucao):
    return list(execucao["data"]["resultData"]["runData"].keys())


def itens_saida(execucao, nome_no):
    total = 0
    for rodada in execucao["data"]["resultData"]["runData"].get(nome_no, []):
        saidas = (rodada.get("data") or {}).get("main") or []
        if saidas and saidas[0]:
            total += len(saidas[0])
    return total
