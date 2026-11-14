"""Saved host CLI: independently counted completion windows, including empty ones."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


class PerformanceReportTests(unittest.TestCase):
    def test_complete_windows_retain_stalls_and_exclude_partial_tail(self):
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            (run / 'launcher').mkdir()
            times = [*range(0, 1000, 100), *range(3500, 4000, 100),
                     *range(4000, 5000, 100), 5000, 5100]
            with (run / 'launcher/frame-times.csv.presents.csv').open('w') as stream:
                writer = csv.writer(stream)
                writer.writerow(('frame', 'elapsed_ms', 'wall_ms', 'swap_ms', 'room',
                                 'internal_w', 'internal_h'))
                for frame, elapsed in enumerate(times):
                    wall = elapsed - times[frame - 1] if frame else 100
                    writer.writerow((frame, elapsed, wall, 2, 210, 320, 240))
            result = subprocess.run([sys.executable, str(REPO / 'scripts/host/performance.py'),
                                     str(run), '--start', '0', '--end', '5.15'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((run / 'performance-summary.json').read_text())
            self.assertEqual(report['frames'], 27)
            self.assertAlmostEqual(report['fps'], 26 / 5.1)
            self.assertEqual(report['wall_ms']['max'], 2600)
            self.assertEqual([w['fps'] for w in report['windows_1s']], [10, 0, 0, 5, 10])
            self.assertEqual([w['fps'] for w in report['windows_5s']], [5])
            self.assertEqual(report['minimum_1s_fps'], 0)
            self.assertEqual(report['minimum_5s_fps'], 5)
            self.assertEqual(report['longest_frames'][0]['wall_ms'], 2600)
            self.assertEqual(report['rooms'], {'210': 27})

    def test_report_keeps_dead_player_observations_visible_beside_actual_motion(self):
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            (run / 'launcher').mkdir()
            (run / 'launcher/frame-times.csv.presents.csv').write_text(
                'frame,elapsed_ms,wall_ms,swap_ms,room,internal_w,internal_h\n'
                '1,0,100,2,210,320,240\n2,1000,1000,2,210,320,240\n'
                '3,2000,1000,2,210,320,240\n4,3000,1000,2,210,320,240\n')
            # Independent IEEE754 examples: health100; x0 then1; final health0.
            (run / 'launcher/stderr.txt').write_text(
                'peek frame 1: 0072D2C0=000000D2 008984E0=00000000 '
                '008984E8=00000000 00898660=42C80000 wall_ms=100\n'
                'peek frame 2: 0072D2C0=000000D2 008984E0=3F800000 '
                '008984E8=00000000 00898660=42C80000 wall_ms=1000\n'
                'peek frame 3: 0072D2C0=000000D2 008984E0=3F800000 '
                '008984E8=00000000 00898660=00000000 wall_ms=2000\n')
            result = subprocess.run([sys.executable, str(REPO / 'scripts/host/performance.py'),
                                     str(run), '--start', '0', '--end', '3'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            player = json.loads((run / 'performance-summary.json').read_text())['player']
            self.assertEqual(player['observations'], 3)
            self.assertEqual(player['live_observations'], 2)
            self.assertEqual(player['non_live_observations'], 1)
            self.assertEqual(player['distinct_live_positions'], 2)
            self.assertEqual(player['motion_windows_30s'][0]['distinct_live_positions'], 2)
            self.assertEqual(player['motion_windows_30s'][0]['non_live_observations'], 1)


if __name__ == '__main__':
    unittest.main()
