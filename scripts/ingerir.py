"""Envia os PDFs de convenios/ ao formulário publicado e confere a execução (seção 4.7)."""
import json
import re
import time
import urllib.parse
import urllib.request
import uuid

from scripts import wf_ingestao
from scripts.execucoes import esperar_execucao, itens_saida, ultimo_id
from scripts.implantar import buscar_workflow
from scripts.n8n_api import BASE_URL, RAIZ

URL_FORM = f"{BASE_URL}/form/base-convenios"


def nome_campo_arquivo(html):
    for tag in re.findall(r"<input\b[^>]*>", html):
        if re.search(r"type=['\"]file['\"]", tag):
            return re.search(r"name=['\"]([^'\"]+)['\"]", tag).group(1)
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


def url_status(form_waiting_url):
    """URL de status do formulário multi-etapas: mesmo caminho + /n8n-execution-status, com a mesma query (signature)."""
    partes = urllib.parse.urlsplit(form_waiting_url)
    caminho = partes.path + "/n8n-execution-status"
    return urllib.parse.urlunsplit((partes.scheme, partes.netloc, caminho, partes.query, partes.fragment))


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
        corpo_resposta = resposta.read()
        print(f"POST {URL_FORM} -> {resposta.status}")
    try:
        dados_resposta = json.loads(corpo_resposta)
    except ValueError:
        dados_resposta = None
    if dados_resposta and dados_resposta.get("formWaitingUrl"):
        form_waiting_url = dados_resposta["formWaitingUrl"]
        fim = time.time() + 120
        situacao = ""
        while time.time() < fim and situacao not in ("form-waiting", "success"):
            with urllib.request.urlopen(url_status(form_waiting_url), timeout=30) as resposta:
                situacao = resposta.read().decode("utf-8").strip()
            if situacao not in ("form-waiting", "success"):
                time.sleep(1)
        if situacao == "form-waiting":
            with urllib.request.urlopen(form_waiting_url, timeout=30) as resposta:
                pagina_final = resposta.read().decode("utf-8")
            if "indexado(s)" in pagina_final:
                achado = re.search(r"\d+ arquivo\(s\) indexado\(s\) em \d+ trecho\(s\)\.", pagina_final)
                if achado:
                    print(achado.group(0))
            # O GET só busca a página; o cliente real do formulário, já carregado nela,
            # dispara um POST vazio para a mesma URL (com a assinatura), e é esse POST
            # que de fato libera o nó em espera (confirmado via API: sem ele a execução
            # fica em "waiting" mesmo após o GET).
            urllib.request.urlopen(
                urllib.request.Request(form_waiting_url, data=b"", method="POST"), timeout=30
            ).close()
    execucao = esperar_execucao(workflow_id, antes)
    arquivos = itens_saida(execucao, "Um item por arquivo")
    trechos = itens_saida(execucao, "Inserir na base")
    print(f"execução {execucao['id']}: {execucao['status']}")
    print(f"{arquivos} arquivo(s) indexado(s) em {trechos} trecho(s).")
    if execucao["status"] != "success" or (arquivos, trechos) != (len(pdfs), len(pdfs)):
        raise SystemExit("ingestão não conferiu: esperado um trecho por PDF")


if __name__ == "__main__":
    main()
