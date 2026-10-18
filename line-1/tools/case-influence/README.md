# Case Influence

Find benchmark cases whose individual removal changes an exact Holm-adjusted
decision or the observed direction of a candidate's paired binary improvement.
This helps a worker spot a conclusion resting on one observation. The original
full-data analysis remains in the report, and every deletion retains the whole
candidate family and the same alpha.

Python standard library only; no installation, network or sibling tool needed.
Copy this entire folder to use it elsewhere. From the workspace root:

```sh
python3 -B line-1/tools/case-influence/case_influence.py --demo
```

When tried, the explicitly synthetic eight-case example rejected equal
discordance for both candidates on all observations: exact Holm-adjusted
p = 1/32. Removing any of seven winning cases gave adjusted p = 1/16 and
changed both decisions at alpha 0.05. Removing the agreement changed neither
decision. All eight exclusions were checked; seven were reported influential.
These are synthetic diagnostic checks, not measured improvements of real systems.

## Your own observations

Use the same complete paired CSV as Candidate Ladder: `case,baseline` followed
by **two through sixteen** distinct candidate names. Each remaining row has a
unique case ID and literal `0`/`1` scores for every system. At least two and at
most 2,000 cases, at most 2 MiB. Quoted identifiers, UTF-8 BOM and CRLF work;
blank records, control-bearing IDs, duplicates and incomplete rows fail.

```sh
python3 -B line-1/tools/case-influence/case_influence.py --input observations.csv --alpha 0.05 --max-details 20
```

Only explicitly requested files resolving inside the current workspace are
read. The program writes nothing. JSON goes to stdout, with labels escaped to
ASCII. Exit 0 means a completed review, regardless of stability; invalid input
exits 2 with stderr and no partial JSON. Use a new filename if redirecting stdout.
JSON escaping is not a guarantee of safe HTML after decoding.

Each candidate summary counts decision changes and direction changes separately
and gives the exact minimum/maximum **pass-fraction difference** across all
single deletions. Multiply by 100 for percentage points. Direction `-1`, `0`,
`1` means baseline, tie, candidate. Effects and exact p-values use integer
fractions; decision thresholds never use rounded displays. Identical complete
outcome patterns share computation, but every case is counted separately.

Details list the first influential cases in original input order, capped at
`--max-details` (0 through 200). `details_omitted` explicitly counts the remaining
influential cases. All cases still contribute to summaries and the diagnostic
digest. `complete_diagnostics_sha256` hashes one canonical ASCII JSON object per
removed case (including unaffected cases), each followed by LF. Each object has
`removed_case`, `changes` and candidate-order `effects`; keys are sorted and
separators are `,` and `:`. This digest is independent of the detail cap. It
binds a computation, not an honest or independently executed experiment.

## How to interpret it

Deletion p-values are **sensitivity diagnostics**, not additional corrected
inferential claims. Do not discard inconvenient cases or promote a deletion's
decision to replace the prespecified full-data analysis. These are repeated,
overlapping subsets; no inference across deletions is claimed. An unchanged
decision does not establish robustness to multiple omissions, clusters, label
errors, case selection or repeated looks. Representative independent cases,
honest outcomes and prespecification remain the worker's responsibility.
Non-rejection does not establish equivalence. The tool does not need currency,
prices, wallets or transactions.

`ladder_engine.py` is an unchanged ordinary-file snapshot of Candidate Ladder;
`provenance.json` records its source and SHA-256. This program uses its validated
CSV parser, full-data analysis and exact McNemar probabilities. The small deletion
rule retains the same whole-family Holm adjustment. The engine is shipped as
source rather than downloaded at runtime.

## Checks performed

```sh
python3 -B -m unittest discover -s line-1/tools/case-influence -v
```

Eleven tests passed, including every two-case pattern for two candidates and
30 seeded families compared against fresh Candidate Ladder analyses of each
reduced CSV. They also cover the known boundary, agreement stability, exact
effect ranges, full diagnostic hash, explicit truncation, CSV/alpha/budget
rejection, quoted Unicode IDs, source provenance and CLI failure behavior.
These local checks are not independent certification.
