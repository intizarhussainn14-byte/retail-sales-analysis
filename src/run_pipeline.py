"""Run tests, inspection, cleaning, analysis and Power BI packaging in order."""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from inspect_data import ROOT, sha256
from project_paths import relative_path


def stage(script, arguments, parent, pattern):
    before = set(parent.glob(pattern))
    print(f'Running {script}...', flush=True)
    # Stream progress/output; check=True prevents later stages after a failure.
    subprocess.run([sys.executable, str(ROOT/'src'/script), *map(str, arguments)], cwd=ROOT, check=True)
    created = set(parent.glob(pattern)) - before
    if len(created) != 1:
        raise RuntimeError('Expected one new output folder; do not run pipelines concurrently')
    return created.pop()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=ROOT/'data/raw/Online Retail.xlsx')
    args = p.parse_args()
    source = args.input.resolve()
    if not source.is_file():
        raise FileNotFoundError('Download Online Retail.xlsx from UCI and place it in data/raw/; see README.md')
    if not __debug__:
        raise RuntimeError('Do not use python -O: validation assertions must stay enabled')
    source_hash = sha256(source)
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT/'src'), '-p', 'test_*.py', '-v'], cwd=ROOT, check=True)
    inspection = stage('inspect_data.py', ['--input', source], ROOT/'reports', 'inspection_*')
    cleaning = stage('clean_data.py', ['--input', source], ROOT/'data/processed', 'cleaning_*')
    analysis = stage('analyze_sales.py', ['--input', cleaning/'completed_sales.csv', '--inspection', inspection/'inspection.json'], ROOT/'reports', 'analysis_*')
    powerbi = stage('prepare_powerbi.py', ['--analysis', analysis], ROOT/'dashboard', 'powerbi_*')
    assert sha256(source) == source_hash
    old = ROOT/'reports/analysis_20261017T163159_486015Z'
    comparisons = {}
    for name in ['kpis', 'monthly', 'top_products_revenue', 'top_products_quantity', 'countries', 'customer_purchases', 'repeat_purchasing']:
        prior = old/f'{name}.csv'
        if prior.exists():
            equal = prior.read_bytes() == (analysis/f'{name}.csv').read_bytes()
            comparisons[name] = equal
            if not equal:
                raise AssertionError(f'{name} differs from the checked-in validated reference; review before accepting new findings')
    result = {'status': 'PASS: Python workflow executed; SQL, Excel and native Power BI not executed/built',
              'raw_sha256': source_hash, 'raw_unchanged': True,
              'inspection': relative_path(inspection), 'cleaning': relative_path(cleaning),
              'analysis': relative_path(analysis), 'powerbi_package': relative_path(powerbi),
              'byte_identical_analysis_tables_vs_original': comparisons}
    manifest = ROOT/'reports'/datetime.now(timezone.utc).strftime('reproduction_%Y%m%dT%H%M%S_%fZ.json')
    manifest.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('Reproduction manifest:', relative_path(manifest), flush=True)


if __name__ == '__main__':
    main()
