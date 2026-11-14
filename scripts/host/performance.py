#!/usr/bin/env python3
"""Summarize collected SDL completion evidence locally; never access device."""
import argparse
from collections import Counter
import csv
import json
import math
from pathlib import Path
import re
import statistics
import struct


def player_observations(run, start, end):
    path = run / 'launcher/stderr.txt'
    samples = []
    for line in path.read_text(errors='replace').splitlines() if path.is_file() else []:
        clock = re.search(r'^peek frame \d+:.*wall_ms=(\d+)', line)
        if not clock or not start <= int(clock[1]) < end:
            continue
        values = {int(k, 16): int(v, 16) for k, v in
                  re.findall(r'([0-9A-F]{8})=([0-9A-F]{8})', line)}
        if not all(k in values for k in (0x72D2C0, 0x8984E0, 0x8984E8, 0x898660)):
            continue
        x, z, health = [struct.unpack('<f', struct.pack('<I', values[k]))[0]
                        for k in (0x8984E0, 0x8984E8, 0x898660)]
        room = values[0x72D2C0]
        samples.append({'elapsed_ms': int(clock[1]), 'room': room, 'x': x, 'z': z,
                        'live': room != 0 and health > 0 and
                                all(math.isfinite(v) for v in (x, z, health))})

    def counts(rows):
        live = [row for row in rows if row['live']]
        return {'observations': len(rows), 'live_observations': len(live),
                'non_live_observations': len(rows) - len(live),
                'distinct_live_positions': len({(r['room'], r['x'], r['z']) for r in live}),
                'rooms': dict(Counter(str(r['room']) for r in rows))}

    result = counts(samples)
    result['motion_windows_30s'] = [
        {'start_seconds': index * 30, **counts([s for s in samples
          if index * 30000 <= s['elapsed_ms'] < (index + 1) * 30000])}
        for index in range(int(start // 30000), math.ceil(end / 30000))]
    return result


def summarize(run, start, end):
    with (run / 'launcher/frame-times.csv.presents.csv').open() as stream:
        all_rows = list(csv.DictReader(stream))
    for row in all_rows:
        for key in ('elapsed_ms', 'wall_ms', 'swap_ms'):
            row[key] = float(row[key])
        row['frame'] = int(row['frame'])
    if len(all_rows) < 2 or any(b['elapsed_ms'] <= a['elapsed_ms']
                               for a, b in zip(all_rows, all_rows[1:])):
        raise ValueError('completion evidence requires increasing wall timestamps')
    rows = [row for row in all_rows if start <= row['elapsed_ms'] < end]
    if len(rows) < 2:
        raise ValueError('requested interval has fewer than two completed frames')
    coverage_start = max(start, all_rows[0]['elapsed_ms'])
    coverage_end = min(end, all_rows[-1]['elapsed_ms'])

    def windows(width):
        counts = Counter(int(row['elapsed_ms'] // width) for row in rows)
        # Include empty bins; exclude both partial edges using whole CSV coverage.
        return [{'start_seconds': index * width / 1000,
                 'fps': counts[index] * 1000 / width}
                for index in range(math.ceil(coverage_start / width),
                                   math.floor(coverage_end / width))]

    values = sorted(row['wall_ms'] for row in rows)
    one, five = windows(1000), windows(5000)
    return {
        'requested_seconds': [start / 1000, end / 1000],
        'observed_seconds': [rows[0]['elapsed_ms'] / 1000, rows[-1]['elapsed_ms'] / 1000],
        'frames': len(rows),
        'fps': 1000 * (len(rows) - 1) / (rows[-1]['elapsed_ms'] - rows[0]['elapsed_ms']),
        'rooms': dict(Counter(row['room'] for row in rows)),
        'internal_sizes': sorted({row['internal_w'] + 'x' + row['internal_h'] for row in rows}),
        'wall_ms': {'mean': statistics.mean(values), 'p50': statistics.median(values),
                    'p95': values[int((len(values) - 1) * .95)],
                    'p99': values[int((len(values) - 1) * .99)], 'max': values[-1]},
        'windows_1s': one, 'windows_5s': five,
        'minimum_1s_fps': min((w['fps'] for w in one), default=None),
        'minimum_5s_fps': min((w['fps'] for w in five), default=None),
        'longest_frames': sorted(rows, key=lambda row: row['wall_ms'], reverse=True)[:20],
        'player': player_observations(run, start, end),
        'method': 'all completion frames retained; interval FPS between first/last completion; '
                  'fixed wall-clock bins, including empty bins, excluding partial edges; '
                  'room, movement, health and transitions require separate evidence review',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--start', type=float, required=True, help='seconds after runtime start')
    parser.add_argument('--end', type=float, required=True, help='exclusive runtime seconds')
    args = parser.parse_args()
    if not (math.isfinite(args.start) and math.isfinite(args.end) and 0 <= args.start < args.end):
        parser.error('require finite 0 <= start < end')
    try:
        report = summarize(args.run, args.start * 1000, args.end * 1000)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, str(error) + '\n')
    output = args.run / 'performance-summary.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f"{report['fps']:.5f} FPS; min complete 1s/5s "
          f"{report['minimum_1s_fps']}/{report['minimum_5s_fps']}; "
          f"p95/p99/max {report['wall_ms']['p95']}/{report['wall_ms']['p99']}/"
          f"{report['wall_ms']['max']} ms; {output}")


if __name__ == '__main__':
    main()
