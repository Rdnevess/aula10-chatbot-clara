"""Desliga o chat público, exporta os dois workflows para workflows/ e gera o .zip de entrega.

Só o pacote, sem exportar de novo: python -c "from scripts.exportar import gerar_zip; gerar_zip()"
"""
import json
import re
import zipfile

from scripts import wf_clara, wf_ingestao
from scripts.configurar_n8n import obter_ids
from scripts.implantar import buscar_workflow, implantar
from scripts.n8n_api import RAIZ, api

CAMPOS = ("name", "nodes", "connections", "settings", "pinData", "meta")
ARQUIVOS = {wf_ingestao.NOME: "ingestao-convenios.json", wf_clara.NOME: "clara-multiagente.json"}
ZIP = RAIZ / "entrega-aula10.zip"


def normalizar(wf):
    return {campo: (wf.get(campo) or {}) if campo in ("pinData", "meta") else wf.get(campo) for campo in CAMPOS}


def sem_segredos(wf):
    texto = json.dumps(wf)
    return not re.search(r'"(apiKey|password|accessToken|token)"\s*:|gsk_[A-Za-z0-9]', texto)


def main():
    implantar(wf_clara.construir(obter_ids(), chat_publico=False))
    for nome, arquivo in ARQUIVOS.items():
        wf = normalizar(api("GET", f"/workflows/{buscar_workflow(nome)['id']}"))
        if not sem_segredos(wf):
            raise SystemExit(f"{nome}: possível segredo no JSON; exportação interrompida")
        destino = RAIZ / "workflows" / arquivo
        destino.write_text(json.dumps(wf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{nome} -> {destino.relative_to(RAIZ)}")
    gerar_zip()


def gerar_zip():
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as pacote:
        for arquivo in ARQUIVOS.values():
            pacote.write(RAIZ / "workflows" / arquivo, f"workflows/{arquivo}")
        pacote.write(RAIZ / "testes.md", "testes.md")
        pacote.write(RAIZ / "LINK-GIT.txt", "LINK-GIT.txt")
    print(f"pacote: {ZIP.name}")


if __name__ == "__main__":
    main()
