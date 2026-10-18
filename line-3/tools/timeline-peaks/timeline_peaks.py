#!/usr/bin/env python3
"""Show the largest shared-time groups in a verified incident timeline pack."""

import argparse
from datetime import datetime
import heapq
import re
import sys

import replay

FORMAT = "timeline-peaks/1"
HEX = re.compile(r"[0-9a-f]{64}\Z")
MAX_GROUPS_SHOWN = 200
MAX_EVENTS_PER_GROUP = 200


def _micros(value):
    return replay.engine.micros(datetime.fromisoformat(value.replace("Z", "+00:00")))


def _collect(events):
    """Return citation-sorted event records with exact half-open integer bounds."""
    result = []
    for event in events:
        result.append({
            "source": event["source"],
            "line": event["line"],
            "start": _micros(event["start_utc"]),
            "end": _micros(event["end_utc_exclusive"]),
        })
    result.sort(key=lambda item: (item["source"], item["line"]))
    if any(item["start"] >= item["end"] for item in result):
        raise replay.ReplayError("verified timeline contains an empty event interval")
    return result


def _endpoints(events):
    points = []
    for index, event in enumerate(events):
        # Endpoints are half-open: remove intervals ending at t before adding
        # intervals starting at t, so touching intervals do not overlap.
        points.append((event["start"], 1, index))
        points.append((event["end"], 0, index))
    points.sort()
    return points


def _maximum_depth(events, points):
    active = set()
    maximum = 0
    at = 0
    while at < len(points):
        time = points[at][0]
        end = at
        while end < len(points) and points[end][0] == time:
            end += 1
        for _, kind, index in points[at:end]:
            if kind == 0:
                active.remove(index)
        for _, kind, index in points[at:end]:
            if kind == 1:
                active.add(index)
        if end < len(points) and points[end][0] > time:
            maximum = max(maximum, len(active))
        at = end
    return maximum


def _peak_windows(events, points, maximum, limit):
    """Second sweep emits only globally largest shared-time sets."""
    if maximum == 0:
        return 0, []
    active = set()
    total = 0
    shown = []
    at = 0
    while at < len(points):
        time = points[at][0]
        end = at
        while end < len(points) and points[end][0] == time:
            end += 1
        for _, kind, index in points[at:end]:
            if kind == 0:
                active.remove(index)
        for _, kind, index in points[at:end]:
            if kind == 1:
                active.add(index)
        if end < len(points):
            next_time = points[end][0]
            if time < next_time and len(active) == maximum:
                total += 1
                if len(shown) < limit:
                    sample = heapq.nsmallest(MAX_EVENTS_PER_GROUP, active)
                    citations = [{
                        "source": events[index]["source"],
                        "line": events[index]["line"],
                        "start_utc": replay.engine.utc_text(events[index]["start"]),
                        "end_utc_exclusive": replay.engine.utc_text(events[index]["end"]),
                    } for index in sample]
                    shown.append({
                        "shared_window": {
                            "start_utc_inclusive": replay.engine.utc_text(time),
                            "end_utc_exclusive": replay.engine.utc_text(next_time),
                        },
                        "events_total": maximum,
                        "events_shown": citations,
                        "events_not_shown": maximum - len(citations),
                    })
        at = end
    return total, shown


def _components(events):
    """Count transitive interval-overlap components (touching is not overlap)."""
    ordered = sorted(events, key=lambda item: (item["start"], item["end"], item["source"], item["line"]))
    if not ordered:
        return 0, 0
    count = 0
    largest = 0
    component_end = None
    component_size = 0
    for event in ordered:
        if component_end is None or event["start"] >= component_end:
            if component_size:
                count += 1
                largest = max(largest, component_size)
            component_end = event["end"]
            component_size = 1
        else:
            component_size += 1
            component_end = max(component_end, event["end"])
    count += 1
    largest = max(largest, component_size)
    return count, largest


def analyze(pack, limit=50):
    if type(limit) is not int or not 0 <= limit <= MAX_GROUPS_SHOWN:
        raise replay.ReplayError(f"limit must be an integer in 0..{MAX_GROUPS_SHOWN}")
    checked = replay.verify_pack(pack)
    events = _collect(pack["timeline"]["events"])
    points = _endpoints(events)
    maximum = _maximum_depth(events, points)
    total, windows = _peak_windows(events, points, maximum, limit)
    components, largest_component = _components(events)
    return {
        "format": FORMAT,
        "replay": checked,
        "counts": {
            "timestamped_events": len(events),
            "undated_lines": len(pack["timeline"]["omitted"]),
            "transitive_overlap_components": components,
            "largest_transitive_component_events": largest_component,
            "maximum_shared_time_events": maximum,
            "peak_windows_total": total,
            "peak_windows_shown": len(windows),
            "peak_windows_not_shown": total - len(windows),
        },
        "peak_windows": windows,
        "engine_sha256": pack["engine_sha256"],
        "options": pack["options"],
        "interpretation": (
            "Each peak is a maximal half-open UTC window containing the greatest number "
            "of event uncertainty intervals at one common instant. These are compatibility "
            "groups, not evidence that events happened simultaneously or were causally related. "
            "Transitive components may chain intervals that have no single shared instant. "
            "Undated lines cannot be placed. Clock bounds are analyst assertions; internal "
            "replay consistency does not establish truthful or complete evidence."
        ),
    }


def checked_pack(name, expected):
    raw = replay.read_workspace(name, replay.MAX_PACK_BYTES)
    actual = replay.digest(raw)
    if expected is not None:
        if HEX.fullmatch(expected) is None:
            raise replay.ReplayError("expected digest must be 64 lowercase hex digits")
        if expected != actual:
            raise replay.ReplayError("pack does not match expected SHA-256")
    return replay.load_pack(raw), actual


def synthetic_pack():
    # ±500 ms makes A overlap B and B overlap C, while A and C cannot share time.
    return replay.make_pack([
        ("alpha.log", b"2026-10-18T10:00:00.000Z opened\n"),
        ("beta.log", b"2026-10-18T10:00:00.800Z retried\n"),
        ("gamma.log", b"2026-10-18T10:00:01.600Z recovered\n"),
        ("later.log", b"2026-10-18T10:00:03.000Z closed\n"),
    ], clock_uncertainty_ms=500)


def demo():
    pack = synthetic_pack()
    result = analyze(pack)
    result["example"] = "synthetic, not a real incident"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="show shared-time peaks in synthetic evidence")
    inspect = commands.add_parser("analyze", help="analyze a workspace evidence pack")
    inspect.add_argument("pack")
    inspect.add_argument("--limit", type=int, default=50, help="peak windows to show (0..200)")
    inspect.add_argument("--expect-sha256", help="independently trusted exact pack digest")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            result = demo()
        else:
            pack, digest = checked_pack(args.pack, args.expect_sha256)
            result = analyze(pack, args.limit)
            result["pack_sha256"] = digest
        sys.stdout.buffer.write(replay.canonical(result) + b"\n")
        return 0
    except (OSError, ValueError, RecursionError, OverflowError) as exc:
        print("timeline-peaks: " + replay.engine.visible(str(exc)), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
