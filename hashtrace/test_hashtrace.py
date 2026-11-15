import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from hashtrace import main, snapshot


class HashTraceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'arquivos'
        self.root.mkdir()
        self.base = Path(self.temp.name) / 'base.json'

    def run_cli(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return main(list(args))

    def test_full_lifecycle(self):
        (self.root / 'alterar.txt').write_text('antes')
        (self.root / 'excluir.txt').write_text('excluir')
        self.assertEqual(self.run_cli('registrar', str(self.root), '--base', str(self.base)), 0)
        self.assertEqual(self.run_cli('verificar', str(self.root), '--base', str(self.base)), 0)
        (self.root / 'alterar.txt').write_text('depois')
        (self.root / 'excluir.txt').unlink()
        (self.root / 'novo.txt').write_text('novo')
        report = Path(self.temp.name) / 'report.json'
        self.assertEqual(self.run_cli('verificar', str(self.root), '--base', str(self.base), '--json', str(report)), 1)
        import json
        data = json.loads(report.read_text())
        self.assertEqual(data['criados'], ['novo.txt'])
        self.assertEqual(data['alterados'], ['alterar.txt'])
        self.assertEqual(data['excluidos'], ['excluir.txt'])

    def test_base_inside_root_is_excluded(self):
        base = self.root / 'base.json'
        self.assertEqual(self.run_cli('registrar', str(self.root), '--base', str(base)), 0)
        self.assertEqual(self.run_cli('verificar', str(self.root), '--base', str(base)), 0)

    def test_refuses_overwrite(self):
        self.base.write_text('preservar')
        self.assertEqual(self.run_cli('registrar', str(self.root), '--base', str(self.base)), 2)
        self.assertEqual(self.base.read_text(), 'preservar')

    def test_invalid_base_and_wrong_folder(self):
        self.base.write_text('[]')
        self.assertEqual(self.run_cli('verificar', str(self.root), '--base', str(self.base)), 2)
        self.run_cli('registrar', str(self.root), '--base', str(self.base), '--sobrescrever')
        other = Path(self.temp.name) / 'outra'
        other.mkdir()
        self.assertEqual(self.run_cli('verificar', str(other), '--base', str(self.base)), 2)

    def test_nested_binary_file(self):
        (self.root / 'sub').mkdir()
        (self.root / 'sub' / 'dados.bin').write_bytes(bytes(range(256)))
        self.assertIn('sub/dados.bin', snapshot(self.root))

    def test_report_cannot_overwrite_monitored_file(self):
        file = self.root / 'dados.txt'
        file.write_text('preservar')
        self.run_cli('registrar', str(self.root), '--base', str(self.base))
        self.assertEqual(self.run_cli('verificar', str(self.root), '--base', str(self.base), '--json', str(file)), 2)
        self.assertEqual(file.read_text(), 'preservar')


if __name__ == '__main__':
    unittest.main()
