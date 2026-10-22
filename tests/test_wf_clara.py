import re
import unittest

from scripts import wf_clara
from scripts.wf_util import nome_ferramenta

IDS = {"groq": "G1", "ollama": "O1", "chamados": "T1"}


class ClaraTest(unittest.TestCase):
    def setUp(self):
        self.wf = wf_clara.construir(IDS)
        self.nos = {n["name"]: n for n in self.wf["nodes"]}
        self.c = self.wf["connections"]

    def test_nos_da_apostila(self):
        self.assertEqual(self.wf["name"], "Aula 10 - CLARA multiagente")
        self.assertEqual(set(self.nos), {
            "Mensagem recebida", "CLARA", "Modelo da CLARA", "Memória",
            "Sub-agente INFO", "Sub-agente CONVENIOS", "Sub-agente ATENDIMENTO",
            "Modelo dos sub-agentes", "Base de convenios", "Embeddings", "Registrar chamado",
        })

    def test_conexoes_apontam_para_nos_existentes(self):
        for origem, saidas in self.c.items():
            self.assertIn(origem, self.nos)
            for ramos in saidas.values():
                for ramo in ramos:
                    for destino in ramo:
                        self.assertIn(destino["node"], self.nos)

    def destinos(self, origem, tipo):
        return sorted(d["node"] for d in self.c[origem][tipo][0])

    def test_ligacoes(self):
        self.assertEqual(self.destinos("Mensagem recebida", "main"), ["CLARA"])
        self.assertEqual(self.destinos("Modelo da CLARA", "ai_languageModel"), ["CLARA"])
        self.assertEqual(self.destinos("Memória", "ai_memory"), ["CLARA"])
        for sub in wf_clara.SUB_AGENTES:
            self.assertEqual(self.destinos(sub, "ai_tool"), ["CLARA"])
        self.assertEqual(self.destinos("Modelo dos sub-agentes", "ai_languageModel"), sorted(wf_clara.SUB_AGENTES))
        self.assertEqual(self.destinos("Base de convenios", "ai_tool"), ["Sub-agente CONVENIOS"])
        self.assertEqual(self.destinos("Embeddings", "ai_embedding"), ["Base de convenios"])
        self.assertEqual(self.destinos("Registrar chamado", "ai_tool"), ["Sub-agente ATENDIMENTO"])

    def test_ferramentas_citadas_nos_prompts_existem(self):
        ferramentas = {nome_ferramenta(n) for n in self.nos}
        textos = [self.nos["CLARA"]["parameters"]["options"]["systemMessage"]]
        textos += [self.nos[s]["parameters"]["options"]["systemMessage"] for s in wf_clara.SUB_AGENTES]
        citadas = set()
        for texto in textos:
            citadas |= set(re.findall(r"\b(?:Sub-agente_[A-Z]+|Base_de_convenios|Registrar_chamado)\b", texto))
        self.assertTrue(citadas)
        self.assertLessEqual(citadas, ferramentas)

    def test_modelos_e_limites(self):
        self.assertEqual(self.nos["Modelo da CLARA"]["parameters"]["model"], "openai/gpt-oss-120b")
        self.assertEqual(self.nos["Modelo dos sub-agentes"]["parameters"]["model"], "openai/gpt-oss-20b")
        for modelo in ("Modelo da CLARA", "Modelo dos sub-agentes"):
            self.assertEqual(self.nos[modelo]["parameters"]["options"]["temperature"], 0.2)
            self.assertEqual(self.nos[modelo]["credentials"], {"groqApi": {"id": "G1", "name": "Groq"}})
        for sub in wf_clara.SUB_AGENTES:
            self.assertEqual(self.nos[sub]["parameters"]["options"]["maxIterations"], 4)
        self.assertEqual(self.nos["Memória"]["parameters"]["contextWindowLength"], 10)
        base = self.nos["Base de convenios"]["parameters"]
        self.assertEqual((base["mode"], base["memoryKey"]["value"], base["topK"]), ("retrieve-as-tool", "convenios", 4))
        self.assertTrue(base["includeDocumentMetadata"])

    def test_registrar_chamado(self):
        p = self.nos["Registrar chamado"]["parameters"]
        self.assertEqual(p["dataTableId"]["value"], "T1")
        valores = p["columns"]["value"]
        self.assertEqual(set(valores), {"protocolo", "nome", "email", "descricao", "registrado_em"})
        for campo in ("nome", "email", "descricao"):
            self.assertIn("$fromAI", valores[campo])
        for campo in ("protocolo", "registrado_em"):
            self.assertNotIn("$fromAI", valores[campo])

    def test_chat_publico_so_quando_pedido(self):
        self.assertFalse(self.nos["Mensagem recebida"]["parameters"].get("public", False))
        publico = {n["name"]: n for n in wf_clara.construir(IDS, chat_publico=True)["nodes"]}
        self.assertTrue(publico["Mensagem recebida"]["parameters"]["public"])


if __name__ == "__main__":
    unittest.main()
