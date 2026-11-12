"""GLES diagnostics via installed launcher; fixtures cover failures only."""
import os
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
