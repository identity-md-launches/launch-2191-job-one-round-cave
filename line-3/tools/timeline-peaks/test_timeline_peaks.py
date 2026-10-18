#!/usr/bin/env python3
"""Offline checks for Timeline Peaks."""

import unittest

import replay
import timeline_peaks as peaks


def pack_with(raw, uncertainty=0, ignore=False):
    return replay.make_pack([("worker.log", raw)], clock_uncertainty_ms=uncertainty,
                            ignore_unmatched=ignore)


class TimelinePeaksTests(unittest.TestCase):
    def test_demo_separates_peak_sharing_from_transitive_chain(self):
        result = peaks.demo()
        counts = result["counts"]
        self.assertEqual(counts["timestamped_events"], 4)
        self.assertEqual(counts["maximum_shared_time_events"], 2)
        self.assertEqual(counts["peak_windows_total"], 2)
        self.assertEqual(counts["transitive_overlap_components"], 2)
        self.assertEqual(counts["largest_transitive_component_events"], 3)
        first = {item["source"] for item in result["peak_windows"][0]["events_shown"]}
        second = {item["source"] for item in result["peak_windows"][1]["events_shown"]}
        self.assertEqual(first, {"alpha.log", "beta.log"})
        self.assertEqual(second, {"beta.log", "gamma.log"})

    def test_touching_half_open_intervals_do_not_overlap(self):
        pack = pack_with(
            b"2026-10-18T10:00:00.000Z first\n"
            b"2026-10-18T10:00:00.001Z second\n")
        result = peaks.analyze(pack)
        self.assertEqual(result["counts"]["maximum_shared_time_events"], 1)
        self.assertEqual(result["counts"]["transitive_overlap_components"], 2)
        self.assertEqual(result["counts"]["peak_windows_total"], 2)

    def test_no_timestamped_events_reports_omissions(self):
        result = peaks.analyze(pack_with(b"plain diagnostic\n", ignore=True))
        self.assertEqual(result["counts"]["timestamped_events"], 0)
        self.assertEqual(result["counts"]["undated_lines"], 1)
        self.assertEqual(result["counts"]["maximum_shared_time_events"], 0)
        self.assertEqual(result["counts"]["peak_windows_total"], 0)
        self.assertEqual(result["counts"]["transitive_overlap_components"], 0)
        self.assertEqual(result["peak_windows"], [])

    def test_group_and_citation_details_are_bounded_and_counted(self):
        repeated = b"2026-10-18T10:00:00.000Z event\n" * 205
        result = peaks.analyze(pack_with(repeated))
        group = result["peak_windows"][0]
        self.assertEqual(group["events_total"], 205)
        self.assertEqual(group["events_not_shown"], 5)
        self.assertEqual(len(group["events_shown"]), 200)
        self.assertEqual(group["events_shown"][0]["line"], 1)

    def test_peak_window_limit_keeps_exact_omission_count(self):
        raw = (
            b"2026-10-18T10:00:00.000Z one\n"
            b"2026-10-18T10:00:01.000Z two\n"
            b"2026-10-18T10:00:02.000Z three\n")
        result = peaks.analyze(pack_with(raw), limit=1)
        self.assertEqual(result["counts"]["peak_windows_total"], 3)
        self.assertEqual(result["counts"]["peak_windows_shown"], 1)
        self.assertEqual(result["counts"]["peak_windows_not_shown"], 2)

    def test_zero_limit_and_invalid_limit(self):
        pack = peaks.synthetic_pack()
        result = peaks.analyze(pack, limit=0)
        self.assertEqual(result["peak_windows"], [])
        self.assertEqual(result["counts"]["peak_windows_not_shown"], 2)
        with self.assertRaises(replay.ReplayError):
            peaks.analyze(pack, limit=True)
        with self.assertRaises(replay.ReplayError):
            peaks.analyze(pack, limit=201)

    def test_full_pack_replay_rejects_changed_report(self):
        pack = peaks.synthetic_pack()
        pack["timeline"]["events"][0]["message"] = "changed"
        with self.assertRaises(replay.ReplayError):
            peaks.analyze(pack)

    def test_output_is_deterministic(self):
        pack = peaks.synthetic_pack()
        self.assertEqual(replay.canonical(peaks.analyze(pack)),
                         replay.canonical(peaks.analyze(pack)))


if __name__ == "__main__":
    unittest.main()
