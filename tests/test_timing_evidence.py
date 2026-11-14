"""Actual R36S timing evidence; fixture passes never stand in for device results."""
import json
import math
import os
from pathlib import Path
import re
import struct
import unittest


@unittest.skipUnless(os.environ.get('SH3_TIMING_EVIDENCE'), 'requires both actual R36S timing runs')
class TimingEvidenceTests(unittest.TestCase):
    def test_both_profiles_keep_movement_and_game_clock_speed(self):
        profiles = set()
        identities = []
        for name in os.environ['SH3_TIMING_EVIDENCE'].split(os.pathsep):
            run = Path(name)
            with self.subTest(run=run.name):
                status = json.loads((run / 'status.json').read_text())
                for key in ('execution', 'collection', 'launcher-collection', 'service-collection'):
                    self.assertEqual(status[key], 0, key)
                self.assertTrue(status['source-preserved'])
                identity = json.loads((run / 'scene-identity.json').read_text())
                self.assertTrue(identity['source_preserved'])
                identities.append((identity['runtime_sha256'], identity['seed_sha256']))
                plan = identity['plan']
                self.assertEqual(plan['capture_every'], 0)
                self.assertEqual(plan['keys'], '10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4,75:S+4')
                self.assertIn('OK', (run / 'device/checkpoint-source-after.txt').read_text())
                logs = (run / 'launcher/stderr.txt').read_text()
                self.assertIn('GL: Mali-G31 / OpenGL ES 3.2', logs)
                self.assertIn('output: requested 640x480 drawable 640x480', logs)
                self.assertNotIn('capture frame ', logs)
                self.assertIn('ExitProcess(0)', logs)
                self.assertIn('ActiveState=active', (run / 'service/frontend-restored.txt').read_text())
                self.assertFalse((run / 'device/runtime-pids-after.txt').read_text().strip())
                samples = []
                for row in logs.splitlines():
                    if not row.startswith('peek frame '):
                        continue
                    values = {int(k, 16): int(v, 16) for k, v in
                              re.findall(r'([0-9A-F]{8})=([0-9A-F]{8})', row)}
                    f32 = lambda address: struct.unpack('<f', struct.pack('<I', values[address]))[0]
                    samples.append({
                        'clock': (values[0x72C808] + (values[0x72C80C] << 32)) / values[0x72C818],
                        'ticks': values[0x72C7F0], 'elapsed': values[0x72C7F4], 'step': values[0xBCC630],
                        'x': f32(0x8984E8), 'z': f32(0x8984E0), 'health': f32(0x898660),
                        'room': values[0x72D2C0], 'game_time': f32(0x70E66F4),
                        'internal': [values[0x72BFD0], values[0x72BFD4]]})
                active = [s for s in samples if s['health'] > 0 and s['room'] == 210
                          and math.isfinite(s['x']) and math.isfinite(s['z'])]
                self.assertGreater(len(active), 3, 'missing live checkpoint samples')
                start, end = active[0], active[-1]
                self.assertLess(start['ticks'], 72 * 60, 'no observation before movement')
                self.assertGreater(end['ticks'], 85 * 60, 'input not completed')
                profile = tuple(int(v) for v in plan['internal_resolution'].split('x'))
                self.assertTrue(all(tuple(s['internal']) == profile for s in active))
                profiles.add(profile)
                speed = math.hypot(end['x'] - start['x'], end['z'] - start['z']) / 4
                # Independent original30FPS reference is600 units/s for this checkpoint/input.
                self.assertAlmostEqual(speed, 600, delta=60, msg='movement differs from original baseline')
                duration = end['clock'] - start['clock']
                self.assertGreater(duration, 20)
                clock_rate = (end['game_time'] - start['game_time']) / duration
                tick_rate = (end['ticks'] - start['ticks']) / duration
                self.assertAlmostEqual(clock_rate, 1, delta=0.05, msg='game timer loses wall time')
                self.assertAlmostEqual(tick_rate, 60, delta=0.1)
                (run / 'timing-analysis.json').write_text(json.dumps({
                    'samples': samples, 'movement_units_per_second': speed,
                    'game_clock_rate': clock_rate, 'timer_ticks_per_second': tick_rate,
                    'internal': profile, 'output': [640, 480]}, indent=2) + '\n')
        self.assertEqual(profiles, {(640, 480), (320, 240)}, 'both supported profiles required')
        self.assertTrue(all(value == identities[0] for value in identities), 'runtime or checkpoint differs')


if __name__ == '__main__':
    unittest.main()
