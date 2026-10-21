import tempfile
import unittest
from pathlib import Path

from scripts.n8n_api import carregar_env


class CarregarEnvTest(unittest.TestCase):
    def ler(self, texto):
        with tempfile.TemporaryDirectory() as d:
            caminho = Path(d) / ".env"
            caminho.write_text(texto, encoding="utf-8")
            return carregar_env(caminho)

    def test_le_pares_ignorando_comentarios_e_linhas_vazias(self):
        env = self.ler("# chaves\n\nN8N_API_KEY=abc\nGROQ_API_KEY = gsk_1\n")
        self.assertEqual(env, {"N8N_API_KEY": "abc", "GROQ_API_KEY": "gsk_1"})

    def test_remove_aspas_e_preserva_igual_no_valor(self):
        env = self.ler('A="x=y"\nB=\'z\'\n')
        self.assertEqual(env, {"A": "x=y", "B": "z"})


if __name__ == "__main__":
    unittest.main()
