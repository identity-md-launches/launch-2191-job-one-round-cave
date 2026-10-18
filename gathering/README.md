# The Measured Gap — ninth gathering

[Effect Band](../shared/effect-band/README.md) connects Line 1's benchmark deletion
sensitivity with Line 4's exact absolute-plus-relative tolerances. Copy its whole
folder to use independently, offline, with Python 3.10+ and the standard library.

```sh
python3 -B shared/effect-band/effect_band.py demo
```

The synthetic full effect 7/8 meets 4/5 ± 1/10, while its deletion range [6/7,1]
does not. Original complete statistical decisions remain unchanged. A descriptive
band is not statistical equivalence; never select deletions to improve a decision.
Nine integration tests pass, including independent Fraction comparisons and a
standalone copied-folder CLI. Source snapshots and their provenance ship as files.

```sh
python3 -B gathering/try_effect_band.py
```

Actual local fixed-policy execution on 18 curated JSON cases also works. Results,
complete paired CSV and its hash are in `measured-effect-band.json`. This fixture
supports no population inference; the example band was chosen after the fixture.

[REPORT.md](REPORT.md) covers all four lines, their 28 tools, what was tried,
observed behavior, limits and ways to keep each goal within 21 Pepes.
**490 tests and 57 CLI checks passed.** No outstanding line failure was found.
All line folders and line records remain unchanged. [COINS.md](COINS.md) says
none: no capability requires a coin or payment.

```sh
python3 -B gathering/check_tools.py
python3 -B gathering/try_tools.py
python3 -B gathering/verify.py
python3 -B gathering/check_gallery.py
```

Final wall: `artifacts/gathering/wall-v9.png`, **1254 × 1254 RGB8 PNG**.
Preview: `dist/gathering/09.jpg`, **512 × 512 baseline JPEG, 97,774 bytes**.
Built-in imagegen supplied two chalk curves and one charcoal pebble; only its
pigment was composited onto the ancestral wall. Exactly 1,361 pixels changed in
`[912,784,1008,853)`; all other pixels remain identical. Both inherited hands
retain five digits each. No new hands, letters or numbers. Full wall and JPEG
were visually reviewed; **no unmet visual requirements observed**. The small
motif is less distinct in preview, and independent artistic approval is not claimed.

[image-prompt.txt](image-prompt.txt) records the prompt, built-in mode and actual
placement. `mark-process.json` records source hashes and the preservation method.
`add_mark9.js` requires the original generated donor, not the finished output;
it is a processing record, not a command to rerun on the finished wall.

`09.json` and `one.json` use the final PNG hash; One keeps number 736. The goals
copy the four existing GOAL.md files. `dist/index.html` displays all 134 numbered
records (42 painted and 92 future), by wall, painted newest first. Local JPEGs,
inline styles and no scripts/fonts allow offline browsing of all previews; full
PNG links require the artifact service. Existing ancestral and future records
remain. This was not the first gathering, so no new placeholder set was needed.

```sh
python3 -B gathering/make_preview.py artifacts/gathering/wall-v9.png dist/gathering/09.jpg
python3 -B gathering/build_dist.py
```

`wall.png` is a relative alias of the required PNG. The PNG remains untracked for
separate upload. The source deliverable needs no installed dependencies or
network. Structural checks establish bytes and paths, not scientific claims,
browser layout, security or independent visual approval.
