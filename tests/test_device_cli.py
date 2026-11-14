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
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="device-cli-", dir=REPO / ".port-cache")
        self.addCleanup(self.temp.cleanup)
        root = self.root = Path(self.temp.name)
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
        source = self.source = root / "player"
        (source / "savedata").mkdir(parents=True)
        contents = self.contents = {"savedata/data.001": b"first slot", "savedata/data.002": b"second slot",
                    "savedata/data.sys": b"index", "savedata/key.ini": b"mapping",
                    "sh3.ini": b"cores=1\n", "sh3-progs.bin": b"cache",
                    "sh3-gl-cache.bin": b"compiled driver programs"}
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

    def run_workflow(self, *options):
        return subprocess.run(["python3", str(self.root / "scripts/host/r36s.py"), "game",
                                 *options, "--reviewed-helpers", str(self.root / "review")], cwd=self.root,
                                env={**os.environ, "PATH": f"{self.root / 'bin'}:{os.environ['PATH']}",
                                     "FIXTURE_ROOT": str(self.root), "GIT_DIR": str(REPO / ".git"),
                                     "GIT_WORK_TREE": str(self.root), "GIT_OPTIONAL_LOCKS": "0"},
                                capture_output=True, text=True, timeout=20)

    def test_persistent_import_deploys_all_player_slots_and_collects_failed_deployment(self):
        root, source, contents = self.root, self.source, self.contents
        result = self.run_workflow("--persistent-state", "--import-session", str(source))
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

    def test_handheld_profile_deploys_selected_resolution_and_collects_failed_deployment(self):
        for resolution in ("320x240", "640x480"):
            with self.subTest(resolution=resolution):
                result = self.run_workflow("--physical-profile", resolution)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                deployed = json.loads((self.root / "deployed.json").read_text())
                self.assertIn("physical-controls", deployed)
                self.assertEqual(deployed.get("physical-profile"),
                                 hashlib.sha256((resolution + "\n").encode()).hexdigest())
                self.assertNotIn("persistent-state", deployed)
                self.assertFalse(any(name.startswith("import-state/") for name in deployed))
                statuses = sorted((self.root / "r36s-dumps/sh3").glob("*/status.json"))
                status = json.loads(statuses[-1].read_text())
                self.assertEqual(status["physical_profile"], resolution)
                self.assertEqual(status["execution"], "deployment-failed")
                self.assertEqual(status["collection"], 42)
        self.assertEqual((self.root / "collection-attempts.txt").read_text().splitlines(), ["attempted"] * 6)

    def test_handheld_profile_rejects_conflicting_state_and_replay_before_deployment(self):
        for conflict in (("--persistent-state",), ("--import-session", str(self.source)),
                         ("--scene", "profile-static-320")):
            with self.subTest(conflict=conflict):
                result = self.run_workflow("--physical-profile", "320x240", *conflict)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("requires game action without scene replay" if "--scene" in conflict
                              else "uses isolated state", result.stderr)
                self.assertFalse((self.root / "deployed.json").exists())
                self.assertFalse((self.root / "collection-attempts.txt").exists())

    def test_unattended_route_deploys_movement_combat_and_frame_profile_without_capture(self):
        result = self.run_workflow("--scene", "performance-route-320", "--seed-session", str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity_path = next((self.root / "r36s-dumps/sh3").glob("*/scene-identity.json"))
        identity = json.loads(identity_path.read_text())
        plan = identity["plan"]
        self.assertEqual(plan["internal_resolution"], "320x240")
        self.assertEqual(plan["fps_limit"], 30)
        self.assertIs(plan["profile"], True)
        self.assertEqual(plan["capture_every"], 0)
        self.assertGreaterEqual(plan["seconds"], 180)
        for action in (":S+", ":W+", ":A+", ":D+", ":B+", ":Space+"):
            self.assertIn(action, plan["keys"], "route must exercise walking, turning and attacks")
        deployed = json.loads((self.root / "deployed.json").read_text())
        self.assertIn("scene-plan.json", deployed)
        self.assertNotIn("physical-controls", deployed)
        self.assertEqual(deployed["scene-seed/sh3-gl-cache.bin"],
                         hashlib.sha256(self.contents["sh3-gl-cache.bin"]).hexdigest())
        self.assertEqual(deployed["scene-seed/savedata/data.001"],
                         hashlib.sha256(self.contents["savedata/data.001"]).hexdigest())
        self.assertEqual((self.source / "savedata/data.001").read_bytes(),
                         self.contents["savedata/data.001"])

    def test_full_resolution_route_deploys_paced_movement_and_combat_for_fallback_comparison(self):
        result = self.run_workflow("--scene", "performance-route-640", "--seed-session", str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity_path = next((self.root / "r36s-dumps/sh3").glob("*/scene-identity.json"))
        identity = json.loads(identity_path.read_text())
        plan = identity["plan"]
        self.assertEqual(plan["internal_resolution"], "640x480")
        self.assertEqual(plan["fps_limit"], 30)
        self.assertIs(plan["profile"], True)
        self.assertEqual(plan["capture_every"], 0)
        self.assertGreaterEqual(plan["seconds"], 180)
        for action in (":S+", ":W+", ":A+", ":D+", ":B+", ":Space+"):
            self.assertIn(action, plan["keys"])
        for address in ("72D2C0", "8984E0", "8984E8", "898660", "72BFD0", "72BFD4"):
            self.assertIn(address, plan["peek"], "comparison needs actual scene, movement and render size")
        deployed = json.loads((self.root / "deployed.json").read_text())
        self.assertIn("scene-plan.json", deployed)
        self.assertNotIn("physical-controls", deployed)
        self.assertEqual(deployed["scene-seed/savedata/data.001"],
                         hashlib.sha256(self.contents["savedata/data.001"]).hexdigest())
        self.assertTrue(identity["source_preserved"])

    def test_program_cache_prime_deploys_only_compiled_programs_without_importing_progress(self):
        cache = self.root / "measured-programs.bin"
        contents = (0x53484231).to_bytes(4, "little") + (4).to_bytes(4, "little") + b"Mali"
        cache.write_bytes(contents)
        result = self.run_workflow("--scene", "traverse-route-320", "--seed-session", str(self.source),
                                   "--prime-program-cache", str(cache))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        deployed = json.loads((self.root / "deployed.json").read_text())
        self.assertEqual(deployed["performance-cache/sh3-gl-cache.bin"], hashlib.sha256(contents).hexdigest())
        self.assertFalse(any(name.startswith("import-state/") for name in deployed))
        self.assertNotIn("persistent-state", deployed)
        self.assertEqual(cache.read_bytes(), contents)

    def test_program_cache_prime_rejects_invalid_or_oversized_files_before_device_access(self):
        cache = self.root / "invalid-programs.bin"
        for contents in (b"", b"wrong cache", (0x53484231).to_bytes(4, "little") +
                         (100).to_bytes(4, "little") + b"short", None):
            with self.subTest(contents=contents):
                if contents is None:
                    with cache.open("wb") as out:
                        out.truncate(32 * 1024 * 1024 + 1)
                else:
                    cache.write_bytes(contents)
                result = self.run_workflow("--prime-program-cache", str(cache))
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("Invalid compiled program cache", result.stderr)
                self.assertFalse((self.root / "deployed.json").exists())
                self.assertFalse((self.root / "collection-attempts.txt").exists())

    def test_cross_level_route_uses_checkpoint_load_and_movement_without_inventory_assumptions(self):
        result = self.run_workflow("--scene", "traverse-route-320", "--seed-session", str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity_path = next((self.root / "r36s-dumps/sh3").glob("*/scene-identity.json"))
        plan = json.loads(identity_path.read_text())["plan"]
        self.assertEqual(plan["fps_limit"], 30)
        self.assertIs(plan["profile"], True)
        self.assertEqual(plan["capture_every"], 0)
        for action in (":Return+", ":S+", ":W+", ":A+", ":D+", ":B+", ":Space+"):
            self.assertIn(action, plan["keys"])
        self.assertNotIn(":I+", plan["keys"], "save-specific inventory layout must not drive generic route")
        self.assertIn("8984E0", plan["peek"], "route needs actual player motion evidence")
        self.assertIn("72D2C0", plan["peek"], "route needs actual loaded room evidence")

    def test_sustained_route_keeps_active_inputs_and_profile_through_fifteen_minutes(self):
        result = self.run_workflow("--scene", "sustained-route-320", "--seed-session", str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity_path = next((self.root / "r36s-dumps/sh3").glob("*/scene-identity.json"))
        plan = json.loads(identity_path.read_text())["plan"]
        self.assertGreaterEqual(plan["seconds"], 900)
        self.assertEqual(plan["fps_limit"], 30)
        self.assertIs(plan["profile"], True)
        self.assertEqual(plan["capture_every"], 0)
        self.assertNotIn(":I+", plan["keys"])
        late = [event for event in plan["keys"].split(',') if float(event.split(':')[0]) >= 840]
        for action in (":W+", ":S+", ":A+", ":D+", ":B+", ":Space+"):
            self.assertTrue(any(action in event for event in late), 'late run lacks ' + action)
        for address in ("72D2C0", "8984E0", "8984E8", "898660"):
            self.assertIn(address, plan["peek"], 'sustained verdict needs room, movement and live-state evidence')
        self.assertTrue(json.loads(identity_path.read_text())["source_preserved"])
        self.assertEqual((self.source / "savedata/data.001").read_bytes(),
                         self.contents["savedata/data.001"])

    def test_exploration_route_attempts_long_walks_and_doors_without_readied_weapon(self):
        result = self.run_workflow("--scene", "explore-route-320", "--seed-session", str(self.source))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        identity_path = next((self.root / "r36s-dumps/sh3").glob("*/scene-identity.json"))
        identity = json.loads(identity_path.read_text())
        plan = identity["plan"]
        self.assertEqual(plan["internal_resolution"], "320x240")
        self.assertEqual(plan["fps_limit"], 30)
        self.assertIs(plan["profile"], True)
        self.assertEqual(plan["capture_every"], 0)
        events = [event.split(':', 1)[1].split('+') for event in plan["keys"].split(',')]
        self.assertTrue(any(key in ('W', 'S') and float(hold) >= 10 for key, hold in events),
                        'exploration must reach beyond short back-and-forth traversal')
        self.assertGreaterEqual(sum(key == 'Space' for key, hold in events), 4,
                                'door interaction needs repeated action attempts')
        self.assertNotIn(':B+', plan['keys'], 'ready weapon changes action from door interaction to attack')
        self.assertNotIn(':I+', plan['keys'], 'generic exploration cannot assume inventory layout')
        for address in ("72D2C0", "8984E0", "8984E8", "898660"):
            self.assertIn(address, plan["peek"])
        self.assertTrue(identity["source_preserved"])


if __name__ == "__main__":
    unittest.main()
