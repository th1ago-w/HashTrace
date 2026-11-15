"""Monitor de integridade local usando SHA-256 e a biblioteca padrão."""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot(root, excluded=()):
    """Não segue links simbólicos; falhas impedem uma comparação incompleta."""
    excluded = {Path(p).resolve() for p in excluded}
    files = {}

    def visit(directory):
        for path in sorted(directory.iterdir()):
            if path.is_symlink() or path.resolve() in excluded:
                continue
            if path.is_dir():
                visit(path)
            elif path.is_file():
                files[path.relative_to(root).as_posix()] = sha256(path)

    visit(root)
    return files


def compare(before, after):
    return {
        'criados': sorted(after.keys() - before.keys()),
        'alterados': sorted(p for p in before.keys() & after.keys() if before[p] != after[p]),
        'excluidos': sorted(before.keys() - after.keys()),
    }


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description='HashTrace — compare a integridade de uma pasta com SHA-256.')
    commands = parser.add_subparsers(dest='command', required=True)
    for name, help_text in [('registrar', 'Cria uma referência dos arquivos atuais.'), ('verificar', 'Compara a pasta com uma referência salva.')]:
        cmd = commands.add_parser(name, help=help_text)
        cmd.add_argument('pasta', type=Path, help='Pasta a analisar.')
        cmd.add_argument('--base', type=Path, default=Path('referencia.json'), help='Arquivo de referência (padrão: referencia.json no diretório atual).')
        if name == 'registrar':
            cmd.add_argument('--sobrescrever', action='store_true', help='Permite substituir uma referência existente.')
        else:
            cmd.add_argument('--json', type=Path, dest='report', help='Salva também um relatório JSON.')
    args = parser.parse_args(argv)
    try:
        root = args.pasta.resolve(strict=True)
        if not root.is_dir():
            raise ValueError('O caminho informado precisa ser uma pasta.')
        base = args.base.resolve()
        if args.command == 'registrar':
            if base.exists() and not args.sobrescrever:
                raise ValueError('A referência já existe. Use --sobrescrever somente se quiser substituí-la.')
            files = snapshot(root, [base])
            save_json(base, dict(version=1, root=str(root), created_at=datetime.now(timezone.utc).isoformat(), files=files))
            print(f'Referência criada: {base}\nArquivos registrados: {len(files)}')
            return 0
        data = json.loads(base.read_text(encoding='utf-8'))
        if not isinstance(data, dict) or data.get('version') != 1 or not isinstance(data.get('files'), dict):
            raise ValueError('Formato de referência inválido.')
        if data.get('root') != str(root):
            raise ValueError('Esta referência pertence a outra pasta. Use a pasta original.')
        before = data['files']
        if not all(isinstance(p, str) and isinstance(h, str) and len(h) == 64 and all(c in '0123456789abcdef' for c in h) for p, h in before.items()):
            raise ValueError('A referência contém entradas inválidas.')
        report_path = args.report.resolve() if args.report else None
        if report_path and (report_path == base or report_path == root or root in report_path.parents):
            raise ValueError('Salve o relatório fora da pasta monitorada e em um arquivo diferente da referência.')
        changes = compare(before, snapshot(root, [base]))
        report = dict(root=str(root), checked_at=datetime.now(timezone.utc).isoformat(), **changes)
        for key, label in [('criados', 'CRIADOS'), ('alterados', 'ALTERADOS'), ('excluidos', 'EXCLUÍDOS')]:
            print(f'\n{label}: {len(changes[key])}')
            for path in changes[key]:
                print(f'  {path}')
        changed = any(changes.values())
        print('\nMudanças detectadas.' if changed else '\nNenhuma mudança detectada.')
        if report_path:
            save_json(report_path, report)
            print(f'Relatório salvo: {report_path}')
        return 1 if changed else 0
    except (OSError, ValueError, RecursionError) as error:
        print(f'Erro: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
