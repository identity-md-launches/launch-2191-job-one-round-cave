#!/usr/bin/env python3
"""Review single-case deletion sensitivity of a fixed paired binary family."""
import argparse
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import io
import json

import ladder_engine as engine

MAX_CASES = 2000
MAX_DETAILS = 200


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')


def fraction(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def decisions(counts, alpha, cache):
    """Same full-family Holm rule as Candidate Ladder; preserve input order on ties."""
    ps = []
    for wins, losses in counts:
        key = (wins, losses)
        if key not in cache:
            cache[key] = engine.exact_mcnemar(wins, losses)
        ps.append(cache[key])
    adjusted = [None] * len(ps)
    running = Fraction(0)
    for rank, index in enumerate(sorted(range(len(ps)), key=lambda i: (ps[i], i))):
        running = max(running, min(Fraction(1), (len(ps) - rank) * ps[index]))
        adjusted[index] = running
    return [p <= alpha for p in adjusted]


def review(raw, alpha_text='0.05', max_details=20):
    alpha = engine.parse_alpha(alpha_text)
    if type(max_details) is not int or not 0 <= max_details <= MAX_DETAILS:
        raise ValueError('max-details must be an integer from 0 through 200')
    names, rows = engine.read_csv_bytes(raw)
    if not 2 <= len(rows) <= MAX_CASES:
        raise ValueError('sensitivity review requires 2 through 2000 paired cases')
    # The engine already strictly parsed these bytes, including BOM/quoted IDs.
    reader = csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True)
    next(reader)
    ids = [row[0] for row in reader]
    base = engine.analyze(raw, names, rows, alpha)
    counts = [(c['candidate_only_pass'], c['baseline_only_pass']) for c in base['candidates']]
    baseline_decisions = [c['familywise_reject_equal_discordance'] for c in base['candidates']]
    alpha_q = Fraction(alpha)
    cache = {}
    if decisions(counts, alpha_q, cache) != baseline_decisions:
        raise ValueError('full-family rule differs from pinned engine')
    summaries = []
    for name, (wins, losses) in zip(names, counts):
        summaries.append({'name': name, 'decision_changes': 0, 'direction_changes': 0,
                          'minimum_effect': None, 'maximum_effect': None})
    # Every distinct complete outcome pattern has the same deletion result.
    # Case identifiers remain distinct and every original row is accounted for.
    pattern_cache = {}
    details = []
    affected = 0
    diagnostic_hash = hashlib.sha256()
    patterns = Counter(rows)
    for case_id, row in zip(ids, rows):
        if row not in pattern_cache:
            reduced = [(w - int(row[0] == 0 and row[i+1] == 1),
                        l - int(row[0] == 1 and row[i+1] == 0))
                       for i, (w, l) in enumerate(counts)]
            rejects = decisions(reduced, alpha_q, cache)
            effects = [Fraction(w-l, len(rows)-1) for w, l in reduced]
            changed = []
            for i, (effect, reject, (w, l)) in enumerate(zip(effects, rejects, reduced)):
                direction = (w > l) - (w < l)
                bw, bl = counts[i]
                old_direction = (bw > bl) - (bw < bl)
                if reject != baseline_decisions[i] or direction != old_direction:
                    changed.append({'name': names[i], 'reject_equal_discordance': reject,
                                    'direction': direction,
                                    'decision_changed': reject != baseline_decisions[i],
                                    'direction_changed': direction != old_direction})
            pattern_cache[row] = effects, changed
        effects, changes = pattern_cache[row]
        for i, effect in enumerate(effects):
            s = summaries[i]
            s['minimum_effect'] = effect if s['minimum_effect'] is None else min(s['minimum_effect'], effect)
            s['maximum_effect'] = effect if s['maximum_effect'] is None else max(s['maximum_effect'], effect)
        for change in changes:
            i = names.index(change['name'])
            summaries[i]['decision_changes'] += change['decision_changed']
            summaries[i]['direction_changes'] += change['direction_changed']
        item = {'removed_case': case_id, 'changes': changes,
                'effects': [fraction(e) for e in effects]}
        diagnostic_hash.update(canonical(item) + b'\n')
        if changes:
            affected += 1
            if len(details) < max_details:
                details.append(item)
    for s in summaries:
        s['minimum_effect'] = fraction(s['minimum_effect'])
        s['maximum_effect'] = fraction(s['maximum_effect'])
    return {'schema': 'case-influence-v1', 'input_sha256': hashlib.sha256(raw).hexdigest(),
            'full_data_analysis': base, 'deletions_checked': len(rows),
            'distinct_outcome_patterns': len(patterns),
            'cases_changing_decision_or_direction': affected,
            'candidates': summaries, 'details': details,
            'details_omitted': affected - len(details),
            'complete_diagnostics_sha256': diagnostic_hash.hexdigest(),
            'effect_units': 'candidate pass fraction minus baseline pass fraction',
            'limitations': [
                'Deletion results are sensitivity diagnostics, not replacement analyses or adjusted inference.',
                'Keep the original full-data decision and full prespecified family; do not choose cases to delete.',
                'Single-case stability does not establish robustness to multiple deletions, clusters, label errors or selection.',
                'Independence, representative sampling and honest outcomes are not established by this review.',
                'Non-rejection is not equivalence; small p-values do not measure practical value.',
                'Direction is encoded as -1 baseline, 0 tie, 1 candidate.'
            ]}


def demo_csv():
    # Explicit synthetic boundary: six candidate-only wins yield Holm p=.0625
    # for two identical candidates; seven yield .03125.
    return ('case,baseline,first,second\n' + ''.join(
        f'synthetic-win-{i},0,1,1\n' for i in range(7)) + 'synthetic-agreement,1,1,1\n').encode()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', help='paired CSV inside the workspace')
    group.add_argument('--demo', action='store_true')
    p.add_argument('--alpha', default='0.05')
    p.add_argument('--max-details', type=int, default=20)
    args = p.parse_args(argv)
    try:
        raw = demo_csv() if args.demo else engine.load_workspace_input(args.input)[0]
        result = review(raw, args.alpha, args.max_details)
        result['data_kind'] = 'synthetic_demonstration' if args.demo else 'user_supplied_benchmark'
        # Serialize before printing: no partial result on any validation failure.
        output = json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False)
    except (ValueError, OSError) as exc:
        p.exit(2, f'error: {exc}\n')
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
