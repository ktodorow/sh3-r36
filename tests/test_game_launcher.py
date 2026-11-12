"""Actual owner game through launcher in ARM64 Docker; never hardware acceptance."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from test_preflight import LauncherFixture, REPO


@unittest.skipUnless(os.environ.get("SH3_GAME_DATA"), "requires read-only owner data in ARM64 Docker")
class GameLauncherTests(LauncherFixture):
    def test_select_start_exits_actual_game_but_either_button_alone_does_not(self):
        self.check_exit_combo(scripted=True)

    def check_exit_combo(self, scripted):
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        shutil.copyfile(os.environ["SH3_RUNTIME_BINARY"], runtime)
        runtime.chmod(0o755)
        pad = self.root / "virtual-exit-pad.so"
        subprocess.run(["cc", "-shared", "-fPIC", str(REPO / "tests/virtual-exit-pad.c"),
                        "-o", str(pad), "-lSDL2", "-ldl"], check=True)
        env = {**os.environ, "SH3_MODE": "game", "SH3_PORT_ROOT": str(self.port),
               "SH3_DATA_DIR": os.environ["SH3_GAME_DATA"], "SH3_RUN_ID": "game-hotkey",
               "SH3_PACKAGE_DIR": str(REPO), "XDG_DATA_HOME": str(self.root / "xdg"),
               "SH3_KEYS": "", "SH3_GL_BACKEND": "desktop", "SDL_VIDEODRIVER": "offscreen",
               "SDL_AUDIODRIVER": "dummy", "LIBGL_ALWAYS_SOFTWARE": "1", "LD_PRELOAD": str(pad),
               "SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS": "1"}
        env.pop("SH3_QUIT_AFTER", None)
        if not scripted:
            env.pop("SH3_KEYS")
        result = subprocess.run(["timeout", "--kill-after=3s", "9s", "bash",
                                 str(REPO / "ports/Silent Hill 3.sh")],
                                env=env, capture_output=True, text=True, timeout=20)
        logs = (self.port / "runs/game-hotkey/stderr.txt").read_text()
        for phase in [1, 2, 3]:
            self.assertIn(f"virtual pad phase={phase}", logs, logs[-8000:])
        self.assertEqual(result.returncode, 0, logs[-8000:])
        if scripted:
            self.assertIn("ExitProcess(0)", logs)
        else:
            self.assertNotIn("CreateDevice", logs, "combo must close launcher before starting game")
        self.assertIn("frontend ready", result.stdout)

    def test_select_start_also_exits_upstream_launcher(self):
        self.check_exit_combo(scripted=False)

    def test_owner_game_presents_640x480_frame_from_separate_writable_session(self):
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        shutil.copyfile(os.environ["SH3_RUNTIME_BINARY"], runtime)
        runtime.chmod(0o755)
        out = Path(os.environ["SH3_GAME_REFERENCE_OUT"])
        out.mkdir(parents=True, exist_ok=True)
        shots = out / "shots"
        shots.mkdir(exist_ok=True)
        seconds = int(os.environ.get("SH3_REFERENCE_SECONDS", "6"))
        checkpoint = seconds > 6
        env = {**os.environ, "SH3_MODE": "game", "SH3_PORT_ROOT": str(self.port),
               "SH3_DATA_DIR": os.environ["SH3_GAME_DATA"], "SH3_RUN_ID": "game-reference",
               "SH3_PACKAGE_DIR": str(REPO), "XDG_DATA_HOME": str(self.root / "xdg"),
               "SH3_KEYS": "2:Return+0.4,5:Return+0.4,10:Return+0.4,15:Return+0.4,20:Return+0.4,"
                           "25:Return+0.4,30:Return+0.4,35:Return+0.4,40:Return+0.4,45:Return+0.4,"
                           "50:Return+0.4,55:Return+0.4,75:Escape+0.4,85:Up+3,90:Right+2",
               "SH3_GL_BACKEND": "desktop", "SDL_VIDEODRIVER": "offscreen",
               "SDL_AUDIODRIVER": "dummy", "LIBGL_ALWAYS_SOFTWARE": "1",
               "SH3_PRESENT_DUMP": str(out / "present.ppm"), "SH3_STATS": "1",
               "SH3_INTERNAL_RESOLUTION": "640x480",
               "SH3_PEEK": "72BFD0,72BFD4",
               "SH3_SHOT": str(shots), "SH3_SHOT_EVERY": "300" if checkpoint else "1",
               "SH3_QUIT_AFTER": str(seconds)}
        if checkpoint:
            env.pop("SH3_PRESENT_DUMP")
        if os.environ.get("SH3_REFERENCE_SEED"):
            env["SH3_SEED_SESSION"] = os.environ["SH3_REFERENCE_SEED"]
            env["SH3_KEYS"] = "10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4,75:S+4"
            env["SH3_PEEK"] = "72BFD0,72BFD4,72D2C0,8984E0,8984E8,898660"
        with (out / "stdout.txt").open("w") as stdout, (out / "stderr.txt").open("w") as stderr:
            result = subprocess.run(["timeout", "--kill-after=3s", f"{seconds + 6}s", "bash",
                                     str(REPO / "ports/Silent Hill 3.sh")],
                                    env=env, stdout=stdout, stderr=stderr, timeout=seconds + 30)
        (out / "exit-status.txt").write_text(str(result.returncode) + "\n")
        run = self.port / "runs/game-reference"
        if run.exists():
            shutil.copytree(run, out / "launcher")
        logs = (run / "stderr.txt").read_text()
        self.assertEqual(result.returncode, 0, logs[-8000:])
        self.assertIn("frontend ready", (out / "stdout.txt").read_text())
        self.assertIn("CreateDevice 640x480", logs, logs[-8000:])
        self.assertRegex(logs, r"0072BFD0=00000280 0072BFD4=000001E0",
                         "scene rendering must initialize at 640x480, independently of output")
        self.assertNotIn("FATAL", logs, logs[-8000:])
        capture = out / "present.ppm"
        sequence = sorted(shots.glob("frame*.ppm"))
        if checkpoint and sequence:
            capture = sequence[-1]
        self.assertTrue(capture.is_file(), logs[-8000:])
        header = capture.read_bytes().split(b"\n", 3)
        self.assertEqual(header[:3], [b"P6", b"640 480", b"255"])
        self.assertEqual(len(header[3]), 640 * 480 * 3)
        self.assertGreater(len(set(header[3])), 32, "presented image lacks game content")
        self.assertGreater(len(sequence), 10, "sequence stops after startup frames")
        last = sequence[-1].read_bytes()
        prefix = re.match(rb"P6\s+(\d+)\s+(\d+)\s+255\s", last)
        self.assertIsNotNone(prefix)
        self.assertEqual(prefix.groups(), (b"640", b"480"))
        if not checkpoint:
            self.assertEqual(last[prefix.end():], header[3], "sequence must show same upright window image")


if __name__ == "__main__":
    unittest.main()
