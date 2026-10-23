import unittest

from scripts.exportar import normalizar, sem_segredos

DA_API = {
    "id": "abc", "name": "W", "active": True, "isArchived": False, "versionId": "v1",
    "createdAt": "2026-10-20", "updatedAt": "2026-10-20", "shared": [{"role": "x"}], "tags": [],
    "nodes": [{"name": "N", "credentials": {"groqApi": {"id": "G1", "name": "Groq"}}}],
    "connections": {}, "settings": {"executionOrder": "v1"}, "staticData": None,
}


class ExportarTest(unittest.TestCase):
    def test_mantem_so_campos_do_export_da_interface(self):
        wf = normalizar(DA_API)
        self.assertEqual(list(wf), ["name", "nodes", "connections", "settings", "pinData", "meta"])
        self.assertEqual(wf["pinData"], {})
        self.assertEqual(wf["meta"], {})

    def test_credenciais_so_por_referencia(self):
        self.assertTrue(sem_segredos(normalizar(DA_API)))
        vazado = normalizar({**DA_API, "nodes": [{"name": "N", "parameters": {"apiKey": "gsk_x"}}]})
        self.assertFalse(sem_segredos(vazado))


if __name__ == "__main__":
    unittest.main()
