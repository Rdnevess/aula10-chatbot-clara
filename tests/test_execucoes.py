import unittest

from scripts.execucoes import itens_saida, nos_executados

EXECUCAO = {"data": {"resultData": {"runData": {
    "Um item por arquivo": [{"data": {"main": [[{"json": {}}, {"json": {}}, {"json": {}}]]}}],
    "Embeddings": [{"data": {"ai_embedding": [[{"json": {}}]]}}],
    "Sub-agente CONVENIOS": [{"data": {"ai_tool": [[{"json": {}}]]}}],
}}}}


class ExecucoesTest(unittest.TestCase):
    def test_nos_executados(self):
        self.assertEqual(nos_executados(EXECUCAO), ["Um item por arquivo", "Embeddings", "Sub-agente CONVENIOS"])

    def test_itens_saida_main(self):
        self.assertEqual(itens_saida(EXECUCAO, "Um item por arquivo"), 3)

    def test_itens_saida_no_ausente_ou_sem_main(self):
        self.assertEqual(itens_saida(EXECUCAO, "Embeddings"), 0)
        self.assertEqual(itens_saida(EXECUCAO, "Nao existe"), 0)


if __name__ == "__main__":
    unittest.main()
