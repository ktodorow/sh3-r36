"""Opt-in saved-checkpoint desktop reference through public host workflow."""
import hashlib
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


if __name__ == "__main__":
    unittest.main()
