"""Installed game menu lifecycle; service manager is external fixture boundary."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

from test_preflight import LauncherFixture, REPO


OWNER = Path(os.environ.get("SH3_GAME_DATA", REPO / "SILENT HILL 3"))


@unittest.skipUnless((OWNER / "sh3.exe").is_file(), "requires original owner game data")
@unittest.skipUnless(Path("/proc/self/cgroup").is_file(), "requires Linux session boundary")
class FrontendSessionTests(LauncherFixture):
    def setUp(self):
        super().setUp()
        for name in ["sh3.exe", "data"]:
            (self.data / name).symlink_to(OWNER / name, target_is_directory=name == "data")
        installed = self.port / "preflight/ports"
        installed.mkdir(parents=True)
        for name in ["Silent Hill 3.sh", "game-session.sh", "restore-frontend.sh"]:
            source = REPO / "ports" / name
            if source.exists():
                shutil.copyfile(source, installed / name)
        self.menu = self.root / "Silent Hill 3 Game.sh"
        shutil.copyfile(REPO / "ports/Silent Hill 3 Game.sh", self.menu)
        self.commands = self.root / "bin"
        self.commands.mkdir()
        self.state = self.root / "frontend-state"
        self.state.write_text("active")
        self.trace = self.root / "service-trace"
        self.write_command("systemctl", '''#!/usr/bin/env python3
from pathlib import Path
import sys
root = Path(__file__).resolve().parent.parent
state = root / 'frontend-state'
action = sys.argv[1]
if action == 'is-active':
    sys.exit(0 if state.read_text() == 'active' else 3)
if action in ['stop', 'start']:
    with (root / 'service-trace').open('a') as trace: trace.write(action + '\\n')
    state.write_text('inactive' if action == 'stop' else 'active')
''')
        self.write_command("pgrep", '''#!/bin/sh
root="$(dirname "$(dirname "$0")")"
[ "$(cat "$root/frontend-state")" = active ] && { echo 123; exit 0; }
exit 1
''')
        self.write_command("sudo", '#!/bin/sh\n[ "$1" = -n ] && shift\nexec "$@"\n')
        self.write_command("systemd-run", '''#!/usr/bin/env python3
import json, os, shlex, signal, subprocess, sys, time
from pathlib import Path
root = Path(__file__).resolve().parent.parent
args = sys.argv[1:]
(root / 'unit-request.json').write_text(json.dumps(args))
env = {}
for arg in args:
    if arg.startswith('--setenv='):
        key, value = arg[len('--setenv='):].split('=', 1)
        env[key] = value
command = args[args.index('/bin/bash'):]
if (root / 'crash-service').exists():
    child = subprocess.Popen(command, env=env, start_new_session=True)
    for attempt in range(200):
        if (root / 'service-trace').exists() and 'runtime' in (root / 'service-trace').read_text(): break
        time.sleep(0.01)
    os.killpg(child.pid, signal.SIGKILL)
    status = child.wait()
else:
    status = subprocess.run(command, env=env).returncode
recovery = next(arg.split('=', 2)[2] for arg in args if arg.startswith('--property=ExecStopPost='))
restored = subprocess.run(shlex.split(recovery.lstrip('+')), env=env).returncode
sys.exit((128 - status if status < 0 else status) or restored)
''')
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        runtime.write_text('''#!/bin/sh
root="$(dirname "$(dirname "$(dirname "$0")")")"
[ "$(cat "$root/frontend-state")" = inactive ] || exit 9
printf 'runtime\\n' >> "$root/service-trace"
exit 7
''')
        runtime.chmod(0o755)

    def write_command(self, name, contents):
        path = self.commands / name
        path.write_text(contents)
        path.chmod(0o755)

    def launch_menu(self):
        return subprocess.run(["bash", str(self.menu)], cwd="/", capture_output=True, text=True,
                              timeout=20, env={**os.environ,
                                  "PATH": f"{self.commands}:{os.environ['PATH']}",
                                  "XDG_DATA_HOME": str(self.root / "xdg"),
                                  "SH3_PACKAGE_DIR": str(REPO), "SH3_RUN_ID": "service-fixture",
                                  "SH3_SERVICE_WAIT": "1"})

    def test_game_runs_outside_frontend_service_and_failure_restores_frontend(self):
        result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertEqual(self.trace.read_text().splitlines(), ["stop", "runtime", "start"])
        self.assertEqual(self.state.read_text(), "active")
        self.assertEqual(self.save.read_bytes(), b"owner save remains unchanged")
        request = json.loads((self.root / "unit-request.json").read_text())
        self.assertIn("--unit=sh3-r36s-game", request)
        self.assertTrue(any("ExecStopPost=" in arg for arg in request), "crash recovery required")
        self.assertFalse(list(self.port.glob("runs/*/frontend-stopped")))

    def test_previously_inactive_frontend_is_left_inactive(self):
        self.state.write_text("inactive")
        result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertEqual(self.trace.read_text().splitlines(), ["runtime"])
        self.assertEqual(self.state.read_text(), "inactive")

    def test_checkpoint_and_requested_render_profile_reach_detached_game(self):
        seed = self.root / "seed-session/savedata"
        seed.mkdir(parents=True)
        (seed / "data.001").write_text("checkpoint one\n")
        (seed / "data.sys").write_text("checkpoint index\n")
        runtime = self.port / "runtime/sh3"
        runtime.write_text(runtime.read_text().replace("exit 7", '''cat savedata/data.001
cat savedata/disp.ini
printf '%s\\n' "$SH3_PEEK"
exit 7'''))
        with patch.dict(os.environ, {"SH3_SEED_SESSION": str(seed.parent),
                                    "SH3_INTERNAL_RESOLUTION": "640x480",
                                    "SH3_PEEK": "72BFD0,72BFD4"}):
            result = self.launch_menu()
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        log = (self.port / "runs/service-fixture/stdout.txt").read_text()
        self.assertIn("checkpoint one\n", log)
        self.assertIn("resolution=640x480\n", log)
        self.assertIn("72BFD0,72BFD4\n", log)
        self.assertEqual((seed / "data.001").read_text(), "checkpoint one\n")
        self.assertEqual(self.state.read_text(), "active")

    def test_service_stop_post_restores_frontend_when_session_cannot_run_exit_trap(self):
        (self.root / "crash-service").touch()
        runtime = self.port / "runtime/sh3"
        runtime.write_text(runtime.read_text().replace("exit 7", "sleep 30"))
        result = self.launch_menu()
        self.assertEqual(result.returncode, 137, result.stdout + result.stderr)
        self.assertEqual(self.trace.read_text().splitlines(), ["stop", "runtime", "start"])
        self.assertEqual(self.state.read_text(), "active")
        self.assertFalse(list(self.port.glob("runs/*/frontend-stopped")))


if __name__ == "__main__":
    unittest.main()
