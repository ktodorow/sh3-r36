"""Saved host workflow; SSH/SCP process fixtures never establish device acceptance."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless((REPO / "SILENT HILL 3/sh3.exe").is_file(), "requires ignored owner installation")
class DeviceCliTests(unittest.TestCase):
    def test_persistent_import_deploys_all_player_slots_and_collects_failed_deployment(self):
        with tempfile.TemporaryDirectory(prefix="device-cli-", dir=REPO / ".port-cache") as temp:
            root = Path(temp)
            spec = importlib.util.spec_from_file_location("device_workflow", REPO / "scripts/host/r36s.py")
            workflow = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(workflow)
            for name in [*workflow.FILES, "scripts/host/r36s.py", "scripts/host/scenes.py",
                         "scripts/host/ssh-askpass.sh", ".gitignore"]:
                dest = root / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO / name, dest)
            (root / ".env").write_text("R36S_PORT=sh3\nR36S_HOST=fixture.invalid\nSH3_GAME_DIR=" +
                                       shlex.quote(str(REPO / "SILENT HILL 3")) + "\n")
            runtime = root / "dist/runtime"
            runtime.mkdir(parents=True)
            binary = bytearray(20)
            binary[:6] = b"\x7fELF\x02\x01"
            binary[18:20] = (183).to_bytes(2, "little")
            (runtime / "sh3").write_bytes(binary)
            owner = REPO / "SILENT HILL 3/sh3.exe"
            (runtime / "build-inputs.json").write_text(json.dumps({"input_sha1": hashlib.sha1(owner.read_bytes()).hexdigest()}))
            for name in ["packages.txt", "compiler.txt", "libc.txt", "python.txt", "elf.txt", "readelf.txt", "artifacts.sha256"]:
                (runtime / name).touch()
            review = root / "review/device"
            review.mkdir(parents=True)
            (review / "portmaster-files.sha256").write_text("fixture reviewed helpers\n")
            source = root / "player"
            (source / "savedata").mkdir(parents=True)
            contents = {"savedata/data.001": b"first slot", "savedata/data.002": b"second slot",
                        "savedata/data.sys": b"index", "savedata/key.ini": b"mapping",
                        "sh3.ini": b"cores=1\n", "sh3-progs.bin": b"cache"}
            for name, value in contents.items():
                (source / name).write_bytes(value)
            (source / "unrelated.txt").write_text("leave out")
            commands = root / "bin"
            commands.mkdir()
            (commands / "ssh").write_text("#!/bin/sh\nexit 0\n")
            (commands / "scp").write_text('''#!/usr/bin/env python3
import hashlib, json, os, pathlib, sys
source = pathlib.Path(sys.argv[-2])
root = pathlib.Path(os.environ['FIXTURE_ROOT'])
if source.is_dir():
    files = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in source.rglob('*') if p.is_file()}
    (root / 'deployed.json').write_text(json.dumps(files))
else:
    with (root / 'collection-attempts.txt').open('a') as out:
        out.write('attempted\\n')
sys.exit(42)
''')
            for command in commands.iterdir():
                command.chmod(0o755)
            result = subprocess.run(["python3", str(root / "scripts/host/r36s.py"), "game",
                                     "--persistent-state", "--import-session", str(source),
                                     "--reviewed-helpers", str(review.parent)], cwd=root,
                                    env={**os.environ, "PATH": f"{commands}:{os.environ['PATH']}",
                                         "FIXTURE_ROOT": str(root), "GIT_DIR": str(REPO / ".git"),
                                         "GIT_WORK_TREE": str(root), "GIT_OPTIONAL_LOCKS": "0"},
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            deployed = json.loads((root / "deployed.json").read_text())
            self.assertIn("persistent-state", deployed)
            self.assertIn("physical-controls", deployed)
            self.assertNotIn("scene-seed/savedata/data.001", deployed)
            self.assertNotIn("import-state/unrelated.txt", deployed)
            for name, value in contents.items():
                self.assertEqual(deployed["import-state/" + name], hashlib.sha256(value).hexdigest())
                self.assertEqual((source / name).read_bytes(), value)
            status = json.loads(next((root / "r36s-dumps/sh3").glob("*/status.json")).read_text())
            self.assertEqual(status["execution"], "deployment-failed")
            self.assertEqual(status["collection"], 42)
            self.assertTrue(status["source-preserved"])
            self.assertEqual((root / "collection-attempts.txt").read_text().splitlines(), ["attempted"] * 3)


if __name__ == "__main__":
    unittest.main()
