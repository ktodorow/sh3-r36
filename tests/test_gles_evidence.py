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

    def test_original_game_quad_preserves_screen_coordinates_and_uvs(self):
        self.assertIn("sample_geometry_va=006b0d00", self.log)
        self.assertIn("game_quad=PASS", self.log)
        image = (self.evidence / "launcher/game-quad.ppm").read_bytes()
        _, pixels = image.split(b"\n255\n", 1)
        for x, y, rgb in [(16, 12, (255, 0, 0)), (48, 12, (0, 255, 0)),
                          (16, 40, (0, 0, 255)), (48, 40, (255, 255, 0))]:
            self.assertEqual(tuple(pixels[(y * 64 + x) * 3: (y * 64 + x) * 3 + 3]), rgb)

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
