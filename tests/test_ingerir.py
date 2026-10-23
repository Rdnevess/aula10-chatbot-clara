import unittest

from scripts.ingerir import montar_multipart, nome_campo_arquivo


class IngerirTest(unittest.TestCase):
    def test_nome_do_campo_de_arquivo(self):
        html = '<form><input type="text" name="x"/><input type="file" id="f" name="field-0" multiple accept=".pdf"/></form>'
        self.assertEqual(nome_campo_arquivo(html), "field-0")

    def test_nome_do_campo_com_name_antes_do_type(self):
        self.assertEqual(nome_campo_arquivo('<input name="documentos" type="file">'), "documentos")

    def test_nome_do_campo_com_aspas_simples_multilinhas(self):
        html = """<input
class='form-input form-required'
type='file'
id='field-0'
name='field-0'
accept='.pdf'
multiple
placeholder=""
/>"""
        self.assertEqual(nome_campo_arquivo(html), "field-0")

    def test_multipart(self):
        corpo = montar_multipart("field-0", [("a.pdf", b"%PDF-1")], "LIM")
        self.assertEqual(corpo, (
            b'--LIM\r\nContent-Disposition: form-data; name="field-0"; filename="a.pdf"\r\n'
            b"Content-Type: application/pdf\r\n\r\n%PDF-1\r\n--LIM--\r\n"
        ))


if __name__ == "__main__":
    unittest.main()
