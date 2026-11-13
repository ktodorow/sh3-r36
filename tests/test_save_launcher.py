"""Save failures through real owner game and launcher in ARM64 Docker."""
import os
from pathlib import Path
import shutil
import subprocess
import unittest

from test_preflight import LauncherFixture, REPO


@unittest.skipUnless(os.environ.get("SH3_REFERENCE_SEED"), "requires collected owner checkpoint in ARM64 Docker")
class SaveLauncherTests(LauncherFixture):
    def test_failed_quicksave_preserves_previous_valid_slot_and_reports_write_error(self):
        seed = Path(os.environ["SH3_REFERENCE_SEED"])
        savedata = self.port / "state/savedata"
        shutil.copytree(seed / "savedata", savedata)
        original = {p.name: p.read_bytes() for p in (seed / "savedata").iterdir() if p.is_file()}
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        shutil.copyfile(os.environ["SH3_RUNTIME_BINARY"], runtime.with_name("native"))
        runtime.with_name("native").chmod(0o755)
        # Actual kernel file-size failure. Pipes keep diagnostic output outside child's limit.
        runtime.write_text('''#!/usr/bin/python3
import os, resource, signal, subprocess, sys
from pathlib import Path
limit = int(os.environ.get('SH3_TEST_FILE_LIMIT', '0'))
def fail_large_writes():
    if limit:
        signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
        resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))
child = subprocess.Popen([str(Path(__file__).with_name('native')), *sys.argv[1:]],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         preexec_fn=fail_large_writes)
for line in child.stdout:
    sys.stderr.buffer.write(line)
    sys.stderr.flush()
sys.exit(child.wait())
''')
        runtime.chmod(0o755)
        out = Path(os.environ["SH3_GAME_REFERENCE_OUT"]).parent / "save-write-failure"
        out.mkdir()

        def play(run_id, limit=0):
            env = {**os.environ, "SH3_MODE": "game", "SH3_PORT_ROOT": str(self.port),
                   "SH3_DATA_DIR": os.environ["SH3_GAME_DATA"], "SH3_RUN_ID": run_id,
                   "SH3_PACKAGE_DIR": str(REPO), "XDG_DATA_HOME": str(self.root / "xdg"),
                   "SH3_KEYS": "10:Return+0.4,30:Down+0.2,32:Return+0.4,34:Return+0.4,36:Return+0.4,"
                               "55:Up+1,65:F5+0.4",
                   "SH3_GL_BACKEND": "desktop", "SDL_VIDEODRIVER": "offscreen",
                   "SDL_AUDIODRIVER": "dummy", "LIBGL_ALWAYS_SOFTWARE": "1",
                   "SH3_INTERNAL_RESOLUTION": "640x480", "SH3_QUIT_AFTER": "85",
                   "SH3_STATS": "1", "SH3_PEEK": "72D2C0,8984E0,8984E8,898660",
                   "SH3_TEST_FILE_LIMIT": str(limit)}
            result = subprocess.run(["bash", str(REPO / "ports/Silent Hill 3.sh")],
                                    env=env, capture_output=True, text=True, timeout=105)
            shutil.copytree(self.port / "runs" / run_id, out / run_id)
            self.assertEqual(result.returncode, 0, result.stderr[-8000:])
            self.assertIn("frontend ready", result.stdout)
            return result

        play("valid-save")
        valid = {p.name: p.read_bytes() for p in savedata.glob("data.[0-9][0-9][0-9]")}
        changed = {name: value for name, value in valid.items() if original.get(name) != value}
        self.assertTrue(changed, "normal game must create quicksave before testing failed overwrite")
        self.assertTrue(all(len(value) > 4096 for value in changed.values()))
        failed = play("failed-save", limit=4096)
        for name, value in changed.items():
            self.assertIn(f"savedata\\{name} access 40000000", failed.stderr,
                          "failure run must attempt overwrite through game save menu")
            self.assertEqual((savedata / name).read_bytes(), value,
                             "failed save must preserve previous complete slot")
        self.assertIn("File too large", failed.stderr)
        self.assertIn("previous file kept", failed.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in (seed / "savedata").iterdir() if p.is_file()}, original)


if __name__ == "__main__":
    unittest.main()
