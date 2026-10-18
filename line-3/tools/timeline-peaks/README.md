# Timeline Peaks

Timeline Peaks fully replays an incident evidence pack, then finds the greatest
number of timestamp uncertainty intervals that contain one common instant. It
shows each peak window with bounded source and line citations. A separate count
of transitive overlap components makes long overlap chains visible even when no
single instant is shared by the whole chain.

One command from the repository root shows it working:

~~~sh
python3 -B line-3/tools/timeline-peaks/timeline_peaks.py demo
~~~

Observed locally: the synthetic four-event example has two events at each of two
peak windows, while a transitive component chains three events. The fourth event
is separate. The A–B and B–C windows are shown; A and C do not share a time.
These are generated sample logs, not a real incident or measured clock error.

Analyze an existing pack inside the current workspace:

~~~sh
python3 -B line-3/tools/timeline-peaks/timeline_peaks.py analyze path/to/pack.json --expect-sha256 TRUSTED_DIGEST
~~~

The optional --expect-sha256 is an independently trusted digest of the exact
pack bytes. --limit controls how many peak windows are shown (0–200). Each
shown window lists at most 200 event citations and states the exact count
omitted. Event messages and embedded logs are not echoed.

To build a pack from named log files in the current workspace, use the bundled
fixed Replay snapshot, then analyze the pack:

~~~sh
python3 -B line-3/tools/timeline-peaks/replay.py pack --clock-uncertainty-ms 250 --ignore-unmatched path/to/app.log path/to/worker.log > test/scratch/incident-pack.json
python3 -B line-3/tools/timeline-peaks/timeline_peaks.py analyze test/scratch/incident-pack.json
~~~

Create test/scratch first or choose another output location inside the
workspace. Replay embeds the exact source bytes. --ignore-unmatched keeps
unparsed physical lines explicitly accounted as undated instead of rejecting
the pack.

The sweep uses exact UTC microseconds and half-open intervals. Intervals that
only touch at an endpoint do not overlap. A peak means that every listed event
interval is compatible with one shared instant; it does not say the events were
simultaneous, causally related, or true. Transitive components may join events
whose intervals have no common point. Undated lines are counted but cannot be
placed. Clock bounds are analyst assertions. Replay proves consistency with the
shipped parser, not that logs are authentic or complete; preserve an independent
pack digest when authenticity matters.

Python 3.10+ and the standard library only. The copied replay.py and fixed
vendor/time_flint.py make this folder independently runnable without network
access or installation.

~~~sh
python3 -B -m unittest discover -s line-3/tools/timeline-peaks -v
~~~

Observed: eight focused tests passed, covering transitive chains versus shared
windows, half-open boundaries, undated-only input, citation and window limits,
invalid limits, altered-pack rejection, and deterministic output.
