#!/usr/bin/env python3
"""Run real ARM64 binary through agreed launcher seam inside reusable Docker image."""
from datetime import datetime, timezone
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

from r36s import ROOT, check_ignores, config


check_ignores()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--game", action="store_true", help="Include actual owner-game desktop comparison")
parser.add_argument("--checkpoint", action="store_true", help="Include 100-second desktop opening-scene reference")
parser.add_argument("--seed-session", type=Path, help="Replay collected checkpoint in 100-second reference")
args = parser.parse_args()
if args.seed_session:
    args.seed_session = args.seed_session.resolve()
    for name in ("data.001", "data.sys"):
        if not (args.seed_session / "savedata" / name).is_file():
            parser.error("Missing collected checkpoint files")
    args.checkpoint = True
recipe = hashlib.sha256((ROOT / "scripts/build/Dockerfile").read_bytes()).hexdigest()
image = "sh3-r36s-build:" + recipe[:16]
out = ROOT / ".port-cache" / "runtime-tests" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
out.mkdir(parents=True)
argv = ["docker", "run", "--rm", "--platform", "linux/arm64"]
for folder in ["tests", "ports", "scripts", "dist"]:
    argv += ["--mount", f"type=bind,src={ROOT / folder},dst=/work/{folder},readonly"]
argv += ["--mount", f"type=bind,src={out},dst=/evidence",
         "-e", "SH3_REFERENCE_OUT=/evidence/desktop-reference"]
if args.game or args.checkpoint:
    cfg = config()
    game = Path(cfg.get("SH3_GAME_DIR") or ROOT / "SILENT HILL 3").expanduser().resolve()
    argv += ["--mount", f"type=bind,src={game},dst=/owner,readonly",
             "-e", "SH3_GAME_DATA=/owner", "-e", "SH3_GAME_REFERENCE_OUT=/evidence/game-reference"]
if args.checkpoint:
    argv += ["-e", "SH3_REFERENCE_SECONDS=100"]
if args.seed_session:
    argv += ["--mount", f"type=bind,src={args.seed_session},dst=/seed,readonly",
             "-e", "SH3_REFERENCE_SEED=/seed"]
argv += ["-e", "SH3_RUNTIME_BINARY=/work/dist/runtime/sh3", "-e", "PYTHONDONTWRITEBYTECODE=1",
         image, "python3", "-m", "unittest", "discover", "-s", "tests", "-v"]
with (out / "stdout.txt").open("w") as stdout, (out / "stderr.txt").open("w") as stderr:
    status = subprocess.run(argv, stdout=stdout, stderr=stderr).returncode
(out / "exit-status.txt").write_text(str(status) + "\n")
print((out / "stderr.txt").read_text(), end="")
print("Evidence:", out.relative_to(ROOT))
sys.exit(status)
