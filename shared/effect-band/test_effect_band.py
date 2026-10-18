import copy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('effect_band', HERE/'effect_band.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def csv_bytes(rows):
    return ('case,baseline,first,second\n' + ''.join(
        f'case-{i},' + ','.join(map(str, row)) + '\n' for i, row in enumerate(rows))).encode()


class EffectBandTests(unittest.TestCase):
    def test_demo_full_pass_but_single_deletion_band_fails(self):
        r = app.demo()
        self.assertEqual(r['sensitivity']['deletions_checked'], 8)
        self.assertEqual(r['sensitivity']['cases_changing_decision_or_direction'], 7)
        for c in r['candidates']:
            self.assertEqual(c['full_effect'], '7/8')
            self.assertEqual(c['single_deletion_range'], {'minimum': '6/7', 'maximum': '1'})
            self.assertTrue(c['full_data_check']['passes'])
            self.assertTrue(c['minimum_check']['passes'])
            self.assertFalse(c['maximum_check']['passes'])
            self.assertFalse(c['all_single_deletion_effects_within_band'])
            self.assertEqual(c['full_data_check']['margin'], '0.025')

    def test_generated_results_against_direct_fraction_deletions(self):
        rng = random.Random(9)
        for trial in range(80):
            rows = [tuple(rng.randrange(2) for _ in range(3)) for _ in range(rng.randrange(2, 14))]
            ref, atol, rtol = Fraction(-1, 5), Fraction(1, 10), Fraction(1, 4)
            result = app.review(csv_bytes(rows), str(ref), str(atol), str(rtol))
            for index, item in enumerate(result['candidates'], 1):
                effects = [Fraction(sum(row[index]-row[0] for i, row in enumerate(rows) if i != removed), len(rows)-1)
                           for removed in range(len(rows))]
                self.assertEqual(Fraction(item['single_deletion_range']['minimum']), min(effects))
                self.assertEqual(Fraction(item['single_deletion_range']['maximum']), max(effects))
                allowed = atol + rtol * abs(ref)
                self.assertEqual(item['all_single_deletion_effects_within_band'],
                                 all(abs(effect-ref) <= allowed for effect in effects))

    def test_inclusive_boundary_zero_and_signed_effects(self):
        raw = csv_bytes([(1, 0, 0), (0, 1, 1)])
        # Deletion effects are exactly -1 and +1, full effect zero.
        result = app.review(raw, '0', '1')
        self.assertTrue(all(c['all_single_deletion_effects_within_band'] for c in result['candidates']))
        result = app.review(raw, '0', '999/1000')
        self.assertTrue(all(c['full_data_check']['passes'] for c in result['candidates']))
        self.assertFalse(any(c['all_single_deletion_effects_within_band'] for c in result['candidates']))

    def test_original_analysis_and_input_never_changed(self):
        raw = app.influence.demo_csv()
        original = bytes(raw)
        expected = app.influence.review(raw, '0.1', 0)
        actual = app.review(raw, '0', '1/10', '1/100', '0.1', 0)
        self.assertEqual(actual['sensitivity'], expected)
        self.assertEqual(raw, original)
        self.assertEqual(actual['sensitivity']['details'], [])
        self.assertEqual(actual['sensitivity']['details_omitted'], 0)  # alpha .1 is stable here

    def test_detail_cap_changes_no_band_result(self):
        a = app.review(app.influence.demo_csv(), '4/5', '1/10', max_details=0)
        b = app.review(app.influence.demo_csv(), '4/5', '1/10', max_details=1)
        self.assertEqual(a['candidates'], b['candidates'])
        self.assertEqual(a['sensitivity']['details_omitted'], 7)
        self.assertEqual(b['sensitivity']['details_omitted'], 6)
        self.assertEqual(a['sensitivity']['complete_diagnostics_sha256'], b['sensitivity']['complete_diagnostics_sha256'])

    def test_invalid_dimension_policy_and_csv_fail(self):
        raw = app.influence.demo_csv()
        for args in [('1 s', '0', '0'), ('0', '-1', '0'), ('0', '0', '-1'),
                     ('0', '1 m', '0'), ('0', '0', '1 m'), ('0', '1/0', '0')]:
            with self.subTest(args=args), self.assertRaises((ValueError, app.tolerance.UnitError)):
                app.review(raw, *args)
        with self.assertRaises(ValueError):
            app.review(b'broken', '0')

    def test_provenance(self):
        root = HERE.parents[1]
        for row in json.loads((HERE/'provenance.json').read_text()):
            original, snapshot = root/row['source'], root/row['snapshot']
            self.assertEqual(original.read_bytes(), snapshot.read_bytes())
            self.assertEqual(hashlib.sha256(snapshot.read_bytes()).hexdigest(), row['sha256'])

    def test_copied_cli_pin_errors_and_outside_workspace(self):
        scratch = Path('test/scratch'); scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temporary:
            root = Path(temporary).resolve()
            shutil.copytree(HERE, root/'effect-band', ignore=shutil.ignore_patterns('__pycache__'))
            raw = app.influence.demo_csv(); (root/'data.csv').write_bytes(raw)
            command = [sys.executable, '-B', 'effect-band/effect_band.py']
            demo = subprocess.run(command+['demo'], cwd=root, capture_output=True)
            self.assertEqual(demo.returncode, 0, demo.stderr)
            args = ['review', '--input', 'data.csv', '--reference', '4/5', '--absolute', '1/10',
                    '--expect-sha256', hashlib.sha256(raw).hexdigest()]
            good = subprocess.run(command+args, cwd=root, capture_output=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            result = json.loads(good.stdout)
            self.assertFalse(result['candidates'][0]['all_single_deletion_effects_within_band'])
            self.assertTrue(all(c in (10, 13) or 32 <= c <= 126 for c in good.stdout))
            for extra in [['--expect-sha256', hashlib.sha256(b'different').hexdigest()],
                          ['--expect-sha256', 'invalid'], ['--absolute', '-1'],
                          ['--reference', '1 m'], ['--max-details', '201'],
                          ['--input', str(HERE/'README.md')]]:
                bad = subprocess.run(command+args+extra, cwd=root, capture_output=True)
                self.assertEqual(bad.returncode, 2, bad.stderr)
                self.assertEqual(bad.stdout, b'')
                self.assertTrue(bad.stderr)

    def test_inert_unicode_labels(self):
        raw = csv_bytes([(0, 1, 0), (1, 0, 1)]).replace(b'first', '\u03b1'.encode())
        result = app.review(raw, '0', '1')
        output = json.dumps(result, ensure_ascii=True)
        self.assertTrue(output.isascii())
        self.assertEqual(json.loads(output)['candidates'][0]['candidate'], '\u03b1')


if __name__ == '__main__':
    unittest.main()
