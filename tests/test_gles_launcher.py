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
