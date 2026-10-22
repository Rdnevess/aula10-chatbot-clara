import unittest

from scripts.gerar_testes_md import celula, gerar


class GerarTestesMdTest(unittest.TestCase):
    def test_celula_escapa_barra_e_quebra(self):
        self.assertEqual(celula("a|b\nc"), "a\\|b<br>c")

    def test_tabela(self):
        md = gerar([{"id": "1", "mensagem": "oi", "resposta": "Sou a CLARA", "acionados": [],
                     "esperado": "Apresenta-se como CLARA", "ok": True, "motivos": [], "execucao": "10"}])
        self.assertIn("| # | Mensagem(ns) | Resposta obtida | Sub-agente (registro) | Esperado | OK? |", md)
        self.assertIn("| 1 | oi | Sou a CLARA | nenhum | Apresenta-se como CLARA | sim |", md)


if __name__ == "__main__":
    unittest.main()
