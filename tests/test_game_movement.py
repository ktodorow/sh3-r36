"""Compare timed movement through real launcher/game with read-only checkpoint input."""
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import unittest
from test_preflight import LauncherFixture, REPO


@unittest.skipUnless(os.environ.get('SH3_MOVEMENT_SEED'), 'requires collected owner checkpoint in ARM64 Docker')
class MovementTimingTests(LauncherFixture):
    def test_checkpoint_movement_keeps_speed_when_presentation_is_slow(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        root = Path('/evidence')
        observations = []
        for name, delay in [('reference', 0), ('slow', 67)]:
            out = root / name
            out.mkdir()
            env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
                   'SH3_SEED_SESSION': os.environ['SH3_MOVEMENT_SEED'], 'SH3_DATA_DIR': '/owner',
                   'SH3_RUN_ID': name, 'SH3_PACKAGE_DIR': str(REPO),
                   'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
                   'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
                   'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_STATS': '1',
                   'SH3_KEYS': '10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4,50:S+4',
                   'SH3_QUIT_AFTER': '66',
                   'SH3_PEEK': '72C808,72C80C,72C818,72C7F0,72C7F4,72C7F8,72C7E8,BCC630,8984E0,8984E8,898660,72D2C0',
                   'SH3_TEST_SWAP_MS': str(delay)}
            # Presentation delay injected only at external SDL boundary, never guest clocks.
            if delay:
                env['LD_PRELOAD'] = str(root / 'slow-presentation.so')
            with (out / 'stdout.txt').open('w') as stdout, (out / 'stderr.txt').open('w') as stderr:
                result = subprocess.run(['timeout', '--kill-after=3s', '72s', 'bash',
                                         str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                        stdout=stdout, stderr=stderr, timeout=78)
            run = self.port / 'runs' / name
            shutil.copytree(run, out / 'launcher')
            logs = (run / 'stderr.txt').read_text()
            self.assertEqual(result.returncode, 0, logs[-4000:])
            self.assertIn('save: open C:\\SH3\\savedata\\data.001 access 80000000 disposition 3 -> ok', logs)
            samples = []
            for row in logs.splitlines():
                if not row.startswith('peek frame '):
                    continue
                values = {int(k, 16): int(v, 16) for k, v in re.findall(r'([0-9A-F]{8})=([0-9A-F]{8})', row)}
                f32 = lambda address: struct.unpack('<f', struct.pack('<I', values[address]))[0]
                samples.append({'clock': (values[0x72C808] + (values[0x72C80C] << 32)) / values[0x72C818],
                                'ticks': values[0x72C7F0], 'elapsed_ticks': values[0x72C7F4],
                                'simulation_step': values[0xBCC630], 'timer_mode': values[0x72C7E8],
                                'x': f32(0x8984E8), 'z': f32(0x8984E0),
                                'health': f32(0x898660), 'room': values[0x72D2C0]})
            (out / 'samples.json').write_text(json.dumps(samples, indent=2) + '\n')
            self.assertTrue(samples, 'missing real game observations')
            # Active checkpoint and actual input required before any speed verdict.
            active = [s for s in samples if math.isfinite(s['x']) and math.isfinite(s['z']) and s['health'] > 0 and s['room'] > 0]
            self.assertGreater(len(active), 2, 'checkpoint did not reach live player state')
            self.assertGreater(active[-1]['ticks'], 57 * 60, 'last sample precedes completed input; invalid comparison')
            observations.append(active)
        speeds = []
        for active in observations:
            start, end = active[0], active[-1]
            distance = math.hypot(end['x'] - start['x'], end['z'] - start['z'])
            self.assertGreater(distance, 5, 'input did not move player; invalid timing setup')
            self.assertEqual(end['room'], start['room'], 'movement crossed room boundary; invalid comparison')
            speeds.append(distance / 4)
        self.assertEqual(observations[0][0]['room'], observations[1][0]['room'], 'different checkpoints')
        ratio = speeds[1] / speeds[0]
        (root / 'comparison.json').write_text(json.dumps({'reference_units_per_second': speeds[0],
                                                        'slow_units_per_second': speeds[1], 'ratio': ratio}, indent=2))
        self.assertAlmostEqual(ratio, 1, delta=0.1, msg='movement slows when presentation is slow')
