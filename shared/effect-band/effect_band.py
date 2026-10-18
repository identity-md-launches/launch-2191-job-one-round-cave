#!/usr/bin/env python3
"""Compare full-data and single-deletion benchmark effects to a declared band."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'engines/case-influence'))
sys.path.insert(0, str(HERE / 'engines/tolerance-flint'))
import case_influence as influence
import tolerance_flint as tolerance

MAX_OUTPUT = 4 * 1024 * 1024


def q(value):
    return Fraction(int(value['numerator']), int(value['denominator']))


def text(value):
    return str(Fraction(value))


def review(raw, reference, absolute='0', relative='0', alpha='0.05', max_details=20):
    # The bounded arithmetic engine validates the policy even before parsing CSV.
    policy = tolerance.compare('0', reference, absolute, relative, '1')
    diagnostic = influence.review(raw, alpha, max_details)
    analysis = diagnostic['full_data_analysis']
    rows = []
    for original, deletion in zip(analysis['candidates'], diagnostic['candidates']):
        full = Fraction(original['candidate_only_pass'] - original['baseline_only_pass'],
                        analysis['paired_cases'])
        lower, upper = q(deletion['minimum_effect']), q(deletion['maximum_effect'])
        checks = [tolerance.compare(text(value), reference, absolute, relative, '1')
                  for value in (full, lower, upper)]
        rows.append({'candidate': original['name'], 'full_effect': text(full),
                     'single_deletion_range': {'minimum': text(lower), 'maximum': text(upper)},
                     'full_data_check': checks[0], 'minimum_check': checks[1],
                     'maximum_check': checks[2],
                     'all_single_deletion_effects_within_band': checks[1]['passes'] and checks[2]['passes']})
    return {'schema': 'effect-band/1', 'input_sha256': diagnostic['input_sha256'],
            'policy': {'reference': reference, 'absolute': absolute, 'relative': relative,
                       'rule': policy['rule'], 'unit': 'candidate minus baseline pass fraction'},
            'candidates': rows, 'sensitivity': diagnostic,
            'limits': [
                'Descriptive engineering tolerance only; passing does not establish statistical equivalence.',
                'The full-data analysis and all candidates remain unchanged; never choose deletions to improve a decision.',
                'Only one-case deletions are checked; no robustness to clusters, multiple omissions, or label errors is established.',
                'Reference and tolerances are user assertions, not estimated confidence or measurement uncertainty.',
                'Declare the band before inspecting outcomes to avoid a post hoc acceptance claim.',
                'No evidence of honest labels, representative sampling, independent cases or preregistration is supplied.',
                'The SHA-256 pin binds selected CSV bytes, not their authenticity or authorship.',
                'Output is ASCII JSON; decoded strings require escaping for HTML or Markdown.'
            ]}


def demo():
    result = review(influence.demo_csv(), '4/5', '1/10')
    result['data_kind'] = 'synthetic_demonstration'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo')
    command = commands.add_parser('review')
    command.add_argument('--input', required=True)
    command.add_argument('--expect-sha256', required=True)
    command.add_argument('--reference', required=True)
    command.add_argument('--absolute', default='0')
    command.add_argument('--relative', default='0')
    command.add_argument('--alpha', default='0.05')
    command.add_argument('--max-details', type=int, default=20)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        else:
            if not re.fullmatch('[0-9a-f]{64}', args.expect_sha256):
                raise ValueError('expected digest must be 64 lowercase hex digits')
            raw, _, _ = influence.engine.load_workspace_input(args.input)
            if hashlib.sha256(raw).hexdigest() != args.expect_sha256:
                raise ValueError('CSV does not match the expected SHA-256')
            result = review(raw, args.reference, args.absolute, args.relative,
                            args.alpha, args.max_details)
            result['data_kind'] = 'user_supplied_benchmark'
        output = json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2) + '\n'
        if len(output) > MAX_OUTPUT:
            raise ValueError('output exceeds 4 MiB budget; reduce max-details')
    except (ValueError, OSError, tolerance.UnitError, OverflowError, RecursionError) as exc:
        parser.exit(2, 'effect-band: ' + ascii(str(exc))[:240] + '\n')
    sys.stdout.write(output)
    # A completed review exits 0, even if its descriptive checks fail.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
