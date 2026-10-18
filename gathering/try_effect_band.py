#!/usr/bin/env python3
"""Apply the shared effect-band view to actual local fixed-policy observations."""
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def main():
    run = subprocess.run([sys.executable, '-B', 'line-1/tools/policy-benchmark/policy_benchmark.py', 'demo'],
                         cwd=ROOT, capture_output=True, check=True, timeout=30)
    measurement = json.loads(run.stdout)
    names = list(measurement['passes'])
    # CLI canonical JSON sorts object keys, so use explicit system roles.
    baseline = 'python-default-v1'
    candidates = ['reject-constants-v1', 'unique-finite-v1']
    if set(names) != {baseline, *candidates}:
        raise ValueError('unexpected policy system names')
    stream = io.StringIO(newline='')
    writer = csv.writer(stream, lineterminator='\n')
    writer.writerow(['case', 'baseline', *candidates])
    for row in measurement['observations']:
        writer.writerow([row['case'], row['passed'][baseline], *[row['passed'][n] for n in candidates]])
    raw = stream.getvalue().encode('utf-8')
    spec = importlib.util.spec_from_file_location('measured_effect_band', ROOT/'shared/effect-band/effect_band.py')
    band = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(band)
    result = band.review(raw, '1/4', '1/10')
    print(json.dumps({'data_kind': 'actual_local_execution_on_18_curated_JSON_cases',
                     'note': 'Descriptive illustration with a post hoc example band, not preregistered acceptance or population inference.',
                     'policy_passes': measurement['passes'], 'recheck': measurement['recheck'],
                     'case_source_sha256': hashlib.sha256((ROOT/'line-1/tools/policy-benchmark/cases.json').read_bytes()).hexdigest(),
                     'observations_csv': raw.decode('utf-8'), 'effect_band': result}, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
