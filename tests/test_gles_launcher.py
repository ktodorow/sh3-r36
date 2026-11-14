"""GLES diagnostics via installed launcher; fixtures cover failures only."""
import os
import csv
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from test_preflight import LauncherFixture, REPO


class GlesLauncherTests(LauncherFixture):
    def test_installed_graphics_menu_finds_package_and_selects_graphics_mode(self):
        launcher = self.port / "preflight/ports/Silent Hill 3.sh"
        launcher.parent.mkdir(parents=True)
        shutil.copyfile(REPO / "ports/Silent Hill 3.sh", launcher)
        menu = self.root / "Silent Hill 3 Graphics Diagnostics.sh"
        shutil.copyfile(REPO / "ports/Silent Hill 3 Graphics Diagnostics.sh", menu)
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        runtime.write_text('#!/bin/sh\nprintf "selected=%s\\n" "$1"\n')
        runtime.chmod(0o755)
        commands = self.root / "bin"
        commands.mkdir()
        (commands / "timeout").write_text('#!/bin/sh\nshift\nexec "$@"\n')
        (commands / "timeout").chmod(0o755)
        env = {k: v for k, v in os.environ.items() if not k.startswith("SH3_")}
        env.update(XDG_DATA_HOME=str(self.root / "xdg"), PATH=f"{commands}:{os.environ['PATH']}")
        result = subprocess.run(["bash", str(menu)], env=env, cwd="/", capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("selected=--gles-diagnostics", result.stdout)
        self.assertIn("frontend ready", result.stdout)

    def test_missing_graphics_runtime_reports_install_step_and_returns(self):
        result = self.launch(SH3_MODE="gles-diagnostics")
        self.assertEqual(result.returncode, 3)
        self.assertIn("Native runtime missing", result.stderr)
        self.assertIn("frontend ready", result.stdout)
        self.assertEqual(self.save.read_bytes(), b"owner save remains unchanged")


@unittest.skipUnless(os.environ.get("SH3_RUNTIME_BINARY"), "requires Linux ARM64 Docker-built binary")
class GlesNativeLauncherTests(LauncherFixture):
    def setUp(self):
        super().setUp()
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        shutil.copyfile(os.environ["SH3_RUNTIME_BINARY"], runtime)
        runtime.chmod(0o755)

    def observe_graphics_cost(self, name, source='sampler-cost.c', **environment):
        observer = self.root / (name + '-cost.so')
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests' / source),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)
        result = self.launch(SH3_MODE='gles-diagnostics', SDL_VIDEODRIVER='offscreen',
                             SDL_AUDIODRIVER='dummy', SH3_GL_BACKEND='desktop',
                             SH3_GRAPHICS_REFERENCE='1', LIBGL_ALWAYS_SOFTWARE='1',
                             LD_PRELOAD=str(observer), **environment)
        if os.environ.get('SH3_REFERENCE_OUT'):
            evidence = Path(os.environ['SH3_REFERENCE_OUT']).parent / (name + '-boundary.txt')
            evidence.write_text(result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('desktop_reference=PASS', result.stdout)
        self.assertIn('frontend ready', result.stdout)
        return result

    def cached_graphics_launches(self, change_cache=None, **environment):
        label = self._testMethodName.removeprefix('test_')
        cold = self.observe_graphics_cost(label + '-cold', 'shader-cache-cost.c', SH3_RUN_ID='cold')
        if change_cache:
            change_cache(self.port / 'runs/cold/sh3-gl-cache.bin')
        control = self.pm / 'control.txt'
        control.write_text(control.read_text() +
            'pm_platform_helper() {\n'
            '  if [ -f "$SH3_PORT_ROOT/runs/cold/sh3-gl-cache.bin" ]; then\n'
            '    cp "$SH3_PORT_ROOT/runs/cold/sh3-gl-cache.bin" '
            '"$SH3_PORT_ROOT/runs/warm/sh3-gl-cache.bin"\n'
            '  fi\n}\n')
        warm = self.observe_graphics_cost(label + '-warm', 'shader-cache-cost.c', SH3_RUN_ID='warm',
                                          **environment)
        for result in (cold, warm):
            for marker in ('indexed_base_vertex=PASS', 'skinning=PASS', 'precision_render=PASS',
                           'samplers=PASS', 'palette_updates=PASS', 'presentation=PASS'):
                self.assertIn(marker, result.stdout)
        counts = []
        for result in (cold, warm):
            calls = re.findall(r'shader_cache_boundary compiled=(\d+) loaded=(\d+)', result.stderr)
            self.assertEqual(len(calls), 1, 'missing real shader compiler boundary observation')
            counts.append(tuple(map(int, calls[0])))
        self.assertGreater(counts[0][0], 10, 'cold launch did not exercise translated shaders')
        return counts

    def test_warm_launch_preserves_graphics_without_recompiling_translated_programs(self):
        counts = self.cached_graphics_launches()
        self.assertEqual(counts[1][0], 0, 'warm launch recompiles previously rendered programs')
        self.assertGreater(counts[1][1], 5, 'warm launch did not restore driver programs')

    def test_changed_driver_keeps_graphics_working_without_loading_incompatible_programs(self):
        counts = self.cached_graphics_launches(SH3_TEST_CACHE_DRIVER='different driver revision')
        self.assertGreater(counts[1][0], 10, 'changed driver must use authoritative shader source')
        self.assertEqual(counts[1][1], 0, 'old driver programs reached changed driver')

    def test_corrupt_cache_keeps_graphics_working_without_feeding_damaged_programs_to_driver(self):
        def corrupt(path):
            payload = bytearray(path.read_bytes())
            payload[-1] ^= 1
            path.write_bytes(payload)
        counts = self.cached_graphics_launches(change_cache=corrupt)
        self.assertGreater(counts[1][0], 10, 'damaged cache must fall back to shader source')
        self.assertEqual(counts[1][1], 0, 'damaged program reached driver')

    def test_unchanged_viewport_uniforms_preserve_pixels_without_repeated_uploads(self):
        result = self.observe_graphics_cost('uniform', 'uniform-cost.c')
        for marker in ('indexed_base_vertex=PASS', 'game_quad=PASS', 'skinning=PASS',
                       'rhw_depth=PASS', 'presentation=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'uniform_boundary viewport_updates=(\d+) viewport_repeats=(\d+)',
                           result.stderr)
        self.assertEqual(len(calls), 1, 'missing real uniform boundary observation')
        updates, repeats = map(int, calls[0])
        self.assertGreater(updates, 0, 'observer did not see viewport initialization')
        self.assertEqual(repeats, 0, 'unchanged viewport values repeatedly uploaded to driver')

    def test_shader_constants_preserve_skinning_without_repeated_uploads(self):
        result = self.observe_graphics_cost('constant', 'uniform-cost.c')
        for marker in ('indexed_base_vertex=PASS', 'skinning=PASS', 'precision_render=PASS',
                       'depth=PASS', 'stencil=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'constant_updates=(\d+) constant_repeats=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing real constant boundary observation')
        updates, repeats = map(int, calls[0])
        self.assertGreater(updates, 0, 'observer did not see constant initialization')
        self.assertEqual(repeats, 0, 'unchanged shader constants repeatedly uploaded to driver')

    def test_constant_ranges_preserve_matrix_rows_and_relative_skinning_with_bounded_payloads(self):
        result = self.observe_graphics_cost('constant-range', 'uniform-cost.c')
        for marker in ('indexed_base_vertex=PASS', 'skinning=PASS', 'precision_render=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'constant_range updates=(\d+) excess=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing real constant-array observation')
        updates, excess = map(int, calls[0])
        self.assertGreater(updates, 0)
        self.assertEqual(excess, 0, 'vertex payload includes constants outside linked active range')
        run = self.port / 'runs/fixture'
        # Original sample reads color c0 and matrix rows c2..c5, hence six registers.
        self.assertIn('uniform vec4 c[6];', (run / 'shader-000.vert').read_text())
        relative = [p.read_text() for p in run.glob('shader-*.vert') if 'c[a0 +' in p.read_text()]
        self.assertTrue(relative, 'relative bone-index sample unavailable')
        for source in relative:
            self.assertIn('uniform vec4 c[96];', source)

    def test_render_state_transitions_preserve_pixels_without_repeated_toggles(self):
        result = self.observe_graphics_cost('state', 'state-cost.c')
        for marker in ('culling=PASS', 'clear_scissor=PASS', 'depth=PASS',
                       'stencil=PASS', 'front_preview=PASS', 'presentation=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'state_boundary updates=(\d+) repeats=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing real state boundary observation')
        updates, repeats = map(int, calls[0])
        self.assertGreater(updates, 0, 'observer did not see state initialization')
        self.assertEqual(repeats, 0, 'unchanged render capabilities repeatedly sent to driver')

    def test_viewport_and_write_masks_preserve_pixels_without_repeated_state_uploads(self):
        result = self.observe_graphics_cost('raster', 'state-cost.c')
        for marker in ('clear_scissor=PASS', 'depth=PASS', 'stencil=PASS',
                       'framebuffer_roundtrip=PASS', 'rhw_depth=PASS', 'presentation=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'raster_boundary updates=(\d+) repeats=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing real raster-state boundary observation')
        updates, repeats = map(int, calls[0])
        self.assertGreater(updates, 0, 'observer did not see raster-state initialization')
        self.assertEqual(repeats, 0, 'unchanged viewport/depth/write masks repeatedly sent to driver')

    def test_sampler_bindings_survive_texture_changes_without_repeated_driver_binds(self):
        result = self.observe_graphics_cost('sampler-bind', 'state-cost.c')
        for marker in ('samplers=PASS', 'palette_updates=PASS', 'mip_updates=PASS',
                       'dxt_variants=PASS', 'front_preview=PASS', 'presentation=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'sampler_bind_boundary updates=(\d+) repeats=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing real sampler binding observation')
        updates, repeats = map(int, calls[0])
        self.assertGreater(updates, 0, 'observer did not see sampler initialization')
        self.assertEqual(repeats, 0, 'unchanged sampler objects repeatedly rebound to driver')

    def test_linked_sampler_usage_preserves_pixels_without_visiting_inactive_texture_units(self):
        result = self.observe_graphics_cost('texture', 'texture-cost.c')
        for marker in ('indexed_base_vertex=PASS', 'skinning=PASS', 'samplers=PASS',
                       'palette_updates=PASS', 'mip_updates=PASS', 'dxt_variants=PASS',
                       'framebuffer_roundtrip=PASS', 'front_preview=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'texture_boundary draws=(\d+) selections=(\d+) inactive=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing real linked-sampler boundary observation')
        draws, selections, inactive = map(int, calls[0])
        self.assertGreater(draws, 10)
        self.assertGreater(selections, 0, 'observer missed active texture selection')
        self.assertEqual(inactive, 0, 'draw setup visits texture units absent from linked program')

    def test_linked_program_changes_preserve_pixels_without_repeated_driver_binds(self):
        result = self.observe_graphics_cost('program', 'state-cost.c')
        for marker in ('indexed_base_vertex=PASS', 'skinning=PASS', 'precision_render=PASS',
                       'samplers=PASS', 'palette_updates=PASS', 'presentation=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'program_boundary updates=(\d+) repeats=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing real program binding observation')
        updates, repeats = map(int, calls[0])
        self.assertGreater(updates, 1, 'observer missed linked program transitions')
        self.assertEqual(repeats, 0, 'unchanged shader program repeatedly rebound to driver')

    def test_vertex_buffer_and_layout_changes_preserve_pixels_without_repeated_driver_state(self):
        result = self.observe_graphics_cost('layout', 'layout-cost.c')
        for marker in ('indexed_base_vertex=PASS', 'skinning=PASS', 'game_quad=PASS',
                       'rhw_depth=PASS', 'packed_color=PASS', 'presentation=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'layout_boundary updates=(\d+) repeats=(\d+) '
                           r'buffer_updates=(\d+) buffer_repeats=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing real vertex-state boundary observation')
        layouts, repeats, buffers, buffer_repeats = map(int, calls[0])
        self.assertGreater(layouts, 1, 'observer missed vertex layout transitions')
        self.assertGreater(buffers, 1, 'observer missed vertex buffer transitions')
        self.assertEqual(repeats, 0, 'unchanged vertex layouts repeatedly submitted to driver')
        self.assertEqual(buffer_repeats, 0, 'unchanged vertex buffer repeatedly rebound to driver')

    def test_primitive_changes_preserve_triangle_line_and_point_pixels(self):
        result = self.launch(SH3_MODE='gles-diagnostics', SDL_VIDEODRIVER='offscreen',
                             SDL_AUDIODRIVER='dummy', SH3_GL_BACKEND='desktop',
                             SH3_GRAPHICS_REFERENCE='1', LIBGL_ALWAYS_SOFTWARE='1')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('primitive_transitions=PASS gl_error=0000', result.stdout)
        run = self.port / 'runs/fixture'
        if os.environ.get('SH3_REFERENCE_OUT'):
            shutil.copytree(run, os.environ['SH3_REFERENCE_OUT'], dirs_exist_ok=True)
        for name, points in {
            'primitive-triangle': [(32,24,(255,0,0)), (2,2,(0,0,0))],
            'primitive-point': [(32,24,(0,255,0)), (31,24,(0,0,0)), (32,23,(0,0,0))],
            'primitive-point-bound': [(32,24,(0,255,0)), (31,24,(0,0,0))],
            'primitive-point-indexed': [(32,24,(0,255,0)), (31,24,(0,0,0))],
            'primitive-point-indexed-up': [(32,24,(0,255,0)), (31,24,(0,0,0))],
            'primitive-line': [(32,12,(0,0,255)), (32,24,(0,0,0))],
            'primitive-triangle-after': [(32,24,(0,0,255)), (2,2,(0,0,0))],
        }.items():
            _, pixels = (run / f'{name}.ppm').read_bytes().split(b'\n255\n', 1)
            for x, y, rgb in points:
                self.assertEqual(tuple(pixels[(y*64+x)*3:(y*64+x)*3+3]), rgb, name)
        self.assertIn('frontend ready', result.stdout)

    def test_point_size_output_is_limited_to_point_draws_with_pixels_preserved(self):
        result = self.observe_graphics_cost('primitive', 'primitive-cost.c')
        for marker in ('primitive_transitions=PASS gl_error=0000', 'skinning=PASS',
                       'game_quad=PASS', 'rhw_depth=PASS', 'presentation=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'primitive_boundary points=(\d+) other=(\d+) missing=(\d+) unused=(\d+)',
                           result.stderr)
        self.assertEqual(len(calls), 1, 'missing linked vertex shader observation')
        points, other, missing, unused = map(int, calls[0])
        self.assertGreaterEqual(points, 4, 'observer missed one of four point draw interfaces')
        self.assertGreater(other, 10)
        self.assertEqual(missing, 0, 'point draw has undefined shader point size')
        self.assertEqual(unused, 0, 'triangle or line draw writes unused point size')

    def test_context_can_render_and_swap_on_worker_then_resume_original_thread(self):
        result = self.launch(SH3_MODE='gles-diagnostics', SDL_VIDEODRIVER='offscreen',
                             SDL_AUDIODRIVER='dummy', SH3_GL_BACKEND='desktop',
                             SH3_GRAPHICS_REFERENCE='1', LIBGL_ALWAYS_SOFTWARE='1')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('worker_context=PASS distinct_thread=yes restored=yes rgba=255,0,255,255',
                      result.stdout)
        for marker in ('indexed_base_vertex=PASS', 'skinning=PASS', 'presentation=PASS',
                       'desktop_reference=PASS', 'frontend ready'):
            self.assertIn(marker, result.stdout)
        if os.environ.get('SH3_REFERENCE_OUT'):
            shutil.copytree(self.port / 'runs/fixture', os.environ['SH3_REFERENCE_OUT'], dirs_exist_ok=True)

    def test_requested_swap_effect_is_reported_before_presentation(self):
        result = self.launch(SH3_MODE='gles-diagnostics', SDL_VIDEODRIVER='offscreen',
                             SDL_AUDIODRIVER='dummy', SH3_GL_BACKEND='desktop',
                             SH3_GRAPHICS_REFERENCE='1', LIBGL_ALWAYS_SOFTWARE='1')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertRegex(result.stderr, r'CreateDevice 64x48 .* swap_effect=0\b')
        self.assertIn('presentation=PASS', result.stdout)
        self.assertIn('frontend ready', result.stdout)
        if os.environ.get('SH3_REFERENCE_OUT'):
            shutil.copytree(self.port / 'runs/fixture', os.environ['SH3_REFERENCE_OUT'], dirs_exist_ok=True)

    def test_front_pixels_survive_repeated_presents_swap_modes_and_resolution_resets(self):
        result = self.launch(SH3_MODE='gles-diagnostics', SDL_VIDEODRIVER='offscreen',
                             SDL_AUDIODRIVER='dummy', SH3_GL_BACKEND='desktop',
                             SH3_GRAPHICS_REFERENCE='1', LIBGL_ALWAYS_SOFTWARE='1')
        run = self.port / 'runs/fixture'
        if os.environ.get('SH3_REFERENCE_OUT'):
            shutil.copytree(run, os.environ['SH3_REFERENCE_OUT'], dirs_exist_ok=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('front_swap_modes=PASS gl_error=0000', result.stdout)
        for width, height in [(64,48), (80,60)]:
            for mode in [1,3]:
                for index, bgra in enumerate([b'\x00\x00\xff\xff', b'\x00\xff\x00\xff',
                                               b'\xff\x00\x00\xff']):
                    pixels = (run / f'front-mode-{mode}-{width}-{index}.bgra').read_bytes()
                    self.assertEqual(len(pixels), (width+2)*(height+2)*4)
                    for x,y in [(0,0), (width//2,height//2), (width-1,height-1)]:
                        offset = (y*(width+2)+x)*4
                        self.assertEqual(pixels[offset:offset+4], bgra)
                    for x,y in [(width,0), (0,height)]:
                        offset = (y*(width+2)+x)*4
                        self.assertEqual(pixels[offset:offset+4], b'\xcd'*4)
        self.assertIn('frontend ready', result.stdout)

    def test_discard_presents_preserve_front_pixels_without_offscreen_snapshot_blits(self):
        observer = self.root / 'presentation-cost.so'
        subprocess.run(['cc', '-shared', '-fPIC', str(REPO / 'tests/presentation-cost.c'),
                        '-o', str(observer), '-lSDL2', '-ldl'], check=True)
        result = self.launch(SH3_MODE='gles-diagnostics', SDL_VIDEODRIVER='offscreen',
                             SDL_AUDIODRIVER='dummy', SH3_GL_BACKEND='desktop',
                             SH3_GRAPHICS_REFERENCE='1', LIBGL_ALWAYS_SOFTWARE='1',
                             LD_PRELOAD=str(observer))
        if os.environ.get('SH3_REFERENCE_OUT'):
            evidence = Path(os.environ['SH3_REFERENCE_OUT']).parent / 'presentation-boundary.txt'
            evidence.write_text(result.stdout + result.stderr)
        calls = re.findall(r'presentation_boundary screen=(\d+) offscreen=(\d+)', result.stderr)
        self.assertGreaterEqual(len(calls), 12, 'observer missed repeated presentation sample')
        tail = [tuple(map(int, pair)) for pair in calls[-12:]]
        self.assertGreater(sum(screen for screen, _ in tail), 0)
        self.assertGreater(sum(offscreen for _, offscreen in tail), 0, 'COPY observation unavailable')
        for index in [0,1,2,6,7,8]:
            self.assertEqual(tail[index][1], 0, 'DISCARD still copies full front snapshot')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for marker in ('front_swap_modes=PASS gl_error=0000', 'front_preview=PASS',
                       'presentation=PASS', 'desktop_reference=PASS', 'frontend ready'):
            self.assertIn(marker, result.stdout)

    def test_framebuffer_pairs_preserve_pixels_without_repeated_attachment_and_status_work(self):
        result = self.observe_graphics_cost('framebuffer', 'framebuffer-cost.c')
        for marker in ('framebuffer_roundtrip=PASS', 'front_preview=PASS', 'mip_updates=PASS',
                       'locked_target_update=PASS', 'front_swap_modes=PASS gl_error=0000',
                       'depth=PASS', 'stencil=PASS', 'presentation=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'framebuffer_boundary attaches=(\d+) attach_repeats=(\d+) '
                           r'checks=(\d+) check_repeats=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing framebuffer boundary observation')
        attaches, attach_repeats, checks, check_repeats = map(int, calls[0])
        self.assertGreater(attaches, 2)
        self.assertGreater(checks, 1)
        self.assertEqual(attach_repeats, 0, 'unchanged framebuffer attachments repeatedly submitted')
        # One explicit completeness oracle follows the diagnostic's SetRenderTarget.
        self.assertLessEqual(check_repeats, 1, 'unchanged framebuffer pairs repeatedly validated')

    def test_renderer_uses_queued_submission_by_default_and_returns_context(self):
        result = self.observe_graphics_cost('thread-default', 'thread-cost.c')
        self.assertIn('gl_thread=enabled max_frames_ahead=1', result.stdout)
        self.assertIn('gl_thread=stopped restored=yes', result.stdout)
        self.assertRegex(result.stderr, r'thread_boundary draws=\d+ main_draws=0 changed_thread=0 '
                                       r'uploads=\d+ main_uploads=0')

    def test_optional_queue_census_matches_real_worker_queries(self):
        result = self.observe_graphics_cost('queue', 'queue-cost.c', SH3_GL_QUEUE_STATS='1')
        calls = re.findall(r'query_boundary locations=(\d+) reads=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1)
        locations, reads = map(int,calls[0])
        self.assertGreater(locations, 10)
        self.assertGreater(reads, 10)
        census = dict((name,int(count)) for name,count in
                      re.findall(r'gl_queue_sync name=(\w+) calls=(\d+) wait_ms=[0-9.]+', result.stdout))
        self.assertEqual(census.get('glGetUniformLocation'), locations)
        self.assertEqual(census.get('glReadPixels'), reads)

    def test_sampler_updates_preserve_border_pixels_without_draining_draw_queue(self):
        result = self.observe_graphics_cost('sampler-queue', 'queue-cost.c', SH3_GL_QUEUE_STATS='1')
        self.assertIn('samplers=PASS', result.stdout)
        borders = re.findall(r'query_boundary locations=\d+ reads=\d+ borders=(\d+)', result.stderr)
        self.assertEqual(len(borders), 1)
        self.assertGreater(int(borders[0]), 10, 'border state did not reach real driver')
        self.assertNotIn('gl_queue_sync name=glSamplerParameterfv ', result.stdout,
                         'sampler updates still drain queued draws')

    def test_texture_uploads_preserve_formats_rows_and_mips_without_draining_draw_queue(self):
        result = self.observe_graphics_cost('upload-queue', 'queue-cost.c', SH3_GL_QUEUE_STATS='1')
        for marker in ('texture_formats=PASS', 'palette_updates=PASS', 'mip_updates=PASS',
                       'dxt_variants=PASS', 'dxt_edges_updates=PASS', 'locked_target_update=PASS',
                       'compressed_copy_tail=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'images=(\d+) blocks=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1)
        images, blocks = map(int,calls[0])
        self.assertGreater(images, 20)
        self.assertGreater(blocks, 20)
        self.assertNotIn('gl_queue_sync name=glTexSubImage2D ', result.stdout,
                         'pixel uploads still drain queued draws')
        self.assertNotIn('gl_queue_sync name=glCompressedTexSubImage2D ', result.stdout,
                         'compressed uploads still drain queued draws')

    def test_resource_deletions_preserve_pixels_without_draining_draw_queue(self):
        result = self.observe_graphics_cost('delete-queue', 'queue-cost.c', SH3_GL_QUEUE_STATS='1')
        for marker in ('texture_formats=PASS', 'mip_updates=PASS', 'dxt_variants=PASS',
                       'framebuffer_roundtrip=PASS', 'locked_target_update=PASS',
                       'front_swap_modes=PASS gl_error=0000', 'presentation=PASS'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'delete_boundary textures=(\d+) buffers=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing actual resource-deletion observation')
        textures, buffers = map(int, calls[0])
        self.assertGreater(textures, 10)
        self.assertGreater(buffers, 1)
        for name in ('glDeleteTextures', 'glDeleteBuffers'):
            self.assertNotIn('gl_queue_sync name=' + name + ' ', result.stdout,
                             'resource release still drains queued draws')

    def test_optional_gpu_timings_report_real_completed_queries_without_blocking_or_pixel_changes(self):
        report = self.root / 'gpu.csv'
        result = self.observe_graphics_cost('gpu', 'gpu-cost.c', SH3_GPU_PROFILE=str(report))
        for marker in ('depth=PASS', 'rhw_depth=PASS', 'front_preview=PASS', 'samplers=PASS'):
            self.assertIn(marker,result.stdout)
        self.assertTrue(report.is_file(), 'requested GPU timings missing')
        with report.open() as stream:
            rows = list(csv.DictReader(stream))
        costs = re.findall(r'gpu_boundary begins=(\d+) ends=(\d+) reads=(\d+) '
                           r'premature=(\d+) main=(\d+) finishes=(\d+) ns=(\d+)', result.stderr)
        self.assertEqual(len(costs),1)
        begins,ends,reads,premature,main,finishes,nanoseconds = map(int,costs[0])
        self.assertGreater(reads,2)
        self.assertEqual(begins,ends)
        self.assertEqual(reads,len(rows))
        self.assertEqual((premature,main,finishes),(0,0,0))
        self.assertAlmostEqual(sum(float(row['gpu_ms']) for row in rows)*1000000,
                               nanoseconds,delta=reads)
        self.assertTrue(all(float(row['gpu_ms'])>=0 for row in rows))
        frames = [int(row['frame']) for row in rows]
        self.assertEqual(frames,sorted(set(frames)))

    def test_optional_gpu_timing_unavailable_entry_point_keeps_graphics_working(self):
        report = self.root / 'unavailable-gpu.csv'
        result = self.observe_graphics_cost('gpu-unavailable', 'gpu-cost.c',
                                           SH3_GPU_PROFILE=str(report),SH3_TEST_NO_GPU_TIMER='1')
        self.assertIn('gpu_profile=unavailable reason=entry-points',result.stdout)
        self.assertNotIn('gpu_profile=enabled',result.stdout)
        self.assertFalse(report.exists())
        self.assertNotIn('gpu_boundary',result.stderr)
        self.assertIn('front_preview=PASS',result.stdout)

    def test_disabled_gpu_timing_performs_no_query_work(self):
        result = self.observe_graphics_cost('gpu-disabled', 'gpu-cost.c', SH3_GPU_PROFILE='0')
        self.assertNotIn('gpu_profile=enabled',result.stdout)
        self.assertNotIn('gpu_boundary',result.stderr)
        self.assertIn('front_preview=PASS',result.stdout)

    def test_explicit_single_thread_fallback_keeps_pixels_and_frontend_return(self):
        result = self.observe_graphics_cost('thread-off', 'thread-cost.c', SH3_GL_THREAD='0')
        self.assertNotIn('gl_thread=enabled', result.stdout)
        calls = re.findall(r'thread_boundary draws=(\d+) main_draws=(\d+) changed_thread=(\d+) '
                           r'uploads=(\d+) main_uploads=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1)
        draws, main_draws, changed_thread, uploads, main_uploads = map(int,calls[0])
        self.assertGreater(draws, 50)
        self.assertEqual(main_draws, draws)
        self.assertEqual(main_uploads, uploads)
        self.assertEqual(changed_thread, 0)

    def test_queued_renderer_preserves_pixels_and_submits_draws_and_uploads_on_one_worker(self):
        result = self.observe_graphics_cost('thread', 'thread-cost.c', SH3_GL_THREAD='1')
        calls = re.findall(r'thread_boundary draws=(\d+) main_draws=(\d+) changed_thread=(\d+) '
                           r'uploads=(\d+) main_uploads=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing worker boundary observation')
        draws, main_draws, changed_thread, uploads, main_uploads = map(int, calls[0])
        self.assertGreater(draws, 50)
        self.assertGreater(uploads, 20)
        self.assertEqual(main_draws, 0, 'draw submission still runs on game thread')
        self.assertEqual(main_uploads, 0, 'buffer upload still runs on game thread')
        self.assertEqual(changed_thread, 0, 'render context has multiple draw owners')
        self.assertIn('resource_compression format=83f1 native=yes', result.stdout)
        for marker in ('gl_thread=enabled max_frames_ahead=1', 'gl_thread=stopped restored=yes',
                       'framebuffer_roundtrip=PASS', 'front_preview=PASS', 'mip_updates=PASS',
                       'locked_target_update=PASS', 'front_swap_modes=PASS gl_error=0000',
                       'depth=PASS', 'stencil=PASS', 'presentation=PASS'):
            self.assertIn(marker, result.stdout)

    def test_sampler_reuse_preserves_pixels_with_bounded_driver_updates(self):
        result = self.observe_graphics_cost('sampler')
        self.assertIn('samplers=PASS', result.stdout)
        calls = re.findall(r'sampler_boundary draws=(\d+) parameters=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing real GL boundary observation')
        draws, parameters = map(int, calls[0])
        self.assertGreater(draws, 10)
        self.assertGreater(parameters, 0, 'observer did not see sampler initialization')
        self.assertLessEqual(parameters, draws * 8,
                             'unchanged sampler state repeatedly submitted to driver')

    def test_vertex_array_reuse_preserves_layouts_with_bounded_driver_updates(self):
        result = self.observe_graphics_cost('attribute')
        for marker in ('indexed_base_vertex=PASS', 'skinning=PASS', 'rhw_depth=PASS',
                       'packed_color=PASS', 'desktop_reference=PASS', 'frontend ready'):
            self.assertIn(marker, result.stdout)
        calls = re.findall(r'sampler_boundary draws=(\d+) parameters=\d+ attributes=(\d+)', result.stderr)
        self.assertEqual(len(calls), 1, 'missing real vertex-array boundary observation')
        draws, attributes = map(int, calls[0])
        self.assertGreater(draws, 10)
        self.assertGreater(attributes, 0, 'observer did not see vertex-array initialization')
        self.assertLessEqual(attributes, draws * 4,
                             'unchanged vertex arrays disabled and re-enabled every draw')

    def test_unavailable_graphics_returns_useful_failure_without_claiming_hardware_pass(self):
        result = self.launch(SH3_MODE="gles-diagnostics", SDL_VIDEODRIVER="dummy")
        self.assertEqual(result.returncode, 9, result.stderr)
        self.assertIn("GLES context unavailable", result.stderr)
        self.assertNotIn("gles=PASS", result.stdout)
        self.assertIn("frontend ready", result.stdout)

    def test_desktop_reference_renders_same_oracles_without_claiming_hardware_pass(self):
        result = self.launch(SH3_MODE="gles-diagnostics", SDL_VIDEODRIVER="offscreen",
                             SDL_AUDIODRIVER="dummy", SH3_GL_BACKEND="desktop",
                             SH3_GRAPHICS_REFERENCE="1", LIBGL_ALWAYS_SOFTWARE="1")
        run = self.port / "runs/fixture"
        if os.environ.get("SH3_REFERENCE_OUT"):
            shutil.copytree(run, os.environ["SH3_REFERENCE_OUT"], dirs_exist_ok=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for marker in ("gl_backend=desktop", "clip_coordinates=clip-control", "indexed_base_vertex=PASS",
                       "game_quad=PASS", "skinning=PASS", "clear_scissor=PASS", "culling=PASS",
                       "depth=PASS", "stencil=PASS", "precision_render=PASS", "rhw_depth=PASS",
                       "packed_color=PASS", "presentation=PASS", "desktop_reference=PASS", "frontend ready"):
            self.assertIn(marker, result.stdout)
        self.assertNotIn("gles=PASS", result.stdout)
        for name, points in {
            "indexed": [(16,12,(255,0,0)), (48,36,(255,255,0)), (2,2,(0,0,0))],
            "skinning": [(12,12,(255,0,0)), (52,36,(255,255,0))],
            "precision-fragment": [(16,12,(127,127,127))],
            "rhw-depth": [(32,16,(0,255,0)), (32,24,(0,0,0))],
            "packed-color": [(32,24,(224,32,128))],
        }.items():
            _, pixels = (run / f"{name}.ppm").read_bytes().split(b"\n255\n", 1)
            for x,y,rgb in points:
                self.assertEqual(tuple(pixels[(y*64+x)*3:(y*64+x)*3+3]), rgb, name)
        for shader in run.glob("shader-*.vert"):
            self.assertTrue(shader.read_text().startswith("#version 430 core\n"))
        self.assertIn("texture_formats=PASS", result.stdout)
        self.assertIn("palette_updates=PASS", result.stdout)
        self.assertIn("mip_updates=PASS", result.stdout)
        self.assertIn("dxt_variants=PASS", result.stdout)
        self.assertIn("resource_compression format=83f1 native=yes", result.stdout)
        self.assertIn("dxt_edges_updates=PASS", result.stdout)
        self.assertIn("framebuffer_roundtrip=PASS", result.stdout)
        self.assertIn("front_preview=PASS", result.stdout)
        self.assertIn("samplers=PASS", result.stdout)
        self.assertIn("resource_memory=PASS", result.stdout)
        self.assertIn("locked_target_update=PASS", result.stdout)
        self.assertIn("compressed_copy_tail=PASS", result.stdout)
        for fmt in (1,3,5):
            _,pixels = (run / f"dxt{fmt}-copy-tail.ppm").read_bytes().split(b"\n255\n",1)
            self.assertEqual(tuple(pixels[(24*64+32)*3:(24*64+32)*3+3]),(255,0,255))
        _,pixels = (run / "locked-target-update.ppm").read_bytes().split(b"\n255\n",1)
        for x,y,rgb in [(8,8,(255,255,0)),(48,36,(0,0,255))]:
            self.assertEqual(tuple(pixels[(y*64+x)*3:(y*64+x)*3+3]),rgb)
        self.assertRegex(result.stdout,r"graphics_peak_rss_kib=[1-9][0-9]*")
        self.assertIn("resource_storage format=827611204 levels=10 source_bytes=174776 scratch_peak_bytes=0 gpu_logical_bytes=174776",result.stdout)
        self.assertIn("resource_storage format=41 levels=10 source_bytes=349525 scratch_peak_bytes=1048576 gpu_logical_bytes=1398100",result.stdout)
        for name,rgb in {"wrap":(0,255,0), "mirror":(255,0,0), "edge":(255,0,0),
                         "border":(0,0,255), "border-linear":(128,0,128),
                         "linear":(128,128,0)}.items():
            _,pixels = (run / f"sampler-{name}.ppm").read_bytes().split(b"\n255\n",1)
            actual = pixels[(24*64+32)*3:(24*64+32)*3+3]
            self.assertTrue(all(abs(a-b) <= 1 for a,b in zip(actual,rgb)),(name,tuple(actual)))
        _,preview = (run / "front-preview.ppm").read_bytes().split(b"\n255\n",1)
        for x,y,rgb in [(16,12,(128,0,0)),(48,12,(0,128,0)),
                        (16,36,(0,0,128)),(48,36,(128,128,0))]:
            actual = preview[(y*64+x)*3:(y*64+x)*3+3]
            self.assertTrue(all(abs(a-b) <= 1 for a,b in zip(actual,rgb)),tuple(actual))
        for name,points in {
            "copy-gpu": [(16,12,(255,0,0)),(48,36,(255,255,0))],
            "copy-upload": [(8,8,(255,0,0)),(48,36,(255,255,0)),(2,2,(0,0,0))],
        }.items():
            _,pixels = (run / f"{name}.ppm").read_bytes().split(b"\n255\n",1)
            for x,y,rgb in points:
                self.assertEqual(tuple(pixels[(y*64+x)*3:(y*64+x)*3+3]),rgb,name)
        _,pixels = (run / "framebuffer-512.ppm").read_bytes().split(b"\n255\n",1)
        for x,y,rgb in [(128,128,(255,0,0)),(384,128,(0,255,0)),
                        (128,500,(0,0,255)),(384,500,(255,255,0))]:
            self.assertEqual(tuple(pixels[(y*512+x)*3:(y*512+x)*3+3]),rgb)
        for fmt in ("dxt1", "dxt3", "dxt5"):
            for suffix,points in {
                "tiles": [(8,8,(255,0,0)),(56,8,(0,255,0)),
                          (8,44,(0,0,255)),(56,44,(255,255,0))],
                "tail": [(32,24,(255,0,255))],
                "update": [(8,8,(0,255,255)),(56,44,(255,255,0))],
            }.items():
                _,pixels = (run / f"{fmt}-{suffix}.ppm").read_bytes().split(b"\n255\n",1)
                for x,y,rgb in points:
                    self.assertEqual(tuple(pixels[(y*64+x)*3:(y*64+x)*3+3]),rgb,(fmt,suffix))
        for name, rgba in {"dxt1": (170,0,85,255), "dxt1-alpha": (0,0,0,0),
                           "dxt3": (170,0,85,255), "dxt5-eight": (0,255,0,36),
                           "dxt5-six": (0,255,0,204)}.items():
            pixels = (run / f"{name}.ppm.rgba").read_bytes()
            x = 40 if name == "dxt1" else 56
            actual = pixels[(8*64+x)*4:(8*64+x)*4+4]
            self.assertTrue(all(abs(a-b) <= 1 for a,b in zip(actual,rgba)),(name,tuple(actual)))
        for name, rgba in {"mip-base": (255,0,0,255), "mip-middle": (0,255,0,255),
                           "mip-tail": (0,0,255,255), "mip-update": (255,255,0,255)}.items():
            pixels = (run / f"{name}.ppm.rgba").read_bytes()
            self.assertEqual(tuple(pixels[(24*64+32)*4:(24*64+32)*4+4]),rgba,name)
        for name, rgba in {"palette-alpha": (224,32,128,51),
                           "palette-update": (16,192,64,170),
                           "palette-select": (64,80,96,119),
                           "palette-opaque": (32,64,96,255)}.items():
            pixels = (run / f"{name}.ppm.rgba").read_bytes()
            self.assertEqual(tuple(pixels[(24*64+32)*4:(24*64+32)*4+4]),rgba,name)
        for name, rgb in {
            "argb8": (224,32,128), "xrgb8": (224,32,128),
            "rgb565": (255,0,0), "argb1555": (0,255,0),
            "xrgb1555": (0,0,255), "argb4444": (255,136,68),
            "xrgb4444": (255,136,68),
        }.items():
            _, pixels = (run / f"{name}.ppm").read_bytes().split(b"\n255\n", 1)
            self.assertEqual(tuple(pixels[(24*64+32)*3:(24*64+32)*3+3]), rgb, name)
            alpha = 51 if name in ("argb8","argb4444") else 255
            rgba = (run / f"{name}.ppm.rgba").read_bytes()
            self.assertEqual(rgba[(24*64+32)*4+3],alpha,name)
