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
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('crosscheck', Path(__file__).with_name('unicode_crosscheck.py'))
cross = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cross)


def docs(*texts):
    return [(str(i), text.encode('utf-8')) for i, text in enumerate(texts)]


class CrosscheckTests(unittest.TestCase):
    def test_cross_file_only(self):
        self.assertEqual(cross.review(docs('owner \u043ewner', 'other'))['finding_count'], 0)
        self.assertEqual(cross.review(docs('owner', '\u043ewner'))['finding_count'], 1)

    def test_identical_spelling_not_collision(self):
        self.assertEqual(cross.review(docs('\u043ewner', '\u043ewner'))['finding_count'], 0)

    def test_second_witness_is_needed(self):
        result = cross.review(docs('owner', '\u043ewner', 'owner'))
        self.assertEqual(result['finding_count'], 2)
        self.assertEqual(result['findings'][1]['earlier']['source_index'], 1)

    def test_two_witnesses_in_same_prior_file(self):
        result = cross.review(docs('owner \u043ewner', 'owner'))
        self.assertEqual(result['finding_count'], 1)
        self.assertEqual(result['findings'][0]['earlier']['byte_start'], 6)

    def test_precise_multibyte_crlf_evidence(self):
        documents = docs('\u00e9; owner\r\n', '\u00e9;\r\n\t\u043ewner')
        result = cross.review(documents)
        item = result['findings'][0]
        self.assertEqual((item['earlier']['byte_start'], item['earlier']['byte_column']), (4, 5))
        self.assertEqual((item['later']['byte_start'], item['later']['line'], item['later']['byte_column']), (6, 2, 2))
        for citation in item['earlier'], item['later']:
            raw = documents[citation['source_index']][1]
            span = raw[citation['byte_start']:citation['byte_end']]
            self.assertEqual(span.hex(), citation['preview_hex'])
            self.assertEqual(hashlib.sha256(span).hexdigest(), citation['token_sha256'])

    def test_nfkc_and_combining(self):
        result = cross.review(docs('owner \u00e9', '\uff4fwner e\u0301'))
        self.assertEqual(result['finding_count'], 2)

    def test_case_sensitive_and_no_escape_decoding(self):
        self.assertEqual(cross.review(docs('owner', 'Owner \\u043ewner'))['finding_count'], 0)

    def test_omissions_count_occurrences(self):
        result = cross.review(docs('owner', '\u043ewner \u043ewner \uff4fwner'), 1)
        self.assertEqual((result['finding_count'], result['retained_findings'], result['omitted_findings']), (3, 1, 2))
        self.assertTrue(result['truncated'])

    def test_printable_output_and_labels(self):
        result = cross.review([('a\x1b[31m\u202e', b'owner'), ('b', '\u043ewner'.encode())])
        rendered = cross.render(result)
        self.assertTrue(all(c == '\n' or 32 <= ord(c) <= 126 for c in rendered))
        self.assertNotIn('\x1b', json.loads(rendered)['sources'][0]['label'])

    def test_long_preview(self):
        result = cross.review(docs('o' + 'a' * 100, '\u043e' + 'a' * 100))
        later = result['findings'][0]['later']
        self.assertEqual(len(bytes.fromhex(later['preview_hex'])), 64)
        self.assertEqual(later['omitted_token_bytes'], 38)

    def test_invalid_utf8_even_after_retention_full(self):
        with self.assertRaises(UnicodeError):
            cross.review([('a', b'owner'), ('b', '\u043ewner'.encode()), ('c', b'\xff')], 1)

    def test_invalid_arguments(self):
        for documents in [[], [('one', b'')], [('same', b''), ('same', b'')], [('a', ''), ('b', b'')]]:
            with self.subTest(documents=documents), self.assertRaises(ValueError):
                cross.review(documents)
        for retention in [True, 0, 1001, 1.0]:
            with self.subTest(retention=retention), self.assertRaises(ValueError):
                cross.review(docs('', ''), retention)

    def test_resource_limits(self):
        cases = [('MAX_TOTAL_BYTES', 3, docs('ab', 'cd')),
                 ('MAX_TOKENS', 2, docs('a b', 'c')),
                 ('MAX_SKELETONS', 2, docs('a b', 'c')),
                 ('MAX_TOKEN_CHARS', 2, docs('abc', ''))]
        for name, limit, documents in cases:
            with self.subTest(name=name), patch.object(cross, name, limit), self.assertRaises(ValueError):
                cross.review(documents)
        with patch.object(cross, 'MAX_OUTPUT', 10), self.assertRaises(ValueError):
            cross.render(cross.review(docs('', '')))

    def test_skeleton_budget_counts_unique_across_files(self):
        with patch.object(cross, 'MAX_SKELETONS', 2):
            self.assertEqual(cross.review(docs('a b', 'b a'))['distinct_skeletons'], 2)

    def test_generated_cases_against_all_previous_tokens(self):
        rng = random.Random(28)
        vocabulary = ['owner', '\u043ewner', '\uff4fwner', 'other', '\u03bfther', 'Owner', 'x', '\u0445']
        for trial in range(80):
            streams = [[rng.choice(vocabulary) for _ in range(rng.randrange(0, 15))] for _ in range(4)]
            documents = docs(*[' '.join(stream) for stream in streams])
            # Brute-force independent witness search, no compressed two-entry index.
            prior, expected = [], []
            for source_index, stream in enumerate(streams):
                byte_offset = 0
                current = []
                for token in stream:
                    skeleton = cross.unicodedata.normalize('NFKC', token).translate(cross.lantern.LOOKALIKES)
                    match = next((entry for entry in prior if entry[0] == skeleton and entry[1] != token), None)
                    if match:
                        expected.append((match[2], match[3], source_index, byte_offset))
                    current.append((skeleton, token, source_index, byte_offset))
                    byte_offset += len(token.encode()) + 1
                prior.extend(current)
            result = cross.review(documents, 1000)
            actual = [(f['earlier']['source_index'], f['earlier']['byte_start'],
                       f['later']['source_index'], f['later']['byte_start']) for f in result['findings']]
            self.assertEqual(actual, expected, trial)

    def test_cli_demo(self):
        result = subprocess.run([sys.executable, '-B', str(Path(cross.__file__)), '--demo', '--max-findings', '2'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['omitted_findings'], 1)

    def test_cli_actual_files_and_duplicate_selection(self):
        paths = [str(Path(cross.__file__)), str(cross.ENGINE)]
        command = [sys.executable, '-B', str(Path(cross.__file__)), '--files']
        result = subprocess.run(command + paths, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['finding_count'], 0)
        result = subprocess.run(command + paths[:1] * 2, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')

    def test_portable_cli_findings_and_fail_closed(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            root = Path(directory).resolve()
            for name in ('unicode-crosscheck', 'unicode-lantern'):
                source = Path(cross.__file__).resolve().parents[1] / name
                shutil.copytree(source, root / name, ignore=shutil.ignore_patterns('__pycache__'))
            (root / 'first.txt').write_bytes(b'owner')
            (root / 'second.txt').write_bytes('\u043ewner'.encode())
            (root / 'invalid.txt').write_bytes(b'\xff')
            command = [sys.executable, '-B', 'unicode-crosscheck/unicode_crosscheck.py', '--files']
            result = subprocess.run(command + ['first.txt', 'second.txt'], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)['finding_count'], 1)
            result = subprocess.run(command + ['first.txt', 'second.txt', 'invalid.txt'], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            # The symlink target exists in the outer workspace, but is outside this CLI's root.
            (root / 'outside.txt').symlink_to(Path(cross.__file__).resolve())
            result = subprocess.run(command + ['first.txt', 'outside.txt'], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertIn('inside the current workspace', result.stderr)


if __name__ == '__main__':
    unittest.main()
