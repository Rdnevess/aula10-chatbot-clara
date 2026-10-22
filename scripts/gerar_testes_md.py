"""Gera testes.md (passos 3 e 4 do laboratório) a partir de testes/resultados.json."""
import json

from scripts.n8n_api import RAIZ

CABECALHO = (
    "# Testes por cenário — CLARA multiagente\n\n"
    "Cenários da seção 6.2 da apostila, enviados ao chat da CLARA com um `sessionId` por cenário "
    "(3, 4 e 5 na mesma sessão). O sub-agente vem do registro da execução (nós executados), "
    "equivalente ao painel Logs.\n\n"
    "| # | Mensagem(ns) | Resposta obtida | Sub-agente (registro) | Esperado | OK? |\n"
    "| --- | --- | --- | --- | --- | --- |\n"
)
AJUSTES = (
    "\n## Ajustes de prompt\n\n"
    "| Cenário | Instrução anterior | Instrução nova | Resultado do novo teste |\n"
    "| --- | --- | --- | --- |\n"
)


def celula(texto):
    return str(texto).replace("|", "\\|").replace("\r", "").replace("\n", "<br>")


def gerar(resultados, ajustes=()):
    linhas = []
    for r in resultados:
        sub = ", ".join(s.replace("Sub-agente ", "") for s in r["acionados"]) or "nenhum"
        ok = "sim" if r["ok"] else "não — " + "; ".join(r["motivos"])
        linhas.append(f"| {r['id']} | {celula(r['mensagem'])} | {celula(r['resposta'])} | {sub} | "
                      f"{celula(r['esperado'])} | {celula(ok)} |")
    corpo = CABECALHO + "\n".join(linhas) + "\n" + AJUSTES
    if ajustes:
        corpo += "\n".join(f"| {a['cenario']} | {celula(a['anterior'])} | {celula(a['nova'])} | "
                           f"{celula(a['resultado'])} |" for a in ajustes) + "\n"
    else:
        corpo += "| — | Nenhum ajuste necessário | — | — |\n"
    return corpo


def main():
    resultados = json.loads((RAIZ / "testes" / "resultados.json").read_text(encoding="utf-8"))
    caminho_ajustes = RAIZ / "testes" / "ajustes.json"
    ajustes = json.loads(caminho_ajustes.read_text(encoding="utf-8")) if caminho_ajustes.exists() else ()
    (RAIZ / "testes.md").write_text(gerar(resultados, ajustes), encoding="utf-8")
    print("testes.md gerado")


if __name__ == "__main__":
    main()
