import unittest

from scripts import wf_ingestao
from scripts.wf_util import nome_ferramenta

IDS = {"groq": "G1", "ollama": "O1", "chamados": "T1"}


class IngestaoTest(unittest.TestCase):
    def setUp(self):
        self.wf = wf_ingestao.construir(IDS)
        self.nos = {n["name"]: n for n in self.wf["nodes"]}

    def test_nome_e_nos_da_apostila(self):
        self.assertEqual(self.wf["name"], "Aula 10 - Ingestão dos convênios")
        self.assertEqual(set(self.nos), {
            "Enviar convênios", "Um item por arquivo", "Extrair texto", "Inserir na base",
            "Base atualizada", "Embeddings", "Carregar documento", "Dividir em trechos",
        })

    def test_conexoes_apontam_para_nos_existentes(self):
        for origem, saidas in self.wf["connections"].items():
            self.assertIn(origem, self.nos)
            for ramos in saidas.values():
                for ramo in ramos:
                    for destino in ramo:
                        self.assertIn(destino["node"], self.nos)

    def test_fluxo_principal_em_ordem(self):
        c = self.wf["connections"]
        seq = ["Enviar convênios", "Um item por arquivo", "Extrair texto", "Inserir na base", "Base atualizada"]
        for a, b in zip(seq, seq[1:]):
            self.assertEqual(c[a]["main"][0][0]["node"], b)

    def test_sub_nos_ligados(self):
        c = self.wf["connections"]
        self.assertEqual(c["Embeddings"]["ai_embedding"][0][0]["node"], "Inserir na base")
        self.assertEqual(c["Carregar documento"]["ai_document"][0][0]["node"], "Inserir na base")
        self.assertEqual(c["Dividir em trechos"]["ai_textSplitter"][0][0]["node"], "Carregar documento")

    def test_parametros_chave(self):
        base = self.nos["Inserir na base"]["parameters"]
        self.assertEqual(base["memoryKey"]["value"], "convenios")
        self.assertTrue(base["clearStore"])
        self.assertEqual(base["embeddingBatchSize"], 50)
        trechos = self.nos["Dividir em trechos"]["parameters"]
        self.assertEqual((trechos["chunkSize"], trechos["chunkOverlap"]), (1000, 150))
        self.assertEqual(self.nos["Enviar convênios"]["parameters"]["options"]["path"], "base-convenios")
        self.assertEqual(self.nos["Embeddings"]["credentials"], {"ollamaApi": {"id": "O1", "name": "Ollama"}})

    def test_metadados(self):
        meta = self.nos["Carregar documento"]["parameters"]["options"]["metadata"]["metadataValues"]
        self.assertEqual([m["name"] for m in meta], ["arquivo", "convenio"])


class NomeFerramentaTest(unittest.TestCase):
    def test_troca_acento_e_espaco(self):
        self.assertEqual(nome_ferramenta("Sub-agente INFO"), "Sub-agente_INFO")
        self.assertEqual(nome_ferramenta("Base de convênios"), "Base_de_conv_nios")


if __name__ == "__main__":
    unittest.main()
