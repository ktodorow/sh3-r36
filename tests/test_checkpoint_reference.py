"""Opt-in saved-checkpoint desktop reference through public host workflow."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("SH3_DESKTOP_CHECKPOINT"), "requires collected owner checkpoint and ARM64 Docker")
class CheckpointReferenceTests(unittest.TestCase):
    def test_reference_replays_physical_checkpoint_without_changing_source(self):
        seed = Path(os.environ["SH3_DESKTOP_CHECKPOINT"]).resolve()
        originals = {path: hashlib.sha256(path.read_bytes()).digest()
                     for path in (seed / "savedata").iterdir() if path.is_file()}
        result = subprocess.run([sys.executable, str(REPO / "scripts/host/test-runtime.py"),
                                 "--checkpoint", "--seed-session", str(seed)],
                                cwd=REPO, capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        evidence = re.search(r"Evidence: (.+)", result.stdout)
        self.assertIsNotNone(evidence, result.stdout)
        logs = (REPO / evidence[1] / "game-reference/launcher/stderr.txt").read_text()
        self.assertRegex(logs, r"0072BFD0=00000280 0072BFD4=000001E0 0072D2C0=000000D2")
        self.assertIn("008984E0=C66B4B22 008984E8=46973350", logs)
        for path, digest in originals.items():
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), digest, path.name)


@unittest.skipUnless(os.environ.get("SH3_DESKTOP_SCENE"), "requires collected checkpoint and ARM64 Docker")
class SceneReferenceTests(unittest.TestCase):
    def test_named_scene_keeps_replay_identity_and_source_checkpoint(self):
        seed = Path(os.environ["SH3_DESKTOP_SCENE"]).resolve()
        scene = os.environ.get("SH3_DESKTOP_SCENE_NAME", "checkpoint-ui")
        room = int(os.environ.get("SH3_DESKTOP_SCENE_ROOM", "210"))
        original = hashlib.sha256((seed / "savedata/data.001").read_bytes()).hexdigest()
        result = subprocess.run([sys.executable, str(REPO / "scripts/host/test-runtime.py"),
                                 "--scene", scene, "--seed-session", str(seed)],
                                cwd=REPO, capture_output=True, text=True, timeout=210)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        evidence = REPO / re.search(r"Evidence: (.+)", result.stdout)[1]
        identity = json.loads((evidence / "scene-identity.json").read_text())
        self.assertEqual(identity["scene"], scene)
        self.assertEqual(identity["seed_sha256"]["savedata/data.001"], original)
        self.assertEqual(identity["runtime_sha256"], hashlib.sha256((REPO / "dist/runtime/sh3").read_bytes()).hexdigest())
        self.assertTrue(identity["source_preserved"])
        logs = (evidence / "game-reference/launcher/stderr.txt").read_text()
        self.assertIn(f"0072D2C0={room:08X}", logs, "checkpoint scene not reached")
        self.assertIn("ExitProcess(0)", logs)
        self.assertIn("capture frame", logs)
        self.assertEqual(hashlib.sha256((seed / "savedata/data.001").read_bytes()).hexdigest(), original)


@unittest.skipUnless(os.environ.get("SH3_OPENING_REFERENCE"), "requires owner data and ARM64 Docker")
class OpeningReferenceTests(unittest.TestCase):
    def test_opening_cutscene_uses_fresh_session_without_seeded_checkpoint(self):
        if os.environ.get("SH3_OPENING_REFERENCE_EVIDENCE"):
            run = REPO / os.environ["SH3_OPENING_REFERENCE_EVIDENCE"]
        else:
            result = subprocess.run([sys.executable, str(REPO / "scripts/host/test-runtime.py"),
                                     "--scene", "opening-cutscene"],
                                    cwd=REPO, capture_output=True, text=True, timeout=360)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run = REPO / re.search(r"Evidence: (.+)", result.stdout)[1]
        identity = json.loads((run / "scene-identity.json").read_text())
        self.assertEqual(identity["scene"], "opening-cutscene")
        self.assertEqual(identity["seed_sha256"], {})
        self.assertFalse((run / "game-reference/launcher/session/savedata/data.001").exists())
        logs = (run / "game-reference/launcher/stderr.txt").read_text()
        self.assertIn("0072D2C0=000000D2", logs, "fresh opening did not reach park")
        poses = re.findall(r"0072D2C0=000000D2 008984E0=([0-9A-F]{8}) 008984E8=([0-9A-F]{8})", logs)
        self.assertTrue(any(x not in {"00000000", "80000000"} and z not in {"00000000", "80000000"}
                            for x, z in poses), "opening window ends before live player pose is initialized")
        self.assertIn("ExitProcess(0)", logs)


if __name__ == "__main__":
    unittest.main()
