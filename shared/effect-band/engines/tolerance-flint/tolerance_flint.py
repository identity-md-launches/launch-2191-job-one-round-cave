#!/usr/bin/env python3
"""Compare quantities using exact, explicit absolute-plus-relative tolerance."""
from __future__ import annotations

import argparse
import json
import sys

from engine import Parser, Quantity, UnitError, ZERO, dimensions, exact_decimal


def compare(observed: str, reference: str, absolute: str | None = None,
            relative: str = "0", target: str | None = None) -> dict:
    """Pass iff |observed-reference| <= absolute + relative*|reference|.

    A missing absolute tolerance means exact zero in the reference dimensions.
    Relative tolerance is dimensionless and the reference is the sole scale.
    """
    for value in (observed, reference, relative):
        if not isinstance(value, str):
            raise ValueError("observed, reference and relative must be strings")
    for value in (absolute, target):
        if value is not None and not isinstance(value, str):
            raise ValueError("absolute and target must be strings or null")
    actual = Parser(observed).parse()
    ref = Parser(reference).parse()
    if actual.dims != ref.dims:
        raise ValueError("observed and reference dimensions must match, including zero")
    atol = (Parser(absolute).parse() if absolute is not None
            else Quantity(ref.value * 0, ref.dims))
    rtol = Parser(relative).parse()
    if atol.dims != ref.dims:
        raise ValueError("absolute tolerance dimensions must match reference")
    if rtol.dims != ZERO:
        raise ValueError("relative tolerance must be dimensionless")
    if atol.value < 0 or rtol.value < 0:
        raise ValueError("tolerances must be nonnegative")
    dims = ref.dims

    def bounded(value):
        return Parser.bounded(Quantity(value, dims), 0).value

    difference = bounded(actual.value - ref.value)
    relative_part = bounded(rtol.value * abs(ref.value))
    allowed = bounded(atol.value + relative_part)
    margin = bounded(allowed - abs(difference))
    scale = Quantity(ref.value * 0 + 1, dims)
    if target is not None:
        scale = Parser(target, target=True).parse()
        if scale.dims != dims or scale.value <= 0:
            raise ValueError("target must have matching dimensions and positive scale")

    def display(value):
        return exact_decimal(bounded(value / scale.value))

    return {
        "schema": "tolerance-flint/v1",
        "request": {"observed": observed, "reference": reference,
                    "absolute": absolute, "relative": relative, "to": target},
        "rule": "abs(observed-reference) <= absolute + relative*abs(reference)",
        "unit": target if target is not None else dimensions(dims),
        "base_unit": dimensions(dims),
        "observed": display(actual.value), "reference": display(ref.value),
        "difference": display(difference), "absolute_error": display(abs(difference)),
        "absolute_tolerance": display(atol.value),
        "relative_tolerance": exact_decimal(rtol.value),
        "relative_contribution": display(relative_part),
        "allowed_error": display(allowed), "margin": display(margin),
        "inclusive": True, "passes": margin >= 0,
    }


def main(argv=None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="show a passing boundary and a failed claim")
    check = commands.add_parser("check")
    check.add_argument("observed")
    check.add_argument("--reference", required=True)
    check.add_argument("--absolute", help="nonnegative quantity; default exact zero")
    check.add_argument("--relative", default="0", help="dimensionless fraction, e.g. 1/100")
    check.add_argument("--to", help="display unit; never changes the comparison")
    args = cli.parse_args(argv)
    try:
        if args.command == "demo":
            boundary = compare("100.6 cm", "1 m", "1 mm", "0.005", "mm")
            failure = compare("100.6001 cm", "1 m", "1 mm", "0.005", "mm")
            if not boundary["passes"] or failure["passes"]:
                raise ValueError("demo self-check failed")
            output = {"boundary": boundary, "outside": failure}
            status = 0
        else:
            output = compare(args.observed, args.reference, args.absolute, args.relative, args.to)
            status = 0 if output["passes"] else 1
    except (ValueError, UnitError) as exc:
        print(f"tolerance-flint: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(output, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
