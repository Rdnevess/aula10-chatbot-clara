import unittest

from scripts.cenarios import CENARIOS, avaliar, subagentes


class CenariosTest(unittest.TestCase):
    def passo(self, ident):
        return next(p for p in CENARIOS if p["id"] == ident)

    def test_oito_cenarios_e_sessoes_compartilhadas(self):
        self.assertEqual(sorted({p["cenario"] for p in CENARIOS}), list(range(1, 9)))
        self.assertEqual({p["sessao"] for p in CENARIOS if p["cenario"] in (3, 4, 5)}, {"A"})

    def test_subagentes_filtra_e_ordena(self):
        nos = ["Mensagem recebida", "CLARA", "Sub-agente INFO", "Modelo da CLARA"]
        self.assertEqual(subagentes(nos), ["Sub-agente INFO"])

    def test_aprova_resposta_e_caminho_certos(self):
        ok, motivos = avaliar(self.passo("4"), "Objeto: Tecnologias Sustentáveis. Valor: R$ 250.000,00.",
                              ["Sub-agente CONVENIOS"])
        self.assertTrue(ok, motivos)

    def test_reprova_caminho_errado(self):
        ok, motivos = avaliar(self.passo("4"), "Tecnologias Sustentáveis, R$ 250.000,00", [])
        self.assertFalse(ok)
        self.assertIn("caminho", motivos[0])

    def test_reprova_texto_proibido(self):
        ok, motivos = avaliar(self.passo("6"), "Não há registro do 099/2026, mas o 047/2026 existe.",
                              ["Sub-agente CONVENIOS"])
        self.assertFalse(ok)

    def test_cenario_5_aceita_com_ou_sem_subagente(self):
        for acionados in ([], ["Sub-agente CONVENIOS"]):
            ok, _ = avaliar(self.passo("5"), "Fernanda Lopes Azevedo assina pela fundação.", acionados)
            self.assertTrue(ok)

    def test_comparacao_ignora_maiusculas(self):
        ok, _ = avaliar(self.passo("1"), "Olá! Eu sou a Clara.", [])
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
