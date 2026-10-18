import csv
from fractions import Fraction
import hashlib
import io
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

import case_influence as ci


def encoded(rows, ids=None):
    out = io.StringIO(newline='')
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(['case', 'baseline'] + ['c' + str(i) for i in range(len(rows[0])-1)])
    writer.writerows([[ids[i] if ids else 'case-' + str(i), *row] for i, row in enumerate(rows)])
    return out.getvalue().encode()


class Tests(unittest.TestCase):
    def test_known_holm_boundary(self):
        report = ci.review(ci.demo_csv())
        self.assertEqual(report['deletions_checked'], 8)
        self.assertEqual(report['cases_changing_decision_or_direction'], 7)
        self.assertTrue(all(c['familywise_reject_equal_discordance']
                            for c in report['full_data_analysis']['candidates']))
        self.assertEqual([s['decision_changes'] for s in report['candidates']], [7, 7])
        self.assertTrue(all(not c['reject_equal_discordance'] for d in report['details'] for c in d['changes']))

    def check_oracle(self, rows, alpha='0.05'):
        raw = encoded(rows)
        result = ci.review(raw, alpha, 200)
        base = result['full_data_analysis']['candidates']
        expected = []
        effects = [[] for _ in base]
        count_changes = [[0, 0] for _ in base]
        digest = hashlib.sha256()
        for i in range(len(rows)):
            reduced = encoded(rows[:i] + rows[i+1:])
            names, pairs = ci.engine.read_csv_bytes(reduced)
            analysis = ci.engine.analyze(reduced, names, pairs, ci.engine.parse_alpha(alpha))
            changes, fractions = [], []
            for k, (old, new) in enumerate(zip(base, analysis['candidates'])):
                dw = new['candidate_only_pass'] - new['baseline_only_pass']
                effect = Fraction(dw, len(rows)-1)
                effects[k].append(effect)
                fractions.append(ci.fraction(effect))
                dc = new['familywise_reject_equal_discordance'] != old['familywise_reject_equal_discordance']
                direction = {'candidate': 1, 'baseline': -1, 'tie': 0}[new['observed_direction']]
                oc = new['observed_direction'] != old['observed_direction']
                count_changes[k][0] += dc
                count_changes[k][1] += oc
                if dc or oc:
                    changes.append({'name': new['name'], 'reject_equal_discordance': new['familywise_reject_equal_discordance'],
                                    'direction': direction, 'decision_changed': dc, 'direction_changed': oc})
            item = {'removed_case': 'case-' + str(i), 'changes': changes, 'effects': fractions}
            digest.update(ci.canonical(item) + b'\n')
            if changes:
                expected.append(item)
        self.assertEqual(result['details'], expected)
        self.assertEqual(result['complete_diagnostics_sha256'], digest.hexdigest())
        for k, summary in enumerate(result['candidates']):
            self.assertEqual(summary['decision_changes'], count_changes[k][0])
            self.assertEqual(summary['direction_changes'], count_changes[k][1])
            self.assertEqual(summary['minimum_effect'], ci.fraction(min(effects[k])))
            self.assertEqual(summary['maximum_effect'], ci.fraction(max(effects[k])))

    def test_every_two_case_pattern(self):
        patterns = list(itertools.product((0, 1), repeat=3))
        for a, b in itertools.product(patterns, repeat=2):
            self.check_oracle([a, b])

    def test_seeded_full_engine_oracle(self):
        rng = random.Random(2801)
        for _ in range(30):
            columns = rng.randint(3, 8)
            rows = [tuple(rng.randrange(2) for _ in range(columns)) for _ in range(rng.randint(3, 35))]
            self.check_oracle(rows, rng.choice(['0.000001', '0.05', '0.2']))

    def test_truncation_is_explicit_and_digest_unchanged(self):
        full = ci.review(ci.demo_csv(), max_details=200)
        for limit in (0, 1, 3):
            limited = ci.review(ci.demo_csv(), max_details=limit)
            self.assertEqual(len(limited['details']), limit)
            self.assertEqual(limited['details_omitted'], 7-limit)
            self.assertEqual(limited['complete_diagnostics_sha256'], full['complete_diagnostics_sha256'])

    def test_bom_crlf_and_quoted_unicode_ids(self):
        raw = encoded([(0, 1, 1), (1, 0, 0)], ['comma,quoted', 'frog-\U0001f438'])
        raw = b'\xef\xbb\xbf' + raw.replace(b'\n', b'\r\n')
        result = ci.review(raw)
        self.assertEqual([d['removed_case'] for d in result['details']], ['comma,quoted', 'frog-\U0001f438'])
        self.assertEqual(result['input_sha256'], hashlib.sha256(raw).hexdigest())

    def test_invalid_csv_and_limits(self):
        for raw in (b'', b'case,baseline,c1,c2\na,0,1,1\n',
                    b'case,baseline,c1,c2\na,0,1,1\na,0,1,1\n',
                    b'case,baseline,c1,c2\na,0,1,2\nb,1,1,1\n',
                    b'case,baseline,c1\na,0,1\nb,1,1\n',
                    encoded([(0,1,1)]*2001)):
            with self.assertRaises(ValueError):
                ci.review(raw)
        for value in (-1, 201, True, 1.5):
            with self.assertRaises(ValueError):
                ci.review(ci.demo_csv(), max_details=value)

    def test_alpha_validation(self):
        for alpha in ('NaN', '0', '0.21', 'no', '1e999'):
            with self.assertRaises(ValueError):
                ci.review(ci.demo_csv(), alpha)

    def test_all_agreement_stability(self):
        result = ci.review(encoded([(1,1,1), (0,0,0), (1,1,1)]))
        self.assertEqual(result['cases_changing_decision_or_direction'], 0)
        self.assertEqual(result['details_omitted'], 0)
        self.assertTrue(all(s['minimum_effect'] == ci.fraction(Fraction(0)) for s in result['candidates']))

    def test_reordering_changes_byte_pin_not_summary(self):
        rows = [(0,1,1)]*7 + [(1,1,1)]
        a, b = ci.review(encoded(rows)), ci.review(encoded(list(reversed(rows))))
        self.assertNotEqual(a['input_sha256'], b['input_sha256'])
        self.assertEqual(a['candidates'], b['candidates'])

    def test_cli_and_inert_output(self):
        script = str(Path(__file__).with_name('case_influence.py'))
        good = subprocess.run([sys.executable, '-B', script, '--demo', '--max-details', '1'],
                              capture_output=True, check=False)
        self.assertEqual(good.returncode, 0)
        self.assertEqual(json.loads(good.stdout)['details_omitted'], 6)
        for options in (['--alpha', 'NaN'], ['--max-details', '-1']):
            bad = subprocess.run([sys.executable, '-B', script, '--demo', *options], capture_output=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, b'')

    def test_snapshot_pin(self):
        folder = Path(__file__).parent
        provenance = json.loads((folder/'provenance.json').read_text())
        actual = hashlib.sha256((folder/'ladder_engine.py').read_bytes()).hexdigest()
        self.assertEqual(provenance['sha256'], actual)


if __name__ == '__main__':
    unittest.main()
