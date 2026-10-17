"""Build small, reproducible competition packages from the active Version-2 code.

The corrected package uses the current implementation. The batch10 package adds
one unverified hypothesis: all withholding is remitted on the next month's 10th.
No data, targets, caches, or diagnostic predictions enter either archive.
"""
import argparse
import hashlib
import json
import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]


def contents(source, variant):
    files = {}
    for path in sorted(source.rglob('*')):
        if '__pycache__' in path.parts or not path.is_file():
            continue
        if path.suffix not in ('.py', '.ipynb') and path.name != 'requirements.txt':
            continue
        content = path.read_bytes()
        if path.suffix == '.ipynb':
            notebook = json.loads(content)
            for cell in notebook.get('cells', []):
                if cell.get('cell_type') == 'code':
                    cell['outputs'] = []
                    cell['execution_count'] = None
            content = (json.dumps(notebook, ensure_ascii=False, indent=1) + '\n').encode()
        files[path.relative_to(source).as_posix()] = content
    if variant == 'batch10':
        text = files['tax_rules.py'].decode()
        old = "REMITTANCE_DAY = {'DE': 10, 'IT': 16}"
        if text.count(old) != 1:
            raise ValueError('The baseline date rules changed; review the batch10 transformation.')
        text = text.replace(old, "REMITTANCE_DAY = {'DE': 10, 'IT': 10, 'CH': 10}")
        text = text.replace('# Withheld taxes are paid on this day of the next month (DE, IT) or 30 days after the end of the month (CH)',
                            '# Experimental hypothesis: one monthly remittance batch on the 10th for every country.')
        files['tax_rules.py'] = text.encode()
    note = (
        '# T7 Version-2 candidate\n\n'
        'Withdrawals and surrenders use the amount after the surrender penalty for withholding. '
        'The raw fund value continues to drive Italian stamp-duty accruals. '
        'A payout without withholding has no remittance date. Death-benefit amounts and '
        'stamp-duty formulas retain the previous convention.\n\n'
        + ('This package tests an unverified common remittance date: the 10th of the next month '
           'for CH, IT and DE, including weekends.\n\n' if variant == 'batch10' else
           'This package retains the previous country-specific remittance dates.\n\n')
        + 'Both published task examples pass. No hidden T7 targets are available locally; '
        'these checks do not establish competition accuracy. The notebooks record earlier '
        'discovery work; the submitted Python modules define this candidate. '
        'Notebook outputs are omitted to satisfy the upload size limit.\n'
    )
    files['T7_CANDIDATE.md'] = note.encode()
    if 'submission.py' not in files or len(files) > 100:
        raise ValueError('Submission must have submission.py at root and at most 100 files.')
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--source', type=pathlib.Path, default=ROOT / 'starter_kit/my_solution')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for variant in ('corrected', 'batch10'):
        files = contents(args.source, variant)
        output = args.output / f't7-version2-{variant}.zip'
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, content in files.items():
                info = zipfile.ZipInfo(name, date_time=(2026, 10, 17, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, content)
        if output.stat().st_size > 5_000_000:
            raise ValueError('Submission exceeds 5 MB.')
        manifest[variant] = {'filename': output.name, 'bytes': output.stat().st_size,
                             'files': len(files), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                             'source_files': {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}}
    (args.output / 't7-candidate-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({name: {k: v for k, v in row.items() if k != 'source_files'}
                      for name, row in manifest.items()}, indent=2))


if __name__ == '__main__':
    main()
