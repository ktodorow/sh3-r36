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
    def compare(self, scenario, action, seconds=66, profile='640x480'):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        root = Path('/evidence') / scenario
        root.mkdir()
        observations = []
        for name, delay in [('reference', 0), ('slow', 67)]:
            out = root / name
            out.mkdir()
            env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
                   'SH3_SEED_SESSION': os.environ['SH3_MOVEMENT_SEED'], 'SH3_DATA_DIR': '/owner',
                   'SH3_RUN_ID': scenario + '-' + name, 'SH3_PACKAGE_DIR': str(REPO),
                   'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
                   'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
                   'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_STATS': '1',
                   'SH3_KEYS': '10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4,' + action,
                   'SH3_QUIT_AFTER': str(seconds), 'SH3_INTERNAL_RESOLUTION': profile,
                   'SH3_FPS_LIMIT': '30',
                   'SH3_PEEK': '72C808,72C80C,72C818,72C7F0,72C7F4,72C7F8,72C7E8,BCC630,8984E0,8984E8,898660,72D2C0,70E66F4,712CAA0,712CAA4,712CAAC,712CAB0,72BFD0,72BFD4',
                   'SH3_TEST_SWAP_MS': str(delay)}
            # Presentation delay injected only at external SDL boundary, never guest clocks.
            if delay:
                env['LD_PRELOAD'] = '/evidence/slow-presentation.so'
            with (out / 'stdout.txt').open('w') as stdout, (out / 'stderr.txt').open('w') as stderr:
                result = subprocess.run(['timeout', '--kill-after=3s', str(seconds + 6) + 's', 'bash',
                                         str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                        stdout=stdout, stderr=stderr, timeout=seconds + 12)
            run = self.port / 'runs' / (scenario + '-' + name)
            shutil.copytree(run, out / 'launcher')
            logs = (run / 'stderr.txt').read_text()
            self.assertEqual(result.returncode, 0, logs[-4000:])
            self.assertIn('frame_limit=30', (run / 'stdout.txt').read_text())
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
                                'health': f32(0x898660), 'room': values[0x72D2C0],
                                'game_time': f32(0x70E66F4),
                                'handgun': values[0x712CAA0] >> 16,
                                'smg': values[0x712CAA4] >> 16,
                                'handgun_reserve': values[0x712CAAC] & 65535,
                                'smg_reserve': values[0x712CAB0] & 65535,
                                'internal': [values[0x72BFD0], values[0x72BFD4]]})
            (out / 'samples.json').write_text(json.dumps(samples, indent=2) + '\n')
            self.assertTrue(samples, 'missing real game observations')
            # Active checkpoint and actual input required before any speed verdict.
            active = [s for s in samples if math.isfinite(s['x']) and math.isfinite(s['z']) and s['health'] > 0 and s['room'] > 0]
            self.assertGreater(len(active), 2, 'checkpoint did not reach live player state')
            self.assertGreater(active[-1]['ticks'], 57 * 60, 'last sample precedes completed input; invalid comparison')
            self.assertEqual(active[-1]['internal'], [int(v) for v in profile.split('x')])
            observations.append(active)
        self.assertEqual(observations[0][0]['room'], observations[1][0]['room'], 'different checkpoints')
        return root, observations

    def test_checkpoint_movement_keeps_speed_when_presentation_is_slow(self):
        root, observations = self.compare('movement', '50:S+4')
        speeds = []
        for active in observations:
            start, end = active[0], active[-1]
            distance = math.hypot(end['x'] - start['x'], end['z'] - start['z'])
            self.assertGreater(distance, 5, 'input did not move player; invalid timing setup')
            self.assertEqual(end['room'], start['room'], 'movement crossed room boundary; invalid comparison')
            speeds.append(distance / 4)
            self.assertAlmostEqual(speeds[-1], 600, delta=60,
                                   msg='movement changed from independently calibrated 600 units/s')
        self.assertEqual(observations[0][0]['room'], observations[1][0]['room'], 'different checkpoints')
        ratio = speeds[1] / speeds[0]
        (root / 'comparison.json').write_text(json.dumps({'reference_units_per_second': speeds[0],
                                                        'slow_units_per_second': speeds[1], 'ratio': ratio}, indent=2))
        self.assertAlmostEqual(ratio, 1, delta=0.1, msg='movement slows when presentation is slow')

    def test_collision_and_timer_keep_wall_time_at_lower_profile(self):
        root, observations = self.compare('collision', '50:S+30', seconds=95, profile='320x240')
        ends = []
        rates = []
        for active in observations:
            start, end = active[0], active[-1]
            self.assertEqual(start['room'], end['room'], 'unexpected room transition')
            moving = [s for s in active if s['ticks'] >= 65 * 60]
            self.assertGreater(len(moving), 2, 'missing collision samples')
            self.assertGreater(math.hypot(end['x'] - start['x'], end['z'] - start['z']), 5)
            # Input continues to80s; window spans multiple sparse slow-frame samples.
            contact = [s for s in active if 65 * 60 <= s['ticks'] <= 80 * 60]
            self.assertGreaterEqual(len(contact), 2, 'insufficient contact observations')
            self.assertLess(math.hypot(contact[-1]['x'] - contact[0]['x'], contact[-1]['z'] - contact[0]['z']), 5,
                            'player did not reach collision boundary; invalid setup')
            settled = [s for s in active if s['ticks'] >= 45 * 60]
            self.assertGreater(len(settled), 2, 'missing settled game-clock samples')
            rates.append((settled[-1]['game_time'] - settled[0]['game_time']) /
                         (settled[-1]['clock'] - settled[0]['clock']))
            self.assertAlmostEqual(rates[-1], 1, delta=0.05, msg='game timer loses wall time')
            ends.append(end)
        self.assertLess(math.hypot(ends[1]['x'] - ends[0]['x'], ends[1]['z'] - ends[0]['z']), 40,
                        'slow presentation crosses collision boundary')
        (root / 'comparison.json').write_text(json.dumps({'game_time_rates': rates, 'end_positions': ends}, indent=2))
        self.assertAlmostEqual(rates[1] / rates[0], 1, delta=0.1, msg='game timer changes speed')

    def test_repeated_fire_keeps_cadence_when_presentation_is_slow(self):
        root, observations = self.compare(
            'combat', '48:I+0.4,51:S+0.15,53:S+0.15,55:E+0.15,57:E+0.15,'
            '60:Return+0.15,61:Return+0.15,62:I+0.4,63:B+6,64:Space+3', seconds=78)
        rounds = []
        for active in observations:
            start, end = active[0], active[-1]
            self.assertGreater(end['ticks'], 70 * 60, 'input not completed')
            self.assertGreater(end['handgun'], 0, 'magazine exhausted; invalid cadence comparison')
            self.assertEqual(end['handgun_reserve'], start['handgun_reserve'], 'reload confounds comparison')
            self.assertEqual(end['smg'], start['smg'], 'handgun not selected')
            fired = start['handgun'] - end['handgun']
            self.assertGreater(fired, 2, 'weapon did not repeatedly fire; invalid setup')
            rounds.append(fired)
        (root / 'comparison.json').write_text(json.dumps({'rounds_fired': rounds}, indent=2))
        self.assertLessEqual(abs(rounds[1] - rounds[0]), 1, 'repeated-fire animation/cadence slows')
