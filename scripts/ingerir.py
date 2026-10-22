"""Envia os PDFs de convenios/ ao formulário publicado e confere a execução (seção 4.7)."""
import re
import urllib.request
import uuid

from scripts import wf_ingestao
from scripts.execucoes import esperar_execucao, itens_saida, ultimo_id
from scripts.implantar import buscar_workflow
from scripts.n8n_api import BASE_URL, RAIZ

URL_FORM = f"{BASE_URL}/form/base-convenios"


def nome_campo_arquivo(html):
    for tag in re.findall(r"<input\b[^>]*>", html):
        if re.search(r'type="file"', tag):
            return re.search(r'name="([^"]+)"', tag).group(1)
    raise ValueError("o formulário não tem campo de arquivo")


def montar_multipart(campo, arquivos, limite):
    partes = []
    for nome, conteudo in arquivos:
        cabecalho = (
            f'--{limite}\r\nContent-Disposition: form-data; name="{campo}"; filename="{nome}"\r\n'
            "Content-Type: application/pdf\r\n\r\n"
        )
        partes.append(cabecalho.encode("utf-8") + conteudo + b"\r\n")
    return b"".join(partes) + f"--{limite}--\r\n".encode("utf-8")


def main():
    workflow_id = buscar_workflow(wf_ingestao.NOME)["id"]
    antes = ultimo_id(workflow_id)
    with urllib.request.urlopen(URL_FORM, timeout=30) as resposta:
        campo = nome_campo_arquivo(resposta.read().decode("utf-8"))
    pdfs = sorted((RAIZ / "convenios").glob("*.pdf"))
    limite = uuid.uuid4().hex
    corpo = montar_multipart(campo, [(p.name, p.read_bytes()) for p in pdfs], limite)
    requisicao = urllib.request.Request(URL_FORM, data=corpo, method="POST",
                                        headers={"Content-Type": f"multipart/form-data; boundary={limite}"})
    with urllib.request.urlopen(requisicao, timeout=120) as resposta:
        print(f"POST {URL_FORM} -> {resposta.status}")
    execucao = esperar_execucao(workflow_id, antes)
    arquivos = itens_saida(execucao, "Um item por arquivo")
    trechos = itens_saida(execucao, "Inserir na base")
    print(f"execução {execucao['id']}: {execucao['status']}")
    print(f"{arquivos} arquivo(s) indexado(s) em {trechos} trecho(s).")
    if execucao["status"] != "success" or (arquivos, trechos) != (len(pdfs), len(pdfs)):
        raise SystemExit("ingestão não conferiu: esperado um trecho por PDF")


if __name__ == "__main__":
    main()
