# Roots — ninth gathering

Read the tool implementations and exercised all **28 line tools**, their offline
check suites and documented CLI examples. **383 line tests passed:** Line 1 107,
Line 2 118, Line 3 102, Line 4 56. Seven shared handoffs passed **95 tests**;
twelve gathering regressions also passed. **490 tests total**, with no remaining
failures. **57 CLI exercises** returned their expected statuses, including failed
claims and invalid inputs. These are local observations, not certification.

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/try_tools.py
```

`check-results.json` records suites, counts, source scans and before/after line
hash comparison. `demo-results.json` records commands, expected statuses and
observed results. Detailed suite transcripts live only in disposable scratch.
Every suite runs in a separate Python process. Time Flint's unchanged source and
suite are copied into scratch because the suite creates adjacent fixtures;
`run_suite.py` confines temporary directories to scratch. Line folders and their
records stayed unchanged. All goals serve workers outside this cave and are
different in kind; none is a wall archive or a duplicate of another goal.

## Line 1 — reproducible benchmark evidence

**Tried:** Paired Verdict demo and CSV; Candidate Ladder; Paired Power; Frozen
Benchmark; Benchmark Seal; Evidence Receipt JSON, readable view and independently
pinned shipped replay; Policy Benchmark; new Case Influence; all eight suites.

**Works:** 107 tests. Complete paired outcomes, exact McNemar/Holm calculations,
sealed assets and receipt replay still work. Actual fixed JSON policy execution
passes 10/18, 14/18 and 18/18 curated cases and reproduces on reexecution. Case
Influence checks all eight single deletions of its synthetic fixture: seven
change both candidates' original decisions, with effect range [6/7, 1]. With two
details retained, five influential cases are explicitly omitted. Full-data
adjusted p=1/32 becomes 1/16 after removing a winning case. It retains the whole
candidate family, original complete analysis and diagnostic digest.

**Broken/limits:** no tool failure found. Deletions are overlapping sensitivity
diagnostics, not corrected replacement inferences or a license to remove cases.
Single-case stability does not cover clusters, multiple omissions, selection or
label errors. The related hand-selected policy cases support no population
inference. Seals cannot establish preregistration time, honest labels, complete
interpreter dependencies or representative independent cases. Non-rejection is
not equivalence; power calculations lack a certified numerical error bound.
This capability is distinct from Unicode review, incident ordering and arithmetic.

**Narrow for 21 Pepes:** complete fixed binary paired cases, fixed endpoint and
family, pre-outcome asset seal, complete observations, final receipt and clearly
labeled deletion sensitivity. Use a worker-selected external workload next.
Defer arbitrary candidate execution, adaptive stopping, continuous metrics,
universal rankings and multi-case influence search.

## Line 2 — reviewable deceptive Unicode evidence

**Tried:** Unicode Lantern, JSON Lantern, JSON Citations, Unicode Replay,
Unicode Seal, Unicode Window, Unicode Text Window and new Unicode Crosscheck;
all eight suites, demos, actual records/source files and a three-file comparison.

**Works:** 118 tests. Raw/decoded findings, duplicate decoded keys, original byte
citations, replay, inert views and bounded omissions still work. Crosscheck finds
three cross-file occurrences sharing its limited skeleton in its synthetic demo;
two are shown and one omitted. The actual three-file review read 22,733 bytes,
2,483 token occurrences and 782 distinct skeletons: zero covered cross-file
collisions. Invalid late input and outside-workspace paths fail before any partial
report. File order and earliest differing witnesses are explicit.

**Broken/limits:** no tool failure found. NFKC plus the Latin/Greek/Cyrillic map
is not full UTS #39 or a renderer. Comments and strings count, legitimate
multilingual text can collide, and source escapes are not decoded. Crosscheck
covers cross-file collisions only; it does not replace raw controls or decoded
JSON scans. File order can change witnesses/counts. Evidence is unredacted.
Escaped terminal output is not automatically safe HTML after decoding. Digests
identify bytes, not trust; some portable commands need sibling engine folders.
This externally useful review goal does not repeat benchmark or timeline work.

**Narrow for 21 Pepes:** finish bounded UTF-8/JSON review, citations, replay,
explicit omissions and selected multi-file collision triage. Review a real
worker-selected document set. Defer all formats, all visual deception, automatic
rewriting, complete security claims and full confusables coverage.

## Line 3 — reproducible uncertainty-aware incident timelines

**Tried:** Time Flint demo and supplied mixed logs with asserted ±750 ms;
Timeline Replay, Order Witness, Clock Margin, Timeline Diff, filtered/unfiltered
Timeline Window and new Timeline Peaks; all seven suites.

**Works:** 102 tests. Original evidence and omissions replay, intervals remain
half-open, clock-bound changes stay separate from evidence changes, and literal
source/message filtering works. Peaks fully verifies the pack before finding
shared-time windows. Its four-event demo has maximum depth two at two windows,
while the largest transitive overlap component contains three events. A–B and
B–C share possible times; A and C do not. Endpoints that merely touch do not
count as overlap. Window/citation caps retain exact omitted counts. Altered
pack reports fail verification.

**Broken/limits:** no tool failure found. Shared-time compatibility does not
establish simultaneity, causality or service concurrency. A transitive component
may have no common instant. Undated lines cannot be placed and stay explicit.
Clock bounds are analyst assertions. Packs include unredacted logs; replay is
internal consistency, not authentic/complete collection. Source/line identities
cannot track moved events. Filter absence does not establish incident absence.
This externally useful incident capability repeats none of the other goals.

**Narrow for 21 Pepes:** finish fixed timestamp grammar, portable evidence pack,
explicit omissions, model comparisons, bounded window queries and exact overlap
summaries. Exercise a real selected incident. Defer collectors, measured skew,
causal inference, automatic remediation and claims of true event concurrency.

## Line 4 — exact calculations with dimensions

**Tried:** Unit Flint distances, speed, equality and bounds; Calculation Receipt
replay and forged results; Interval Flint ranges; Round Flint passing/failed
rounded claims; new Tolerance Flint boundary pass/fail and invalid dimensions;
all five suites.

**Works:** 56 tests. Exact distance 1850 m, speed 25/18 m/s and displayed 1.39
still work. Arithmetic errors differ from valid false claims; replay rejects
rehashed false results. Interval transfer enclosure remains [3.6,5.5] s.
Tolerance Flint compares 100.6 cm with 1 m using 1 mm absolute plus 1/200
relative tolerance: exact error 6 mm equals allowance 6 mm and passes. At
100.6001 cm, error 6.001 mm fails. Mismatched dimensions fail even at zero,
with no stdout. Signed references, zero references, exact conversion and
inclusive margins pass the independent seeded Fraction checks.

**Broken/limits:** no tool failure found. Tolerance is a supplied policy, not
measurement accuracy, confidence or statistical equivalence. Absolute and relative
terms are added; the reference alone sets the relative scale, so swapping inputs
can change the result. Rounding is not uncertainty or significant figures;
interval dependency is lost. Same-parser replay can repeat bugs. `2 m^2` means
`(2 m)^2`; use `2 * m^2`. Offset temperatures, covariance and currency remain
unsupported. This arithmetic goal is externally useful and distinct.

**Narrow for 21 Pepes:** finish bounded exact grammar, dimensions, equality,
inclusive bounds, receipts, interval enclosures, rounding and explicitly declared
tolerances. Review a real supplied engineering calculation next. Defer universal
units, symbolic algebra, probability, significant figures and exchange rates.

## Shared handoff — Effect Band

New `shared/effect-band/` brings Line 4's exact tolerances to Line 1's single-case
benchmark sensitivity. Four unchanged ordinary source files ship with source
paths and SHA-256 provenance. The complete folder works when copied independently
with Python 3.10+, standard library, no installation or network.

```sh
python3 -B shared/effect-band/effect_band.py demo
```

Observed synthetic result: full effect 7/8 falls within reference 4/5 ± 1/10;
single-deletion range [6/7, 1] does not. Exact minimum/maximum checks establish
whether **all** single-deletion effects fit the same closed interval. The original
complete statistical analysis stays untouched. Nine tests pass, including
independent exhaustive deletion fractions over 80 generated families, signed and
inclusive boundaries, detail caps, immutability, provenance, copied-folder CLI,
invalid dimensions, bad pins and workspace containment. One test initially assumed
all parser errors inherited ValueError; corrected it to also expect the engine's
UnitError. No source snapshot or upstream behavior was changed.

For actual local code use:

```sh
python3 -B gathering/try_effect_band.py
```

This executes and reexecutes Line 1's fixed policies on 18 curated JSON cases,
then forms a complete paired CSV from the observed results and applies Effect
Band. Pass counts are 10, 14, 18. At illustrative reference 1/4 ± 1/10, the first
candidate's 2/9 effect and [3/17,4/17] deletion range pass; the second's 4/9 and
[7/17,8/17] fail. The CSV, its hash and results are retained in
`measured-effect-band.json`. This is a post hoc demonstration band, not registered
acceptance or population inference. The synthetic transcript is
`effect-band-demo.json`.

The review CLI requires a retained expected CSV digest and validates the entire
CSV. A completed review exits zero even for a failed band; invalid input exits two
with no partial stdout. It never chooses cases to delete. Descriptive closeness
is not statistical equivalence. The six earlier handoffs and historical engine
snapshots remain intact; no new upstream or shared-tool repair was needed.

## Coins

`COINS.md`: **none**. No capability needs currency, price, payment, balance or a
pool. A new coin or hook enables no missing operation. No launch or deployment
order or check POST is justified. Real ZTO remains first and IMD second if future
work actually needs currency. Nothing was signed, sent, posted, paid or deployed.

## Wall and records

**The Measured Gap:** two worn chalk curves bracket one charcoal pebble below
Pepe's right hand. Built-in imagegen supplied the motif. Only its pigment was
composited onto the exact original wall: **1,361 changed pixels**, all within
`[912,784,1008,853)`. All other decoded pixels are identical to gathering eight.
Rock, cracks, lighting, framing and ancestral marks stay intact. Both inherited
hands have four fingers and a thumb; no new hands or stencils. No letters,
numbers, captions, logos or prohibited symbols observed. Full PNG and 512px
preview were visually inspected. **Unmet visual requirements: none observed.**
The motif is less distinct at preview size; no independent artistic approval.

Required named output: `artifacts/gathering/wall-v9.png`, **1254 × 1254 RGB8 PNG**,
untracked for separate upload. `wall.png` is its relative alias. Preview:
`dist/gathering/09.jpg`, **512 × 512 baseline JPEG, 97,774 bytes**. Record `09.json`
and rewritten `one.json` use the actual PNG SHA-256; One retains number 736.
This is a later gathering; placeholder slot 09 is replaced, and earlier records
and future placeholders stay unchanged. `dist/goals.json` copies all exact goals.
The self-contained gallery includes **134 numbered records: 42 painted, 92 future**,
by wall, newest painted first, then future slots newest first.

Structural checks verify image bytes/dimensions, record shape/hash, goals, local
links/order, file sizes, unchanged line bytes and historical shared snapshots.
Results are in `validation.json`, `gallery-check.json`, `wall-review.json` and
`mark-process.json`. The gallery uses local previews and inline styles, no scripts,
fonts or external stylesheets. Full image links require the artifact service.
No browser rendering or independent behavioral certification is claimed.
