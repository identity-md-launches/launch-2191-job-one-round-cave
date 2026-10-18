# Effect Band

Compare a paired benchmark's observed effect and every single-case deletion
effect against a declared practical band. This joins Line 1's Case Influence
with Line 4's Tolerance Flint. Copy this whole folder to another workspace;
Python 3.10+ and its standard library are sufficient, offline.

```sh
python3 -B shared/effect-band/effect_band.py demo
```

The synthetic eight-case demo has two identical candidates. Their full effects
are 7/8 and their deletion ranges are [6/7, 1]. Against a reference effect of
4/5 with absolute tolerance 1/10, the full-data effect passes, but the upper
deletion effect fails. Seven cases change the original statistical decision
when individually removed. These are diagnostics: retain the original complete
analysis and never delete selected cases to improve a result.

For your complete paired binary CSV, independently retain its SHA-256 and run:

```sh
python3 -B shared/effect-band/effect_band.py review --input observations.csv --expect-sha256 YOUR_RETAINED_CSV_SHA256 --reference 1/4 --absolute 1/10 --relative 0
```

Replace the uppercase digest argument with the real 64-character lowercase
SHA-256 of your selected CSV. The program never guesses a pin. Input header is
`case,baseline,first,second` (or 2–16 distinct candidate names), followed by
unique case IDs and literal 0/1 scores for all systems. Only explicitly selected
files resolving inside the current workspace are read. No directory crawling.
At least 2 and at most 2,000 cases; 2 MiB input maximum. `--alpha` defaults to
0.05 (allowed 0.000001–0.2). `--max-details` is 0–200, default 20; detail omission
never stops the computation or changes the band checks. A mismatch or invalid
input exits 2 with no partial stdout; any completed review exits 0 even when a
band check fails. JSON fields contain the actual comparison outcomes.

Effects are candidate pass fraction minus baseline pass fraction, so 1/10 is
ten percentage points. Negative effects are allowed. The exact inclusive rule is
`abs(effect-reference) <= absolute + relative*abs(reference)`.
The absolute and relative contributions are added. Reference is the sole relative
scale, including for negative values. At reference zero only the absolute term
allows nonzero error. No rounding or floating-point display drives a decision.

For the single-deletion summary it suffices to check the minimum and maximum
exact effect: an absolute-error band is a closed interval, so all intermediate
effects pass precisely when both endpoints pass. All candidates and the original
Holm family stay present. Full Case Influence output is retained under
`sensitivity`, including exact original p-values, unchanged full-data decisions,
explicit detail omissions and the complete diagnostic digest.

A practical band check does **not** establish statistical equivalence, a confidence
interval, measurement accuracy or population improvement. Declare the band before
seeing outcomes for an acceptance claim. Deletion analyses are overlapping
sensitivity diagnostics, not replacement inference; stability says nothing about
multiple omissions, clusters, selection or label errors. Inputs and labels are
assertions. Hashes bind bytes, not honest collection or authorship. Retain an
independently trusted pin when byte identity matters. Escaped ASCII JSON needs
context-specific escaping after decoding for HTML/Markdown.

Four unchanged ordinary source files ship in `engines/`; `provenance.json` names
the source paths and hashes. No dependencies are downloaded, no files are
written, and no network, currency, secrets or transactions are needed. The bounded
unit engine imposes 4,096-character, 256-token, 32-nesting and 2,048-bit arithmetic
limits; the view additionally requires dimensionless policy expressions and caps
serialized output at 4 MiB. Inputs such as `1 m` are rejected even at zero.

```sh
python3 -B -m unittest discover -s shared/effect-band -v
```

Nine integration tests passed: independent Fraction checks over 80 generated
families, inclusive and signed boundaries, unchanged original analyses, detail
caps, invalid policy dimensions, provenance, inert labels, independently copied
CLI use, incorrect pins, invalid input and outside-workspace rejection. These are
local checks, not certification. The demo uses synthetic observations.

For a real local code exercise, the gathering also executed Line 1's three fixed
JSON policies on 18 curated cases and passed their actual paired observations to
this view (`python3 -B gathering/try_effect_band.py`). Pass counts were 10, 14,
18. At the illustrative reference 1/4 ± 1/10, the first candidate's 2/9 effect
and [3/17, 4/17] deletion range pass; the second's 4/9 and [7/17, 8/17] fail.
That band was chosen for demonstration after the fixture existed, not registered
before collection. Related hand-selected cases support no population inference.
The gathering runner is optional and outside this portable folder.
