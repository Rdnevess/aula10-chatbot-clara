"""Cria no n8n, se ainda não existirem, as credenciais Groq e Ollama e a Data table chamados."""
from scripts.n8n_api import ErroApi, api, carregar_env

OLLAMA_URL = "http://host.docker.internal:11434"
COLUNAS = ("protocolo", "nome", "email", "descricao", "registrado_em")


def _buscar_credencial(nome, tipo):
    for credencial in api("GET", "/credentials?limit=250")["data"]:
        if credencial["name"] == nome and credencial["type"] == tipo:
            return credencial["id"]
    return None


def _buscar_tabela(nome):
    for tabela in api("GET", "/data-tables?limit=100")["data"]:
        if tabela["name"] == nome:
            return tabela["id"]
    return None


def obter_ids():
    ids = {
        "groq": _buscar_credencial("Groq", "groqApi"),
        "ollama": _buscar_credencial("Ollama", "ollamaApi"),
        "chamados": _buscar_tabela("chamados"),
    }
    faltando = [chave for chave, valor in ids.items() if not valor]
    if faltando:
        raise ErroApi(f"Recursos ausentes no n8n: {faltando}. Rode python -m scripts.configurar_n8n")
    return ids


def _garantir_credencial(nome, tipo, dados):
    existente = _buscar_credencial(nome, tipo)
    if existente:
        return existente, False
    return api("POST", "/credentials", {"name": nome, "type": tipo, "data": dados})["id"], True


def _garantir_tabela():
    existente = _buscar_tabela("chamados")
    if existente:
        return existente, False
    corpo = {"name": "chamados", "columns": [{"name": c, "type": "string"} for c in COLUNAS]}
    return api("POST", "/data-tables", corpo)["id"], True


def main():
    env = carregar_env()
    recursos = {
        "Groq": _garantir_credencial("Groq", "groqApi", {"apiKey": env["GROQ_API_KEY"]}),
        "Ollama": _garantir_credencial("Ollama", "ollamaApi", {"baseUrl": OLLAMA_URL}),
        "chamados": _garantir_tabela(),
    }
    for nome, (ident, criado) in recursos.items():
        print(f"{nome}: {ident} ({'criado' if criado else 'já existia'})")
    for nome in ("Groq", "Ollama"):
        try:
            resultado = api("POST", f"/credentials/{recursos[nome][0]}/test")
            print(f"teste {nome}: {resultado}")
        except ErroApi as erro:
            print(f"teste {nome}: FALHOU {erro}")


if __name__ == "__main__":
    main()
