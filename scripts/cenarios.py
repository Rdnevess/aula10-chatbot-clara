"""Roda os cenários da seção 6.2 contra o chat público e grava testes/resultados.json."""
import json
import time
import uuid

from scripts import wf_clara
from scripts.chat import ErroChat, enviar
from scripts.configurar_n8n import obter_ids
from scripts.execucoes import esperar_execucao, nos_executados, ultimo_id
from scripts.implantar import buscar_workflow
from scripts.n8n_api import RAIZ, api

PAUSA_S = 20
ESPERA_COTA_S = 60
OUTROS_CONVENIOS = ["021/2026", "034/2026", "047/2026", "85.000", "120.000", "250.000"]

CENARIOS = [
    {"id": "1", "cenario": 1, "sessao": "1", "mensagem": "oi",
     "subagentes_aceitos": [[]], "contem": ["CLARA"], "nao_contem": [],
     "esperado": "Nenhum sub-agente; apresenta-se como CLARA"},
    {"id": "2", "cenario": 2, "sessao": "2", "mensagem": "Qual o horário de atendimento e o e-mail de vocês?",
     "subagentes_aceitos": [["Sub-agente INFO"]], "contem": ["8h", "17h", "atendimento@nucleo-convenios.example"],
     "nao_contem": [], "esperado": "INFO; segunda a sexta, das 8h às 17h, e o e-mail do Núcleo"},
    {"id": "3", "cenario": 3, "sessao": "A", "mensagem": "Quero saber sobre um convênio.",
     "subagentes_aceitos": [[]], "contem": ["número"], "nao_contem": [],
     "esperado": "Nenhum sub-agente; pede o número no formato NNN/AAAA"},
    {"id": "4", "cenario": 4, "sessao": "A", "mensagem": "É o 047/2026. Qual o objeto e o valor?",
     "subagentes_aceitos": [["Sub-agente CONVENIOS"]], "contem": ["Tecnologias Sustentáveis", "250.000,00"],
     "nao_contem": [], "esperado": "CONVENIOS; \"Pesquisa Aplicada em Tecnologias Sustentáveis\" e R$ 250.000,00"},
    {"id": "5", "cenario": 5, "sessao": "A", "mensagem": "Quem assina pela fundação?",
     "subagentes_aceitos": [["Sub-agente CONVENIOS"], []], "contem": ["Fernanda Lopes Azevedo"], "nao_contem": [],
     "esperado": "CONVENIOS ou nenhum; Fernanda Lopes Azevedo, sem pedir o número de novo"},
    {"id": "6", "cenario": 6, "sessao": "6", "mensagem": "E o convênio 099/2026, qual o valor?",
     "subagentes_aceitos": [["Sub-agente CONVENIOS"]], "contem": ["registro"], "nao_contem": OUTROS_CONVENIOS,
     "esperado": "CONVENIOS; não há registro desse número; não cita outros convênios"},
    {"id": "7a", "cenario": 7, "sessao": "7",
     "mensagem": "Preciso falar com uma pessoa: meu pedido de aditivo do convênio 021/2026 está parado há um mês.",
     "subagentes_aceitos": [[]], "contem": ["e-mail"], "nao_contem": [],
     "esperado": "Nenhum sub-agente; pede só nome e e-mail"},
    {"id": "7b", "cenario": 7, "sessao": "7", "mensagem": "Sou Carlos Mendes, carlos.mendes@exemplo.example",
     "subagentes_aceitos": [["Sub-agente ATENDIMENTO"]], "contem": ["CH-"], "nao_contem": [],
     "esperado": "ATENDIMENTO; protocolo CH-…; nova linha na tabela chamados"},
    {"id": "8a", "cenario": 8, "sessao": "8", "mensagem": "Meu nome é Maria.",
     "subagentes_aceitos": [[]], "contem": [], "nao_contem": [], "esperado": "Nenhum sub-agente"},
    {"id": "8b", "cenario": 8, "sessao": "8", "mensagem": "Você lembra meu nome?",
     "subagentes_aceitos": [[]], "contem": ["Maria"], "nao_contem": [],
     "esperado": "Nenhum sub-agente; responde Maria, pela memória da sessão"},
]


def subagentes(nos):
    return sorted(n for n in nos if n in wf_clara.SUB_AGENTES)


def avaliar(passo, resposta, acionados):
    motivos = []
    if sorted(acionados) not in [sorted(a) for a in passo["subagentes_aceitos"]]:
        motivos.append(f"caminho: acionou {acionados or 'nenhum'}, aceitos {passo['subagentes_aceitos']}")
    texto = resposta.lower()
    motivos += [f"faltou '{t}'" for t in passo["contem"] if t.lower() not in texto]
    motivos += [f"citou '{t}'" for t in passo["nao_contem"] if t.lower() in texto]
    return not motivos, motivos


def _enviar_com_retentativa(sessao, mensagem):
    try:
        return enviar(sessao, mensagem)
    except ErroChat as erro:
        print(f"  erro {erro}; aguardando {ESPERA_COTA_S} s e reenviando")
        time.sleep(ESPERA_COTA_S)
        return enviar(sessao, mensagem)


def _linha_do_chamado(tabela_id, email):
    linhas = api("GET", f"/data-tables/{tabela_id}/rows?limit=100")["data"]
    return next((l for l in linhas if l.get("email") == email), None)


def main():
    workflow_id = buscar_workflow(wf_clara.NOME)["id"]
    tabela_id = obter_ids()["chamados"]
    rodada = uuid.uuid4().hex[:8]
    resultados = []
    for indice, passo in enumerate(CENARIOS):
        if indice:
            time.sleep(PAUSA_S)
        antes = ultimo_id(workflow_id)
        resposta = _enviar_com_retentativa(f"teste-{rodada}-{passo['sessao']}", passo["mensagem"])
        execucao = esperar_execucao(workflow_id, antes)
        acionados = subagentes(nos_executados(execucao))
        ok, motivos = avaliar(passo, resposta, acionados)
        resultado = {**passo, "resposta": resposta, "acionados": acionados, "ok": ok, "motivos": motivos,
                     "execucao": execucao["id"]}
        if passo["id"] == "7b":
            linha = _linha_do_chamado(tabela_id, "carlos.mendes@exemplo.example")
            resultado["linha_chamados"] = linha
            if not linha:
                resultado["ok"] = False
                resultado["motivos"].append("nenhuma linha nova em chamados")
        resultados.append(resultado)
        print(f"[{passo['id']}] {'OK' if resultado['ok'] else 'FALHOU'} {acionados} {resultado['motivos']}")
    destino = RAIZ / "testes" / "resultados.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"gravado em {destino}")


if __name__ == "__main__":
    main()
