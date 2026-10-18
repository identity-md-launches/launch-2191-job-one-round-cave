# Unicode Crosscheck

Find different identifiers in separate UTF-8 documents that share Unicode
Lantern's limited visual skeleton. A worker reviewing several source files can
now see collisions that scanning each file separately would miss. Each finding
links an earlier spelling to the later occurrence with exact original byte
ranges, byte columns, token hashes and bounded hexadecimal previews. Original
files are never rewritten.

Run this synthetic offline demonstration from the repository root:

```sh
python3 -B line-2/tools/unicode-crosscheck/unicode_crosscheck.py --demo --max-findings 2
```

It compares ASCII `owner`, a spelling starting with Cyrillic o, and one starting
with fullwidth o across three documents. Three occurrences collide across files;
two are retained and one is explicitly omitted. Demo success exits 0. The output
is printable ASCII JSON with inert source labels and hexadecimal evidence.

For real, explicitly selected, non-sensitive workspace files:

```sh
python3 -B line-2/tools/unicode-crosscheck/unicode_crosscheck.py --files line-1/tools/paired-verdict/paired_verdict.py line-2/tools/unicode-lantern/unicode_lantern.py line-2/tools/unicode-text-window/unicode_text_window.py
```

Actual-file mode exits 0 for no covered cross-file collisions, 1 for findings,
and 2 for invalid input or exceeded limits. Errors go to stderr with no partial
stdout report, even when a later file is invalid. All selected files are read
before results are printed. Files must resolve inside the current working
directory; duplicate resolved paths are rejected. There is no directory crawling,
network access, environment reading, signing, sending, wallet or key access.
Only select files you intend to expose: evidence is not redacted.

Python 3.9+ and standard library only. Copy this folder and its unchanged sibling
`unicode-lantern` together to another workspace. No installation or runtime
download is needed. `engine_sha256` identifies the sibling scanner source bytes,
including its mapping; it does not identify the whole runtime or authenticate
the report. `unicode_version` records the normalization database version.

## Counting and evidence contract

Files are processed in command-line order. Tokens follow Lantern's Python-like
identifier boundaries, including combining characters after an initial letter.
Each occurrence whose spelling differs from a token in an earlier file, but has
the same NFKC-plus-lookalike skeleton, counts once. The witness is the earliest
distinct spelling in an earlier file. Repetitions count as occurrences, not
unique pairs. An identical spelling alone is not a collision. Same-file-only
collisions are not reported by this tool. File order can change counts and
witnesses; preserve the ordered source list when comparing reports.

Ranges are zero-based half-open original UTF-8 byte offsets. Lines and byte
columns are one-based; only LF starts a line, including within CRLF. Each source
has its full SHA-256 and byte length. Each token citation has its full token
SHA-256, up to 64 bytes as `preview_hex`, and an explicit omitted-byte count.
Hex previews may end midway through UTF-8 characters. No source escape sequences
are decoded. `sources[].label` uses `unicode_escape`, so controls remain inert
even after JSON parsing. Unescaping these labels can reactivate controls.

The index keeps at most two distinct earlier spellings per skeleton: one of
them must differ from any later colliding token. It defers a file's index updates
until its end, so a token cannot witness its own file. Retention limits never
stop counting or input validation. This is a bounded report, not an all-pairs
listing or a portable replay bundle.

## Limits

- 2–32 files; 2 MiB per file and 8 MiB total UTF-8 bytes.
- 200,000 token occurrences; 50,000 distinct skeletons; 4,096 characters per token.
- 1–1,000 retained findings (default 100); 4 MiB serialized report.
- Labels contain 1–1,024 characters. All exceeded budgets fail with exit 2.

These are resource bounds, not a constant-memory guarantee. This case-sensitive
Latin/Greek/Cyrillic heuristic is not full UTS #39, a renderer, or a language
parser. Comments and strings count. Literal escaped JSON/source identifiers are
not decoded; use the line's JSON tools for decoded JSON. This tool does not scan
for bidi controls, invisible characters or same-file issues: use Unicode Lantern
or Unicode Text Window alongside it. Legitimate multilingual identifiers can
collide. No findings does not establish safety. Digests establish byte identity,
not authorship, collection integrity or trust. Concurrent file mutation and
hostile filesystem races are outside the contract; review an immutable workspace.

## What happened when tried

All 18 new tests passed, including 80 seeded brute-force witness comparisons,
NFKC and combining characters, exact multibyte/CRLF locations, limits, omissions,
invalid late input, CLI exit codes, outside-workspace symlink rejection and a
two-folder portable copy. The 100 unchanged ancestral tests also passed.

The real three-file command above reviewed 22,733 bytes and 2,483 token
occurrences across 782 skeletons, with zero covered cross-file collisions.
The source hashes and full result are in `line-2/round-28-real-review.json`.
These are local observations, not an independent security certification.

```sh
python3 -B -m unittest discover -s line-2/tools/unicode-crosscheck -v
```

The mark is two pale pebbles in separate ochre crescents joined by charcoal:
similar spellings in separate documents brought together for comparison.
