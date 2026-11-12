"""Opt-in named scene through saved host workflow and installed R36S launcher."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("SH3_R36S_SCENE_SEED"), "requires R36S and reviewed helpers")
class DeviceSceneTests(unittest.TestCase):
    def test_named_scene_records_matched_plan_and_preserves_checkpoint(self):
        seed = Path(os.environ["SH3_R36S_SCENE_SEED"]).resolve()
        scene = os.environ.get("SH3_R36S_SCENE_NAME", "checkpoint-ui")
        room = int(os.environ.get("SH3_R36S_SCENE_ROOM", "210"))
        original = hashlib.sha256((seed / "savedata/data.001").read_bytes()).hexdigest()
        result = subprocess.run([sys.executable, str(REPO / "scripts/host/r36s.py"), "game",
                                 "--scene", scene, "--seed-session", str(seed),
                                 "--reviewed-helpers", os.environ["SH3_REVIEWED_HELPERS"]],
                                cwd=REPO, capture_output=True, text=True, timeout=330)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        run = REPO / re.search(r"Evidence: (.+)", result.stdout)[1]
        identity = json.loads((run / "scene-identity.json").read_text())
        self.assertEqual(identity["scene"], scene)
        self.assertTrue(identity["source_preserved"])
        self.assertEqual(identity["seed_sha256"]["savedata/data.001"], original)
        self.assertEqual(json.loads((run / "device/scene-plan.json").read_text()), identity["plan"])
        self.assertIn("OK", (run / "device/checkpoint-source-after.txt").read_text())
        logs = (run / "launcher/stderr.txt").read_text()
        self.assertIn("GL: Mali-G31 / OpenGL ES 3.2", logs)
        self.assertIn(f"0072D2C0={room:08X}", logs, "checkpoint scene not reached")
        self.assertRegex(logs, r"capture frame \d+ ticks \d+ output 640x480 backbuffer 640x480")
        self.assertIn("ExitProcess(0)", logs)
        self.assertIn("ActiveState=active", (run / "service/frontend-restored.txt").read_text())
        self.assertEqual(hashlib.sha256((seed / "savedata/data.001").read_bytes()).hexdigest(), original)


@unittest.skipUnless(os.environ.get("SH3_R36S_OPENING"), "requires R36S and reviewed helpers")
class DeviceOpeningTests(unittest.TestCase):
    def test_opening_scene_does_not_copy_latest_device_checkpoint(self):
        result = subprocess.run([sys.executable, str(REPO / "scripts/host/r36s.py"), "game",
                                 "--scene", "opening-cutscene", "--reviewed-helpers",
                                 os.environ["SH3_REVIEWED_HELPERS"]],
                                cwd=REPO, capture_output=True, text=True, timeout=480)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        run = REPO / re.search(r"Evidence: (.+)", result.stdout)[1]
        self.assertFalse((run / "launcher/session/savedata/data.001").exists())
        self.assertFalse((run / "device/checkpoint-seed").exists())
        self.assertEqual(json.loads((run / "scene-identity.json").read_text())["seed_sha256"], {})
        logs = (run / "launcher/stderr.txt").read_text()
        self.assertIn("GL: Mali-G31 / OpenGL ES 3.2", logs)
        self.assertIn("0072D2C0=000000D2", logs, "opening did not reach park")
        poses = re.findall(r"0072D2C0=000000D2 008984E0=([0-9A-F]{8}) 008984E8=([0-9A-F]{8})", logs)
        self.assertTrue(any(x not in {"00000000", "80000000"} and z not in {"00000000", "80000000"}
                            for x, z in poses), "opening window ends before live player pose is initialized")
        self.assertIn("ExitProcess(0)", logs)
        self.assertIn("ActiveState=active", (run / "service/frontend-restored.txt").read_text())


if __name__ == "__main__":
    unittest.main()
