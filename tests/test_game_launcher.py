"""Actual owner game through launcher in ARM64 Docker; never hardware acceptance."""
import os
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from test_preflight import LauncherFixture, REPO


@unittest.skipUnless(os.environ.get("SH3_GAME_DATA"), "requires read-only owner data in ARM64 Docker")
class GameLauncherTests(LauncherFixture):
    def test_graphics_options_persist_without_saving_game_progress(self):
        """Real Options -> 512x256 -> Exit/Yes -> Select+Start -> cold launch."""
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        shutil.copyfile(os.environ["SH3_RUNTIME_BINARY"], runtime)
        runtime.chmod(0o755)
        pad = self.root / "virtual-exit-pad.so"
        subprocess.run(["cc", "-shared", "-fPIC", str(REPO / "tests/virtual-exit-pad.c"),
                        "-o", str(pad), "-lSDL2", "-ldl"], check=True)
        evidence = Path(os.environ["SH3_GAME_REFERENCE_OUT"]).parent / "game-graphics-options"
        evidence.mkdir()
        env = {**os.environ, "SH3_MODE": "game", "SH3_PORT_ROOT": str(self.port),
               "SH3_DATA_DIR": os.environ["SH3_GAME_DATA"], "SH3_PACKAGE_DIR": str(REPO),
               "XDG_DATA_HOME": str(self.root / "xdg"), "SH3_GL_BACKEND": "desktop",
               "SDL_VIDEODRIVER": "offscreen", "SDL_AUDIODRIVER": "dummy",
               "LIBGL_ALWAYS_SOFTWARE": "1", "SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS": "1"}
        menu = "10:Return+0.4,26:Down+0.2,28:Down+0.2,30:Return+0.4,33:D+0.2,36:D+0.2"
        for run, seconds, keys in [
            ("choose", 57, menu + ",39:S+0.2,41:Left+0.2,43:Up+0.2,45:Up+0.2,47:Return+0.2,52:Return+0.2"),
            ("reload", 42, menu),
        ]:
            shots = evidence / run / "shots"
            shots.mkdir(parents=True)
            current = {**env, "SH3_RUN_ID": run, "SH3_KEYS": keys,
                       "SH3_SHOT": str(shots), "SH3_SHOT_EVERY": "60"}
            if run == "choose":
                current.update(LD_PRELOAD=str(pad), SH3_TEST_EXIT_AFTER=str(seconds))
                current.pop("SH3_QUIT_AFTER", None)
            else:
                current["SH3_QUIT_AFTER"] = str(seconds)
            result = subprocess.run(["timeout", "--kill-after=3s", f"{seconds + 8}s", "bash",
                                     str(REPO / "ports/Silent Hill 3.sh")],
                                    env=current, capture_output=True, text=True, timeout=seconds + 20)
            shutil.copytree(self.port / "runs" / run, evidence / run / "launcher")
            self.assertEqual(result.returncode, 0, result.stderr[-8000:])
            self.assertIn("frontend ready", result.stdout)
            if run == "choose":
                self.assertIn("window close requested: Select+Start", result.stderr)
            display = self.port / "state/savedata/disp.ini"
            self.assertTrue(display.is_file(), "confirmed game Options must create display preferences")
            values = dict(line.split("=", 1) for line in display.read_text().splitlines() if "=" in line)
            self.assertEqual(values.get("resolution"), "512x256",
                             "confirmed rendering choice must survive clean exit and cold launch, without a save")
            self.assertFalse(list((self.port / "state/savedata").glob("data.[0-9][0-9][0-9]")),
                             "graphics preferences must persist independently of progression saves")

    def test_failed_native_options_save_preserves_previous_preferences(self):
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        shutil.copyfile(os.environ["SH3_RUNTIME_BINARY"], runtime.with_name("native"))
        runtime.with_name("native").chmod(0o755)
        runtime.write_text('''#!/usr/bin/python3
import os, resource, signal, subprocess, sys
from pathlib import Path
def limit_writes():
    limit = int(os.environ.get('SH3_TEST_FILE_LIMIT', '0'))
    if limit:
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
child = subprocess.Popen([str(Path(__file__).with_name('native')), *sys.argv[1:]],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=limit_writes)
for line in child.stdout:
    sys.stderr.buffer.write(line)
    sys.stderr.flush()
sys.exit(child.wait())
''')
        runtime.chmod(0o755)
        pad = self.root / "options-input.so"
        subprocess.run(["cc", "-shared", "-fPIC", str(REPO / "tests/virtual-options-input.c"),
                        "-o", str(pad), "-lSDL2", "-ldl"], check=True)
        config = self.port / "state/sh3.ini"
        config.parent.mkdir()
        config.write_text("; user preferences\nresolution=640x480\ncores=3\n")
        evidence = Path(os.environ["SH3_GAME_REFERENCE_OUT"]).parent / "native-options-failure"
        evidence.mkdir()
        for run, limit in [("options-saved", "0"), ("options-failed", "4")]:
            result = self.launch(SH3_MODE="game", SH3_DATA_DIR=os.environ["SH3_GAME_DATA"],
                                 SH3_RUN_ID=run, SH3_LAUNCHER="1", SH3_KEYS="",
                                 SH3_GL_BACKEND="desktop", SDL_VIDEODRIVER="offscreen",
                                 SDL_AUDIODRIVER="dummy", LIBGL_ALWAYS_SOFTWARE="1",
                                 SH3_TEST_FILE_LIMIT=limit, LD_PRELOAD=str(pad))
            shutil.copytree(self.port / "runs" / run, evidence / run)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr[-6000:])
            self.assertIn("options fixture step=6", result.stderr)
            self.assertEqual(config.read_text(), "; user preferences\nresolution=640x480\ncores=1\n",
                             "failed option write must retain successful previous choice and comments")
        self.assertIn("previous settings kept", result.stderr)
        self.assertIn("File too large", result.stderr)

    def test_game_exit_preserves_display_preferences_for_cold_restart(self):
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        shutil.copyfile(os.environ["SH3_RUNTIME_BINARY"], runtime)
        runtime.chmod(0o755)
        display = self.port / "state/savedata/disp.ini"
        display.parent.mkdir(parents=True)
        preferences = ("format=D3DFMT_A8R8G8B8\ngamma_b=1\ngamma_g=1\ngamma_r=0.875\n"
                       "lensflare_ztest=1\nmode=fullscreen\nshadow=1\nsize=640x480\n"
                       "resolution=640x480\n")
        display.write_text(preferences)
        result = self.launch(SH3_MODE="game", SH3_DATA_DIR=os.environ["SH3_GAME_DATA"],
                             SH3_KEYS="", SH3_GL_BACKEND="desktop", SDL_VIDEODRIVER="offscreen",
                             SDL_AUDIODRIVER="dummy", LIBGL_ALWAYS_SOFTWARE="1", SH3_QUIT_AFTER="6")
        out = Path(os.environ["SH3_GAME_REFERENCE_OUT"]).parent / "display-persistence"
        shutil.copytree(self.port / "runs/fixture", out)
        self.assertEqual(result.returncode, 0, result.stderr[-8000:])
        self.assertIn("frontend ready", result.stdout)
        self.assertIn("gamma_r=0.875", display.read_text(),
                      "normal port exit must retain last valid display preferences")
        self.assertIn("resolution=640x480", display.read_text())

    def test_input_trace_observes_button_mapped_digital_triggers_through_real_game(self):
        self.check_exit_combo(scripted=True, input_matrix=True)

    def test_select_start_exits_actual_game_but_either_button_alone_does_not(self):
        self.check_exit_combo(scripted=True)

    def check_exit_combo(self, scripted, input_matrix=False):
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
        if input_matrix:
            env.update(SH3_INPUT_LOG="1", SH3_TEST_INPUT_MATRIX="1")
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
        if input_matrix:
            self.assertRegex(logs, r"input controller mapping=.*lefttrigger:b6.*righttrigger:b7",
                             "native trace must record applied SDL mapping")
            self.assertRegex(logs, r"input state ticks=\d+ axes=0,0,0,0,32767,0 buttons=040 pov=-1",
                             "digital L2 must reach game's search-view button")
            self.assertRegex(logs, r"input state ticks=\d+ axes=0,0,0,0,0,32767 buttons=080 pov=-1",
                             "digital R2 must reach game's ready-weapon button")
        else:
            self.assertNotIn("input state ticks=", logs, "ordinary launches must keep input trace disabled")

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
        if os.environ.get("SH3_REFERENCE_SCENE"):
            plan = json.loads((REPO / "scripts/scenes.json").read_text())[os.environ["SH3_REFERENCE_SCENE"]]
            seconds = plan["seconds"]
            checkpoint = True
            env.pop("SH3_PRESENT_DUMP", None)
            env.update(SH3_KEYS=plan["keys"], SH3_QUIT_AFTER=str(seconds),
                       SH3_SHOT_EVERY=str(plan["capture_every"]), SH3_PEEK=plan["peek"])
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
        captured = re.findall(r"capture frame (\d+) ticks (\d+) output (\d+)x(\d+) backbuffer (\d+)x(\d+)", logs)
        self.assertEqual({int(row[0]) for row in captured},
                         {int(path.stem.removeprefix("frame")) for path in sequence},
                         "every scene image needs time and dimensions for matched comparisons")
        self.assertTrue(all(row[2:] == ("640", "480", "640", "480") for row in captured))
        self.assertEqual([int(row[1]) for row in captured], sorted(int(row[1]) for row in captured))
        last = sequence[-1].read_bytes()
        prefix = re.match(rb"P6\s+(\d+)\s+(\d+)\s+255\s", last)
        self.assertIsNotNone(prefix)
        self.assertEqual(prefix.groups(), (b"640", b"480"))
        if not checkpoint:
            self.assertEqual(last[prefix.end():], header[3], "sequence must show same upright window image")


if __name__ == "__main__":
    unittest.main()
