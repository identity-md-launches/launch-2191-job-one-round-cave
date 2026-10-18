"""Independent rational oracles, boundary semantics and real CLI streams."""
from fractions import Fraction
from pathlib import Path
import json
import random
import subprocess
import sys
import unittest

from engine import UnitError
from tolerance_flint import compare


class ToleranceTests(unittest.TestCase):
    def test_exact_boundary_conversion(self):
        result = compare("100.6 cm", "1 m", "1 mm", "0.005", "mm")
        self.assertTrue(result["passes"])
        self.assertEqual(result["difference"], "6")
        self.assertEqual(result["relative_contribution"], "5")
        self.assertEqual(result["allowed_error"], "6")
        self.assertEqual(result["margin"], "0")
        self.assertFalse(compare("100.6001 cm", "1 m", "1 mm", "0.005")["passes"])

    def test_reference_scaling_is_asymmetric(self):
        self.assertTrue(compare("90 m", "100 m", relative="1/10")["passes"])
        self.assertFalse(compare("100 m", "90 m", relative="1/10")["passes"])
        self.assertTrue(compare("-90 m", "-100 m", relative="1/10")["passes"])
        self.assertFalse(compare("90 m", "-100 m", relative="1/10")["passes"])

    def test_zero_reference_and_exact_defaults(self):
        self.assertTrue(compare("0 cm", "0 m")["passes"])
        self.assertFalse(compare("1 mm", "0 m", relative="100")["passes"])
        self.assertTrue(compare("1 mm", "0 m", absolute="1 mm")["passes"])
        self.assertTrue(compare("1/3", "2/6")["passes"])
        self.assertFalse(compare("0.3333333333333333", "1/3")["passes"])

    def test_sum_policy(self):
        # Sum is deliberate: neither component alone allows this error.
        self.assertTrue(compare("1.015 m", "1 m", "0.01 m", "0.01")["passes"])

    def test_seeded_fraction_oracle(self):
        rng = random.Random(2804)
        for _ in range(1000):
            actual = Fraction(rng.randint(-10000, 10000), rng.randint(1, 100))
            ref = Fraction(rng.randint(-10000, 10000), rng.randint(1, 100))
            absolute = Fraction(rng.randint(0, 500), rng.randint(1, 100))
            relative = Fraction(rng.randint(0, 10), rng.randint(1, 100))
            # Observed in cm, reference/tolerances in m, output in mm.
            result = compare(f"({actual}) * cm", f"({ref}) * m",
                             f"({absolute}) * m", str(relative), "mm")
            difference = actual / 100 - ref
            allowed = absolute + relative * abs(ref)
            self.assertEqual(result["passes"], abs(difference) <= allowed)
            self.assertEqual(Fraction(result["difference"]), difference * 1000)
            self.assertEqual(Fraction(result["allowed_error"]), allowed * 1000)
            self.assertEqual(Fraction(result["margin"]), (allowed-abs(difference))*1000)

    def test_invalid_dimensions_signs_and_types(self):
        invalid = [
            ("0 m", "0 s"), ("1 m", "1 m", "0"),
            ("1 m", "1 m", "-1 mm"), ("1 m", "1 m", None, "-0.01"),
            ("1 m", "1 m", None, "1 m"),
            ("0 m", "0 m", None, "0", "s"),
            ("1 m", "1 m", None, "0", "-m"),
            ("1 m", "1 m", None, "0", "0*m"),
            ("1 m", "1 m", None, "0", "m+m"),
            ("1/0", "1"), ("unknown", "1"), ("", "1"),
            (True, "1"), ("1", "1", 0), ("1", "1", None, False),
        ]
        for args in invalid:
            with self.subTest(args=args), self.assertRaises((ValueError, UnitError)):
                compare(*args)

    def test_budgets(self):
        for expression in ("("*40 + "1" + ")"*40, "1+"*200 + "1", "1"*4097):
            with self.assertRaises(UnitError):
                compare(expression, "1")
        # Individually valid operands; new difference/relative intermediate overflows.
        with self.assertRaises(UnitError):
            compare("1", "(1e100)^6", relative="(1e100)^6")

    def test_conversion_leaves_decision_unchanged(self):
        for target in (None, "m", "cm", "2*m", "ft"):
            result = compare("1.005 m", "100 cm", "1 mm", "1/250", target)
            self.assertTrue(result["passes"])
            self.assertEqual(Fraction(result["margin"]), 0)

    def test_cli_status_and_streams(self):
        script = str(Path(__file__).with_name("tolerance_flint.py"))
        for args, status in [
            (["demo"], 0),
            (["check", "1 m", "--reference", "100 cm"], 0),
            (["check", "1.01 m", "--reference", "1 m"], 1),
            (["check", "0 m", "--reference", "0 s"], 2),
            (["check", "--reference=-1 m", "--relative", "1/10", "--", "-0.9 m"], 0),
        ]:
            result = subprocess.run([sys.executable, "-B", script, *args],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, status, result.stderr)
            if status == 2:
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr)
            else:
                self.assertEqual(result.stderr, "")
                json.loads(result.stdout)


if __name__ == "__main__":
    unittest.main()
