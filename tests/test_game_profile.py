"""Opt-in frame costs observed through installed launcher and real checkpoint."""
import csv
from collections import Counter
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from test_preflight import LauncherFixture, REPO


@unittest.skipUnless(os.environ.get('SH3_ROUTE_TEST'), 'requires isolated opening checkpoint in ARM64 Docker')
class RouteTransitionTests(LauncherFixture):
    def test_opening_route_reaches_next_live_monster_room(self):
        from scenes import SCENES
        plan = SCENES['explore-route-320']
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/door-route')
        out.mkdir()
        env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
               'SH3_DATA_DIR': '/owner', 'SH3_SEED_SESSION': '/seed',
               'SH3_RUN_ID': 'door-route', 'SH3_PACKAGE_DIR': str(REPO),
               'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
               'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
               'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_KEYS': plan['keys'],
               'SH3_PEEK': plan['peek'], 'SH3_QUIT_AFTER': str(plan['seconds']),
               'SH3_INTERNAL_RESOLUTION': plan['internal_resolution'],
               'SH3_FPS_LIMIT': str(plan['fps_limit'])}
        for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PROFILE',
                    'SH3_GPU_PROFILE', 'LD_PRELOAD'):
            env.pop(key, None)
        result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                capture_output=True, text=True, timeout=plan['seconds'] + 25)
        (out / 'stdout.txt').write_text(result.stdout)
        (out / 'stderr.txt').write_text(result.stderr)
        shutil.copytree(self.port / 'runs/door-route', out / 'launcher')
        logs = (out / 'launcher/stderr.txt').read_text()
        self.assertEqual(result.returncode, 0, logs[-4000:])
        self.assertIn('ExitProcess(0)', logs)
        rooms = {}
        for line in logs.splitlines():
            stamp = re.match(r'peek frame \d+:.*wall_ms=(\d+)', line)
            if not stamp or int(stamp[1]) < 48000:
                continue
            values = {int(k, 16): int(v, 16) for k, v in
                      re.findall(r'([0-9A-F]{8})=([0-9A-F]{8})', line)}
            room = values.get(0x72D2C0)
            rooms.setdefault(room, []).append(values)
        self.assertIn(210, rooms, 'opening checkpoint was not loaded')
        self.assertIn(211, rooms, 'route did not open door into next monster room')
        live = [v for v in rooms[211] if 0 < v[0x898660] < 0x7F800000]
        self.assertGreater(len(live), 20, 'insufficient live monster-room coverage')
        self.assertGreater(len({(v[0x8984E0], v[0x8984E8]) for v in live}), 10,
                           'player did not move through monster room')


@unittest.skipUnless(os.environ.get('SH3_PROFILE_TEST'), 'requires owner checkpoint in ARM64 Docker')
class GameProfileTests(LauncherFixture):
    def test_near_budget_checkpoint_does_not_latch_to_twenty_fps(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/frame-budget')
        out.mkdir()
        observer = out / 'frame-budget.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/frame-budget.c'),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)
        report = out / 'frames.csv'
        env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
               'SH3_DATA_DIR': '/owner', 'SH3_SEED_SESSION': '/seed',
               'SH3_RUN_ID': 'frame-budget', 'SH3_PACKAGE_DIR': str(REPO),
               'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
               'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
               'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_PROFILE': str(report),
               'SH3_GPU_PROFILE': '0', 'SH3_INTERNAL_RESOLUTION': '320x240',
               'SH3_KEYS': '10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4',
               'SH3_QUIT_AFTER': '64', 'SH3_FPS_LIMIT': '30',
               'LD_PRELOAD': str(observer)}
        for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PEEK'):
            env.pop(key, None)
        result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                capture_output=True, text=True, timeout=80)
        (out / 'stdout.txt').write_text(result.stdout)
        (out / 'stderr.txt').write_text(result.stderr)
        shutil.copytree(self.port / 'runs/frame-budget', out / 'launcher')
        logs = (out / 'launcher/stderr.txt').read_text()
        self.assertEqual(result.returncode, 0, logs[-3000:])
        self.assertIn('ExitProcess(0)', logs)
        delayed = re.findall(r'frame_budget delayed_input_polls=(\d+) delay_ms=32', logs)
        self.assertEqual(len(delayed), 1, 'missing actual input-latency observation')
        self.assertGreater(int(delayed[0]), 200, 'near-budget workload did not run')
        measured = re.findall(r'frame_budget .* observed_mean_ms=([\d.]+) observed_max_ms=([\d.]+)', logs)
        self.assertEqual(len(measured), 1, 'missing calibrated external delay')
        self.assertGreaterEqual(float(measured[0][0]), 32)
        self.assertLessEqual(float(measured[0][0]), 33, 'injected delay exceeds stated workload')
        with Path(str(report) + '.presents.csv').open() as stream:
            active = [r for r in csv.DictReader(stream)
                      if 52000 <= int(r['elapsed_ms']) < 60000]
        self.assertTrue(active)
        self.assertEqual({r['room'] for r in active}, {'210'}, 'checkpoint not active')
        windows = Counter(int(r['elapsed_ms']) // 1000 for r in active)
        self.assertEqual(set(windows), set(range(52, 60)))
        self.assertGreaterEqual(min(windows.values()), 25,
                                'timer adds 20FPS cap to near-budget gameplay')

    def test_paced_menu_prepares_input_while_completed_swap_is_throttled(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/pacing-overlap')
        out.mkdir()
        observer = out / 'pacing-overlap.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/pacing-overlap.c'),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)
        env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
               'SH3_DATA_DIR': '/owner', 'SH3_RUN_ID': 'pacing-overlap',
               'SH3_PACKAGE_DIR': str(REPO), 'XDG_DATA_HOME': str(self.root / 'xdg'),
               'SH3_GL_BACKEND': 'desktop', 'SDL_VIDEODRIVER': 'offscreen',
               'SDL_AUDIODRIVER': 'dummy', 'LIBGL_ALWAYS_SOFTWARE': '1',
               'SH3_KEYS': '10:Return+0.4', 'SH3_QUIT_AFTER': '28',
               'SH3_INTERNAL_RESOLUTION': '320x240', 'SH3_FPS_LIMIT': '30',
               'SH3_GL_THREAD': '1', 'LD_PRELOAD': str(observer)}
        for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PEEK',
                    'SH3_PROFILE', 'SH3_GPU_PROFILE'):
            env.pop(key, None)
        result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                capture_output=True, text=True, timeout=45)
        (out / 'stdout.txt').write_text(result.stdout)
        (out / 'stderr.txt').write_text(result.stderr)
        shutil.copytree(self.port / 'runs/pacing-overlap', out / 'launcher')
        logs = (out / 'launcher/stderr.txt').read_text()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr + logs[-2000:])
        self.assertIn('ExitProcess(0)', logs)
        matches = [tuple(map(int, match)) for match in re.findall(
            r'pacing_overlap sleeps=(\d+) productive=(\d+) input_polls=(\d+) total_polls=(\d+)', logs)
                   if int(match[0])]
        self.assertEqual(len(matches), 1)
        sleeps, productive, polls, total_polls = matches[0]
        self.assertGreater(sleeps, 50, 'observer missed actual render-worker throttle')
        self.assertGreater(total_polls, 50, 'observer missed real game input')
        self.assertGreaterEqual(productive / sleeps, 0.8,
                                'CPU waits for throttle after SDL has already completed swap')

    def test_thirty_fps_profile_paces_actual_menu_completions_without_capture(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence/paced-menu')
        out.mkdir()
        report = out / 'paced-frame-times.csv'
        env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
               'SH3_DATA_DIR': '/owner', 'SH3_RUN_ID': 'paced-menu',
               'SH3_PACKAGE_DIR': str(REPO), 'XDG_DATA_HOME': str(self.root / 'xdg'),
               'SH3_GL_BACKEND': 'desktop', 'SDL_VIDEODRIVER': 'offscreen',
               'SDL_AUDIODRIVER': 'dummy', 'LIBGL_ALWAYS_SOFTWARE': '1',
               'SH3_PROFILE': str(report), 'SH3_GPU_PROFILE': '0',
               'SH3_KEYS': '10:Return+0.4', 'SH3_QUIT_AFTER': '28',
               'SH3_INTERNAL_RESOLUTION': '320x240', 'SH3_FPS_LIMIT': '30'}
        for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_PEEK', 'LD_PRELOAD'):
            env.pop(key, None)
        result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                capture_output=True, text=True, timeout=45)
        (out / 'paced-stdout.txt').write_text(result.stdout)
        (out / 'paced-stderr.txt').write_text(result.stderr)
        shutil.copytree(self.port / 'runs/paced-menu', out / 'launcher')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        logs = (out / 'launcher/stderr.txt').read_text()
        self.assertIn('ExitProcess(0)', logs)
        self.assertNotIn('capture frame', logs)
        with Path(str(report) + '.presents.csv').open() as stream:
            completed = [r for r in csv.DictReader(stream)
                         if r['room'] == '0' and 15000 < float(r['elapsed_ms']) < 26000]
        self.assertGreater(len(completed), 100, 'real game menu did not remain active')
        intervals = [float(b['elapsed_ms']) - float(a['elapsed_ms'])
                     for a, b in zip(completed, completed[1:])]
        fps = 1000 * len(intervals) / sum(intervals)
        self.assertLessEqual(fps, 30.5, '30FPS profile wastes work rendering menu above target')
        self.assertGreaterEqual(fps, 28.5, 'pacing introduces avoidable menu slowdown')
        windows = Counter(int(float(r['elapsed_ms']) // 1000) for r in completed)
        self.assertLessEqual(max(windows.values()), 31, 'late frame caused catch-up burst')

    def test_checkpoint_reports_frame_costs_without_capturing_pixels(self):
        runtime = self.port / 'runtime/sh3'
        runtime.parent.mkdir()
        shutil.copyfile(os.environ['SH3_RUNTIME_BINARY'], runtime)
        runtime.chmod(0o755)
        out = Path('/evidence')
        report = out / 'frame-times.csv'
        observer = out / 'input-cost.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/input-cost.c'),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)
        swap_observer = out / 'swap-cost.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/presentation-cost.c'),
                        '-o', str(swap_observer), '-lSDL2', '-ldl'], check=True)
        env = {**os.environ, 'SH3_MODE': 'game', 'SH3_PORT_ROOT': str(self.port),
               'SH3_SEED_SESSION': '/seed', 'SH3_DATA_DIR': '/owner',
               'SH3_RUN_ID': 'profile', 'SH3_PACKAGE_DIR': str(REPO),
               'XDG_DATA_HOME': str(self.root / 'xdg'), 'SH3_GL_BACKEND': 'desktop',
               'SDL_VIDEODRIVER': 'offscreen', 'SDL_AUDIODRIVER': 'dummy',
               'LIBGL_ALWAYS_SOFTWARE': '1', 'SH3_PROFILE': str(report),
               'SH3_PEEK': '72D2C0',
               'LD_PRELOAD': str(observer) + ':' + str(swap_observer), 'SH3_TEST_SWAP_MS': '20',
               'SH3_KEYS': '10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4',
               'SH3_QUIT_AFTER': '62', 'SH3_INTERNAL_RESOLUTION': '640x480'}
        for key in ('SH3_SHOT', 'SH3_SHOT_EVERY', 'SH3_PRESENT_DUMP', 'SH3_GPU_PROFILE'):
            env.pop(key, None)
        with (out / 'game-stdout.txt').open('w') as stdout, (out / 'game-stderr.txt').open('w') as stderr:
            result = subprocess.run(['bash', str(REPO / 'ports/Silent Hill 3.sh')], env=env,
                                    stdout=stdout, stderr=stderr, timeout=75)
        run = self.port / 'runs/profile'
        shutil.copytree(run, out / 'launcher')
        logs = (run / 'stderr.txt').read_text()
        self.assertEqual(result.returncode, 0, logs[-4000:])
        self.assertNotIn('gpu_profile=enabled', (run / 'stdout.txt').read_text(),
                         'frame-cadence profiling unexpectedly enabled costly GPU queries')
        self.assertFalse(Path(str(report) + '.gpu.csv').exists())
        self.assertIn('frontend ready', (out / 'game-stdout.txt').read_text())
        self.assertIn('save: open C:\\SH3\\savedata\\data.001 access 80000000 disposition 3 -> ok', logs)
        self.assertNotIn('capture frame', logs)
        self.assertTrue(report.is_file(), 'requested per-frame costs missing')
        with report.open() as stream:
            rows = list(csv.DictReader(stream))
        active = [row for row in rows if row['room'] == '210' and float(row['elapsed_ms']) > 50000]
        self.assertGreater(len(active), 10, 'missing warmed real-checkpoint frames')
        sparse = re.findall(r'peek frame (\d+):[^\n]*wall_ms=(\d+)', logs)
        self.assertGreater(len(sparse), 10, 'sparse scene observations lack native wall timestamps')
        by_frame = {int(row['frame']): row for row in rows}
        previous_wall = -1
        for frame, wall in sparse:
            wall = int(wall)
            self.assertGreater(wall, previous_wall)
            previous_wall = wall
            self.assertIn(int(frame), by_frame)
            self.assertLess(abs(wall - float(by_frame[int(frame)]['elapsed_ms'])), 500,
                            'sparse observation uses a different clock than native frame report')
        for row in active:
            wall = float(row['wall_ms'])
            self.assertGreater(wall, 0)
            self.assertGreaterEqual(float(row['cpu_ms']), 0)
            self.assertLessEqual(float(row['cpu_ms']), wall * 1.1 + 1)
            self.assertGreater(float(row['draw_ms']), 0)
            self.assertLessEqual(float(row['draw_ms']) + float(row['present_ms']), wall + 0.1)
            self.assertLessEqual(float(row['swap_ms']), float(row['present_ms']) + 0.1)
            self.assertGreater(int(row['draws']), 0)
            self.assertEqual((int(row['internal_w']), int(row['internal_h'])), (640, 480))
        completed = Path(str(report) + '.presents.csv')
        self.assertTrue(completed.is_file(), 'missing actual SDL swap completion timings')
        with completed.open() as stream:
            presents = list(csv.DictReader(stream))
        swaps = re.findall(r'presentation_boundary screen=1 offscreen=\d+', logs)
        self.assertEqual(len(presents), len(swaps), 'completion log does not match actual SDL swaps')
        active_presents = [row for row in presents if row['room']=='210' and float(row['elapsed_ms'])>50000]
        self.assertGreater(len(active_presents), 10)
        frames = [int(row['frame']) for row in presents]
        self.assertEqual(frames, sorted(set(frames)))
        for row in active_presents:
            self.assertGreaterEqual(float(row['swap_ms']), 19,
                                    'timing missed delay at actual worker SDL boundary')
            self.assertGreater(float(row['wall_ms']), 0)
            self.assertEqual((int(row['internal_w']),int(row['internal_h'])), (640,480))
        for previous, current in zip(presents,presents[1:]):
            self.assertGreaterEqual(int(current['elapsed_ms']),int(previous['elapsed_ms']))
        samples = Path(str(report) + '.samples')
        self.assertTrue(samples.is_file(), 'requested CPU hotspot samples missing')
        with samples.open() as stream:
            costs = list(csv.DictReader(stream))
        self.assertGreater(len(costs), 10, 'CPU sampler did not observe running game')
        self.assertTrue(any(row['module'].endswith('/sh3') for row in costs), 'native game code not sampled')
        self.assertTrue(all(int(row['pc'], 16) > 0 and int(row['offset'], 16) >= 0 for row in costs))
        self.assertTrue(all(row.get('caller_module') for row in costs), 'CPU samples omit caller location')
        self.assertTrue(any(row['caller_module'].endswith('/sh3') for row in costs),
                        'CPU sampler did not retain native caller locations')
        calls = re.findall(r'input_boundary polls=(\d+) names=(\d+)', logs)
        self.assertEqual(len(calls), 1, 'missing real keyboard boundary observation')
        polls, names = map(int, calls[0])
        self.assertGreater(polls, 10)
        # Five fixed events plus generous margin for SDL's own initialization.
        self.assertLessEqual(names, 128,
                             'scripted input repeatedly decodes unchanged schedule at every poll')
