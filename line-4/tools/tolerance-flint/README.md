# Tolerance Flint

Compare an observed calculation with a reference using exact rational arithmetic
and explicit unit dimensions. This is useful when exact equality is too strict
but the permitted error must be declared and checked without floating point.

One command from the repository root shows it working:

```sh
python3 -B line-4/tools/tolerance-flint/tolerance_flint.py demo
```

Tried locally: `100.6 cm` compared with `1 m`, absolute tolerance `1 mm` and
relative tolerance `0.005`, passes exactly at the inclusive boundary. The error
is `6 mm`, the allowance is `1 + 5 = 6 mm`, and the margin is zero. `100.6001 cm`
fails with the same policy. The demo exits 0 only when both checks behave as
expected. These are hypothetical quantities, not externally verified measurements.

```sh
python3 -B line-4/tools/tolerance-flint/tolerance_flint.py check '100.6 cm' --reference '1 m' --absolute '1 mm' --relative '1/200' --to mm
```

The exact rule is:

```text
abs(observed - reference) <= absolute + relative * abs(reference)
```

The two error allowances are **added**. This deliberately differs from policies
that take their maximum. The relative scale is solely the reference magnitude:
swapping observed and reference can change the answer. Negative references use
their absolute magnitude. At a zero reference, relative tolerance contributes
zero; an absolute tolerance is needed to allow any nonzero error. No division by
the reference is performed. Tolerances must be nonnegative; no upper limit on
relative tolerance is imposed beyond the arithmetic budget. Supply `1/100` for
one percent; percent notation is not part of the grammar.

`--absolute` defaults to exact zero with reference dimensions; an explicit
absolute tolerance must have matching dimensions, even if zero. `--relative`
defaults to dimensionless zero. Observed and reference dimensions always have
to match, including zero. `--to` is an optional positive display scale of the
same dimensions; conversion happens after the decision. Every emitted numerical
value is an exact decimal or fraction string. `difference` is observed minus
reference; `margin` is allowance minus absolute error. Those fields and all
quantity fields use `unit`; `relative_tolerance` is dimensionless. `base_unit`
describes the dimensions. Output schema is `tolerance-flint/v1` and includes all
request strings, the explicit rule, the inclusive flag and boolean `passes`.

`check` exits 0 for a passing comparison, 1 for a valid comparison outside its
tolerance, and 2 for invalid input or resource limits. Invalid calculations emit
only stderr. For negative arguments use `--reference='-1 m'`, or place a negative
positional expression after `--` with the options before it:

```sh
python3 -B line-4/tools/tolerance-flint/tolerance_flint.py check --reference='-1 m' --relative 1/10 -- '-0.9 m'
```

Copy this entire folder for standalone offline use. Python 3.10+ and its standard
library are sufficient. `engine.py` is an unchanged ordinary-file snapshot of
Unit Flint mark 24, SHA-256
`c683e558cdbdf6cf73d4b32572b6fa498b80e7816483b882bf2d51adfff3062e`.
The bounded parser never evaluates Python code. Each expression has limits of
4,096 characters, 256 tokens and 32 nesting levels; exact intermediates share
the 2,048-bit budget, including the new difference, allowance, margin and display
conversions. Over-budget intermediates may reject a mathematically small final
answer. As in Unit Flint, `2 m^2` means `(2 m)^2`; write `2 * m^2` for two
square metres. Supported units are listed in the bundled engine.

```sh
python3 -B -m unittest discover -s line-4/tools/tolerance-flint -v
```

All nine tests passed locally, including 1,000 seeded independent Fraction
comparisons using mixed input/output units, inclusive and just-outside cases,
reference asymmetry, signed and zero references, exact equality, sum policy,
invalid dimensions and tolerances, resource limits, conversion invariance, and
actual CLI exit codes and streams. This is local evidence, not certification.

Limits: this checks supplied arithmetic against a supplied policy. It cannot
establish measurement accuracy, the right tolerance, statistical significance,
source authenticity, probability, or correlated uncertainty. It neither rounds
nor infers precision from decimal spelling. Currency, offset temperatures and
significant figures remain unsupported. No coin, price or payment is needed;
no ZTO or IMD exchange rate is invented. The program uses no network, files,
environment, configuration, keys, wallets or transactions; it imports only its
own bundled code and the standard library.
