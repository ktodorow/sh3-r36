"""Actual collected R36S observations; never synthesize hardware evidence."""
import os
import json
from pathlib import Path
import subprocess
import unittest

REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("SH3_GLES_EVIDENCE"), "requires collected native R36S graphics run")
class GraphicsEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.evidence = REPO / os.environ["SH3_GLES_EVIDENCE"]
        self.log = (self.evidence / "launcher/stdout.txt").read_text()

    def test_texture_uploads_preserve_bgra_and_packed_channel_order(self):
        self.assertIn("texture_formats=PASS", self.log)
        self.assertNotIn("source_preserved=no", self.log)
        for name, rgb in {
            "argb8": (224,32,128), "xrgb8": (224,32,128), "rgb565": (255,0,0),
            "argb1555": (0,255,0), "xrgb1555": (0,0,255),
            "argb4444": (255,136,68), "xrgb4444": (255,136,68),
        }.items():
            _, pixels = (self.evidence / f"launcher/{name}.ppm").read_bytes().split(b"\n255\n",1)
            self.assertEqual(tuple(pixels[(24*64+32)*3:(24*64+32)*3+3]),rgb,name)
            rgba = (self.evidence / f"launcher/{name}.ppm.rgba").read_bytes()
            self.assertEqual(rgba[(24*64+32)*4+3],51 if name in ("argb8","argb4444") else 255,name)

    def test_palette_alpha_and_palette_changes_reach_rendered_image(self):
        self.assertIn("palette_updates=PASS source_preserved=yes", self.log)
        for name, rgba in {"palette-alpha": (224,32,128,51),
                           "palette-update": (16,192,64,170),
                           "palette-select": (64,80,96,119),
                           "palette-opaque": (32,64,96,255)}.items():
            pixels = (self.evidence / f"launcher/{name}.ppm.rgba").read_bytes()
            self.assertEqual(tuple(pixels[(24*64+32)*4:(24*64+32)*4+4]),rgba,name)

    def test_mips_and_lock_updates_reach_selected_level(self):
        self.assertIn("mip_updates=PASS", self.log)
        for name,rgb in {"mip-base": (255,0,0), "mip-middle": (0,255,0),
                         "mip-tail": (0,0,255), "mip-update": (255,255,0)}.items():
            _,pixels = (self.evidence / f"launcher/{name}.ppm").read_bytes().split(b"\n255\n",1)
            self.assertEqual(tuple(pixels[(24*64+32)*3:(24*64+32)*3+3]),rgb,name)

    def test_dxt_variants_preserve_color_and_distinct_alpha_encodings(self):
        self.assertIn("dxt_variants=PASS", self.log)
        for name,row in {
            "dxt1": [(255,0,0,255),(0,0,255,255),(170,0,85,255),(85,0,170,255)],
            "dxt1-alpha": [(0,0,255,255),(255,0,0,255),(127,0,127,255),(0,0,0,0)],
            "dxt3": [(0,0,255,0),(255,0,0,85),(85,0,170,170),(170,0,85,255)],
            "dxt5-eight": [(0,255,0,255),(0,255,0,0),(0,255,0,218),(0,255,0,36)],
            "dxt5-six": [(0,255,0,0),(0,255,0,255),(0,255,0,51),(0,255,0,204)],
        }.items():
            pixels = (self.evidence / f"launcher/{name}.ppm.rgba").read_bytes()
            for x,rgba in zip((8,24,40,56),row):
                actual = pixels[(8*64+x)*4:(8*64+x)*4+4]
                self.assertTrue(all(abs(a-b) <= 1 for a,b in zip(actual,rgba)),(name,x,tuple(actual)))

    def test_native_backend_identity_and_shader_precision_are_observed(self):
        for value in ("sdl_backend=KMSDRM", "gl_vendor=ARM", "gl_renderer=Mali-G31",
                      "gl_version=OpenGL ES 3.2", "glsl_version=OpenGL ES GLSL ES 3.20",
                      "egl_vendor=ARM", "max_vertex_attribs=16", "highp_vertex=127,127,23",
                      "highp_fragment=127,127,23", "identity=PASS"):
            self.assertIn(value, self.log)
        providers = (self.evidence / "launcher/graphics-providers.txt").read_text()
        self.assertIn("libSDL2", providers)
        self.assertIn("mali", providers.lower())
        self.assertNotIn("libGL4ES", providers)

    def test_native_context_can_render_and_swap_on_worker_then_resume_original_thread(self):
        self.assertIn('worker_context=PASS distinct_thread=yes restored=yes rgba=255,0,255,255',
                      self.log)
        self.assertNotIn('worker_context_error=', self.log)
        self.assertIn('gles=PASS', self.log)

    def test_native_queued_renderer_completes_graphics_suite_and_restores_context(self):
        self.assertIn('gl_thread=enabled max_frames_ahead=1', self.log)
        self.assertIn('gl_thread=stopped restored=yes', self.log)
        self.assertIn('front_swap_modes=PASS gl_error=0000', self.log)
        self.assertIn('gles=PASS', self.log)

    def test_dxt_block_edges_tail_mips_and_partial_updates_are_rendered(self):
        self.assertIn("dxt_edges_updates=PASS", self.log)
        for fmt in (1,3,5):
            for suffix, points in {
                "tiles": [(8,8,(255,0,0)), (56,8,(0,255,0)),
                          (8,44,(0,0,255)), (56,44,(255,255,0))],
                "tail": [(32,24,(255,0,255))],
                "update": [(8,8,(0,255,255)), (56,44,(255,255,0))],
            }.items():
                _,pixels = (self.evidence / f"launcher/dxt{fmt}-{suffix}.ppm").read_bytes().split(b"\n255\n",1)
                for x,y,rgb in points:
                    self.assertEqual(tuple(pixels[(y*64+x)*3:(y*64+x)*3+3]),rgb)

    def test_framebuffer_depth_extent_copies_and_fresh_packed_readback(self):
        self.assertIn("framebuffer_roundtrip=PASS gl_error=0000", self.log)
        self.assertIn("readback_repeat=1 fresh=yes", self.log)
        _,pixels = (self.evidence / "launcher/framebuffer-512.ppm").read_bytes().split(b"\n255\n",1)
        for x,y,rgb in [(128,128,(255,0,0)), (384,128,(0,255,0)),
                        (128,500,(0,0,255)), (384,500,(255,255,0))]:
            self.assertEqual(tuple(pixels[(y*512+x)*3:(y*512+x)*3+3]),rgb)
        for name,points in {
            "copy-gpu": [(8,8,(255,0,0)), (48,36,(255,255,0))],
            "copy-upload": [(8,8,(255,0,0)), (48,36,(255,255,0)), (2,2,(0,0,0))],
        }.items():
            _,pixels = (self.evidence / f"launcher/{name}.ppm").read_bytes().split(b"\n255\n",1)
            for x,y,rgb in points:
                self.assertEqual(tuple(pixels[(y*64+x)*3:(y*64+x)*3+3]),rgb)

    def test_last_presented_frame_drives_upright_preview_fade(self):
        self.assertIn("front_snapshot=last-presented outside_untouched=yes",self.log)
        self.assertIn("front_preview=PASS",self.log)
        _,pixels = (self.evidence / "launcher/front-preview.ppm").read_bytes().split(b"\n255\n",1)
        for x,y,rgb in [(16,12,(128,0,0)),(48,12,(0,128,0)),
                        (16,36,(0,0,128)),(48,36,(128,128,0))]:
            actual = pixels[(y*64+x)*3:(y*64+x)*3+3]
            self.assertTrue(all(abs(a-b) <= 1 for a,b in zip(actual,rgb)),tuple(actual))

    def test_native_front_pixels_survive_swap_modes_repeated_presents_and_resets(self):
        self.assertIn('front_swap_modes=PASS gl_error=0000', self.log)
        for width,height in [(64,48), (80,60)]:
            for mode in [1,3]:
                for index,bgra in enumerate([b'\x00\x00\xff\xff', b'\x00\xff\x00\xff',
                                              b'\xff\x00\x00\xff']):
                    path = self.evidence / f'launcher/front-mode-{mode}-{width}-{index}.bgra'
                    pixels = path.read_bytes()
                    self.assertEqual(len(pixels), (width+2)*(height+2)*4)
                    for x,y in [(0,0), (width//2,height//2), (width-1,height-1)]:
                        offset = (y*(width+2)+x)*4
                        self.assertEqual(pixels[offset:offset+4], bgra)
                    for x,y in [(width,0), (0,height)]:
                        offset = (y*(width+2)+x)*4
                        self.assertEqual(pixels[offset:offset+4], b'\xcd'*4)

    def test_sampler_address_modes_border_color_and_linear_filtering(self):
        self.assertIn("samplers=PASS",self.log)
        for name,rgb in {"wrap":(0,255,0), "mirror":(255,0,0), "edge":(255,0,0),
                         "border":(0,0,255), "border-linear":(128,0,128),
                         "linear":(128,128,0)}.items():
            _,pixels = (self.evidence / f"launcher/sampler-{name}.ppm").read_bytes().split(b"\n255\n",1)
            actual = pixels[(24*64+32)*3:(24*64+32)*3+3]
            self.assertTrue(all(abs(a-b) <= 1 for a,b in zip(actual,rgb)),(name,tuple(actual)))

    def test_runtime_conversion_memory_costs_are_recorded_for_full_mip_chains(self):
        self.assertIn("resource_memory=PASS",self.log)
        self.assertRegex(self.log,r"graphics_peak_rss_kib=[1-9][0-9]*")
        for fmt,source,scratch,gpu in [(21,1398100,1048576,1398100),
                (23,699050,0,699050),(25,699050,1048576,1398100),
                (26,699050,1048576,1398100),(41,349525,1048576,1398100),
                (827611204,174776,1048576,1398100),
                (861165636,349552,1048576,1398100),(894720068,349552,1048576,1398100)]:
            self.assertIn(f"resource_storage format={fmt} levels=10 source_bytes={source} "
                          f"scratch_peak_bytes={scratch} gpu_logical_bytes={gpu}",self.log)

    def test_copy_after_target_lock_and_writable_lock_reach_gpu(self):
        self.assertIn("locked_target_update=PASS",self.log)
        for name,points in {"copy-after-lock": [(48,36,(0,0,255))],
                "locked-target-update": [(8,8,(255,255,0)),(48,36,(0,0,255))]}.items():
            _,pixels = (self.evidence / f"launcher/{name}.ppm").read_bytes().split(b"\n255\n",1)
            for x,y,rgb in points:
                self.assertEqual(tuple(pixels[(y*64+x)*3:(y*64+x)*3+3]),rgb)

    def test_compressed_copy_preserves_sub_block_tail(self):
        self.assertIn("compressed_copy_tail=PASS",self.log)
        for fmt in (1,3,5):
            _,pixels = (self.evidence / f"launcher/dxt{fmt}-copy-tail.ppm").read_bytes().split(b"\n255\n",1)
            self.assertEqual(tuple(pixels[(24*64+32)*3:(24*64+32)*3+3]),(255,0,255))

    def test_original_game_quad_preserves_screen_coordinates_and_uvs(self):
        self.assertIn("sample_geometry_va=006b0d00", self.log)
        self.assertIn("game_quad=PASS", self.log)
        image = (self.evidence / "launcher/game-quad.ppm").read_bytes()
        _, pixels = image.split(b"\n255\n", 1)
        for x, y, rgb in [(16, 12, (255, 0, 0)), (48, 12, (0, 255, 0)),
                          (16, 40, (0, 0, 255)), (48, 40, (255, 255, 0))]:
            self.assertEqual(tuple(pixels[(y * 64 + x) * 3: (y * 64 + x) * 3 + 3]), rgb)

    def test_point_triangle_and_line_switches_preserve_pixels(self):
        self.assertIn('primitive_transitions=PASS gl_error=0000', self.log)
        expected = {
            'primitive-triangle': [(32,24,(255,0,0)), (2,2,(0,0,0))],
            'primitive-line': [(32,12,(0,0,255)), (32,24,(0,0,0))],
            'primitive-triangle-after': [(32,24,(0,0,255)), (2,2,(0,0,0))],
        }
        for suffix in ('', '-bound', '-indexed', '-indexed-up'):
            expected['primitive-point' + suffix] = [(32,24,(0,255,0)),
                                                   (31,24,(0,0,0)), (32,23,(0,0,0))]
        for name, points in expected.items():
            _, pixels = (self.evidence / f'launcher/{name}.ppm').read_bytes().split(b'\n255\n', 1)
            for x, y, rgb in points:
                self.assertEqual(tuple(pixels[(y*64+x)*3:(y*64+x)*3+3]), rgb, name)

    def test_game_skin_shader_uses_weighted_relative_bone_constants(self):
        self.assertIn("sample_skin_offset=002b6b70", self.log)
        self.assertIn("skinning=PASS", self.log)
        _, pixels = (self.evidence / "launcher/skinning.ppm").read_bytes().split(b"\n255\n", 1)
        for x, y, rgb in [(12, 12, (255, 0, 0)), (52, 12, (0, 255, 0)),
                          (12, 36, (0, 0, 255)), (52, 36, (255, 255, 0)),
                          (2, 2, (0, 0, 0))]:
            self.assertEqual(tuple(pixels[(y * 64 + x) * 3: (y * 64 + x) * 3 + 3]), rgb)

    def test_clear_rect_uses_top_left_scissor_coordinates(self):
        self.assertIn("clear_scissor=PASS", self.log)
        _, pixels = (self.evidence / "launcher/scissor.ppm").read_bytes().split(b"\n255\n", 1)
        for x, y, rgb in [(8, 8, (255, 0, 0)), (8, 40, (0, 0, 0)), (24, 8, (0, 0, 0))]:
            self.assertEqual(tuple(pixels[(y * 64 + x) * 3: (y * 64 + x) * 3 + 3]), rgb)

    def test_culling_preserves_d3d_clockwise_and_counterclockwise_faces(self):
        self.assertIn("culling=PASS", self.log)
        for name, rgb in [("cw-keep", (255, 0, 0)), ("cw-drop", (0, 0, 0)),
                          ("ccw-drop", (0, 0, 0)), ("ccw-keep", (255, 0, 0))]:
            _, pixels = (self.evidence / f"launcher/{name}.ppm").read_bytes().split(b"\n255\n", 1)
            self.assertEqual(tuple(pixels[(24 * 64 + 32) * 3: (24 * 64 + 32) * 3 + 3]), rgb, name)

    def test_depth_clips_zero_to_one_and_obeys_order_and_write_mask(self):
        self.assertIn("depth=PASS", self.log)
        for name, rgb in [("depth-clip", (0, 0, 0)), ("depth-order", (0, 255, 0)),
                          ("depth-write", (0, 0, 255))]:
            _, pixels = (self.evidence / f"launcher/{name}.ppm").read_bytes().split(b"\n255\n", 1)
            self.assertEqual(tuple(pixels[(24 * 64 + 32) * 3: (24 * 64 + 32) * 3 + 3]), rgb, name)

    def test_stencil_replace_compare_write_mask_and_depth_fail_are_rendered(self):
        self.assertIn("stencil=PASS", self.log)
        for name in ("stencil-mask", "stencil-zfail"):
            _, pixels = (self.evidence / f"launcher/{name}.ppm").read_bytes().split(b"\n255\n", 1)
            self.assertEqual(tuple(pixels[(24 * 64 + 32) * 3: (24 * 64 + 32) * 3 + 3]), (0, 255, 0), name)
            self.assertEqual(tuple(pixels[(2 * 64 + 2) * 3: (2 * 64 + 2) * 3 + 3]), (0, 0, 0), name)

    def test_generated_shader_precision_preserves_large_vertex_and_fractional_pixel_values(self):
        self.assertIn("precision_render=PASS", self.log)
        for name, rgb in [("precision-vertex", (255, 255, 255)), ("precision-fragment", (127, 127, 127))]:
            _, pixels = (self.evidence / f"launcher/{name}.ppm").read_bytes().split(b"\n255\n", 1)
            for x, y in ((16, 12), (48, 36)):
                self.assertEqual(tuple(pixels[(y * 64 + x) * 3: (y * 64 + x) * 3 + 3]), rgb, name)
        for stage in ("vert", "frag"):
            shaders = list((self.evidence / "launcher").glob(f"shader-*.{stage}"))
            self.assertGreaterEqual(len(shaders), 3)
            for shader in shaders:
                source = shader.read_text()
                self.assertTrue(source.startswith("#version 300 es\n"), shader.name)
                self.assertIn("precision highp float;", source)

    def test_screen_space_depth_clamps_after_interpolation_with_varying_rhw(self):
        self.assertIn("rhw_depth=PASS", self.log)
        _, pixels = (self.evidence / "launcher/rhw-depth.ppm").read_bytes().split(b"\n255\n", 1)
        for x, y, rgb in ((32, 16, (0, 255, 0)), (32, 24, (0, 0, 0)), (2, 2, (0, 0, 0))):
            self.assertEqual(tuple(pixels[(y * 64 + x) * 3: (y * 64 + x) * 3 + 3]), rgb)

    def test_complete_graphics_run_presents_upright_window_and_returns_cleanly(self):
        status = json.loads((self.evidence / "status.json").read_text())
        self.assertEqual(status["execution"], 0)
        self.assertEqual(status["collection"], 0)
        self.assertIn("gles=PASS", self.log)
        self.assertIn("presentation=PASS", self.log)
        header, pixels = (self.evidence / "launcher/present.ppm").read_bytes().split(b"\n255\n", 1)
        self.assertEqual(header, b"P6\n640 480")
        for x, y, rgb in ((160, 120, (255, 0, 0)), (480, 120, (0, 255, 0)),
                          (160, 400, (0, 0, 255)), (480, 400, (255, 255, 0))):
            self.assertEqual(tuple(pixels[(y * 640 + x) * 3: (y * 640 + x) * 3 + 3]), rgb)
        device = self.evidence / "device"
        def frontend(name):
            return [(parts[0], parts[2]) for line in (device / name).read_text().splitlines()
                    if len(parts := line.split()) >= 3]
        self.assertTrue(frontend("frontend-before.txt"))
        self.assertEqual(frontend("frontend-before.txt"), frontend("frontend-after.txt"))
        self.assertEqual((device / "port-mounts-before.txt").read_bytes(), (device / "port-mounts-after.txt").read_bytes())
        self.assertFalse((device / "runtime-pids-after.txt").read_text().strip())
        self.assertNotIn("FAILED", (device / "firmware-libraries-after.txt").read_text())
        self.assertEqual((self.evidence / "launcher/exit-status.txt").read_text().strip(), "0")

    def test_fixed_function_packed_diffuse_color_preserves_d3d_channel_order(self):
        self.assertIn("packed_color=PASS", self.log)
        _, pixels = (self.evidence / "launcher/packed-color.ppm").read_bytes().split(b"\n255\n", 1)
        self.assertEqual(tuple(pixels[(24*64+32)*3:(24*64+32)*3+3]), (224,32,128))

    def test_game_shader_indexed_base_vertex_draw_has_expected_orientation_and_color(self):
        self.assertIn("sample_vs_offset=002b6af4", self.log)
        self.assertIn("sample_ps_offset=0028f300", self.log)
        self.assertIn("sample_input_sha1=d851669ef609b3164e3581aa8dcfbfaec866cb79", self.log)
        self.assertIn("indexed_base_vertex=PASS", self.log)
        image = (self.evidence / "launcher/indexed.ppm").read_bytes()
        header, pixels = image.split(b"\n255\n", 1)
        self.assertEqual(header, b"P6\n64 48")
        for x, y, rgb in [(16, 12, (255, 0, 0)), (48, 12, (0, 255, 0)),
                          (16, 36, (0, 0, 255)), (48, 36, (255, 255, 0)),
                          (2, 2, (0, 0, 0)), (62, 46, (0, 0, 0))]:
            self.assertEqual(tuple(pixels[(y * 64 + x) * 3: (y * 64 + x) * 3 + 3]), rgb)


@unittest.skipUnless(os.environ.get("SH3_GLES_RUN"), "requires explicit actual R36S run")
class GraphicsDeploymentTests(unittest.TestCase):
    def test_saved_workflow_installs_graphics_menu_and_reaches_native_context(self):
        result = subprocess.run(
            ["python3", "scripts/host/r36s.py", "gles", "--reviewed-helpers", os.environ["SH3_GLES_RUN"]],
            cwd=REPO, capture_output=True, text=True, timeout=360)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Evidence:", result.stdout, result.stderr)
        evidence = REPO / result.stdout.split("Evidence: ", 1)[1].splitlines()[0]
        log = (evidence / "launcher/stdout.txt").read_text()
        self.assertIn("context_created=yes", log, (evidence / "launcher/stderr.txt").read_text())
        self.assertIn("gles=PASS", log)
