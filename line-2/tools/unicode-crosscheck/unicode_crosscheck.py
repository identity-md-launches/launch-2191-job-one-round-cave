#!/usr/bin/env python3
"""Compare explicitly selected UTF-8 documents for cross-file lookalike identifiers."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unicodedata

ENGINE = Path(__file__).resolve().parents[1] / 'unicode-lantern' / 'unicode_lantern.py'
spec = importlib.util.spec_from_file_location('crosscheck_lantern', ENGINE)
lantern = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lantern)

MAX_FILES = 32
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_TOKENS = 200000
MAX_SKELETONS = 50000
MAX_TOKEN_CHARS = 4096
MAX_OUTPUT = 4 * 1024 * 1024
PREVIEW_BYTES = 64


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def tokens(text):
    """Match Lantern's Python-like token boundaries; never decode source escapes."""
    chars = []
    offset, line, column = 0, 1, 1
    start = None
    for char in text:
        if chars and not ('a' + char).isidentifier():
            yield ''.join(chars), start, offset
            chars = []
        if chars:
            chars.append(char)
        elif char == '_' or char.isidentifier():
            chars = [char]
            start = (offset, line, column)
        if len(chars) > MAX_TOKEN_CHARS:
            raise ValueError('identifier exceeds character budget')
        size = len(char.encode('utf-8'))
        offset += size
        if char == '\n':
            line, column = line + 1, 1
        else:
            column += size
    if chars:
        yield ''.join(chars), start, offset


def citation(raw, source_index, start, end):
    offset, line, column = start
    span = raw[offset:end]
    return dict(source_index=source_index, byte_start=offset, byte_end=end,
                line=line, byte_column=column, token_sha256=digest(span),
                preview_hex=span[:PREVIEW_BYTES].hex(),
                omitted_token_bytes=max(0, len(span) - PREVIEW_BYTES))


def review(documents, max_findings=100):
    """Documents are ordered (unique label, original bytes) pairs, never paths to open."""
    if type(documents) not in (list, tuple) or not 2 <= len(documents) <= MAX_FILES:
        raise ValueError('provide between 2 and 32 documents')
    if type(max_findings) is not int or not 1 <= max_findings <= 1000:
        raise ValueError('max_findings must be an integer between 1 and 1000')
    labels, total_bytes = set(), 0
    for document in documents:
        if type(document) not in (list, tuple) or len(document) != 2:
            raise ValueError('each document must be a label and bytes pair')
        label, raw = document
        if not isinstance(label, str) or not label or len(label) > 1024:
            raise ValueError('document label must contain 1 to 1024 characters')
        if label in labels:
            raise ValueError('document labels must be unique')
        labels.add(label)
        if not isinstance(raw, bytes) or len(raw) > lantern.MAX_BYTES:
            raise ValueError('document must be UTF-8 bytes within the 2 MiB budget')
        total_bytes += len(raw)
    if total_bytes > MAX_TOTAL_BYTES:
        raise ValueError('documents exceed total byte budget')

    prior, findings, sources = {}, [], []
    token_count, finding_count = 0, 0
    for index, (label, raw) in enumerate(documents):
        text = raw.decode('utf-8', errors='strict')
        sources.append(dict(index=index, label=lantern.escaped(label),
                            sha256=digest(raw), bytes=len(raw)))
        pending, new_skeletons = {}, 0
        for token, start, end in tokens(text):
            token_count += 1
            if token_count > MAX_TOKENS:
                raise ValueError('documents exceed token budget')
            skeleton = unicodedata.normalize('NFKC', token).translate(lantern.LOOKALIKES)
            earlier = prior.get(skeleton, [])
            witness = next((entry for entry in earlier if entry[0] != token), None)
            if witness is not None:
                finding_count += 1
                if len(findings) < max_findings:
                    findings.append(dict(rule='cross-file-lookalike-collision',
                                         skeleton_sha256=digest(skeleton.encode('utf-8')),
                                         earlier=witness[1],
                                         later=citation(raw, index, start, end)))
            # Two distinct spellings suffice to witness inequality with any later token.
            # Defer merging until EOF so a file can never collide with itself here.
            if skeleton not in prior and skeleton not in pending:
                if len(prior) + new_skeletons >= MAX_SKELETONS:
                    raise ValueError('documents exceed distinct skeleton budget')
                new_skeletons += 1
            candidates = pending.setdefault(skeleton, list(earlier))
            if len(candidates) < 2 and all(entry[0] != token for entry in candidates):
                candidates.append((token, citation(raw, index, start, end)))
        prior.update(pending)

    return dict(tool='unicode-crosscheck/1', unicode_version=unicodedata.unidata_version,
                engine_sha256=digest(ENGINE.read_bytes()), sources=sources,
                total_bytes=total_bytes, token_count=token_count,
                distinct_skeletons=len(prior), finding_count=finding_count,
                retained_findings=len(findings), omitted_findings=finding_count - len(findings),
                truncated=finding_count > len(findings), findings=findings,
                assessment='review-required' if finding_count else 'no-cross-file-collisions-found',
                limitations=[
                    'Heuristic triage, not proof of deception or absence of deception.',
                    'NFKC plus Lantern limited case-sensitive lookalikes, not full UTS #39.',
                    'Raw UTF-8 Python-like tokens, including comments and strings; no escape decoding.',
                    'Only cross-file collisions are covered; run Unicode Lantern for other patterns.',
                    'Each occurrence differing from a spelling in an earlier file counts once.',
                    'File order affects counts and witnesses; identical spellings do not collide.',
                    'Witness is the earliest distinct spelling in an earlier file, not all pairs.',
                    'Ranges are zero-based half-open original bytes; line/byte-column are one-based.',
                    'Only LF starts a line; preview_hex is at most 64 original bytes.',
                    'Source labels are unicode_escape encoded; evidence is not redacted.',
                    'Hashes identify bytes, not authenticity; only supplied files are assessed.'])


def render(report):
    result = json.dumps(report, ensure_ascii=True, allow_nan=False, indent=2) + '\n'
    if len(result) > MAX_OUTPUT:
        raise ValueError('report exceeds output budget; reduce max_findings')
    return result


def read_documents(values):
    if not 2 <= len(values) <= MAX_FILES:
        raise ValueError('provide between 2 and 32 files')
    paths, documents, total = set(), [], 0
    root = Path.cwd().resolve()
    for value in values:
        path = lantern.workspace_file(value)
        if path in paths:
            raise ValueError('the same resolved file was selected twice')
        paths.add(path)
        with path.open('rb') as handle:
            raw = handle.read(lantern.MAX_BYTES + 1)
        total += len(raw)
        if len(raw) > lantern.MAX_BYTES or total > MAX_TOTAL_BYTES:
            raise ValueError('selected files exceed byte budget')
        documents.append((str(path.relative_to(root)), raw))
    return documents


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--demo', action='store_true')
    group.add_argument('--files', nargs='+', metavar='PATH')
    parser.add_argument('--max-findings', type=int, default=100)
    args = parser.parse_args(argv)
    try:
        documents = [('synthetic/first.txt', b'owner = 1\n'),
                     ('synthetic/second.txt', '\u043ewner = 2\n\uff4fwner = 3\n'.encode('utf-8')),
                     ('synthetic/third.txt', b'owner = 4\n')] if args.demo else read_documents(args.files)
        report = review(documents, args.max_findings)
        sys.stdout.write(render(report))
        return 0 if args.demo or not report['finding_count'] else 1
    except (OSError, ValueError, OverflowError) as error:
        sys.stderr.write(json.dumps({'error': str(error)}, ensure_ascii=True) + '\n')
        return 2


if __name__ == '__main__':
    sys.exit(main())
