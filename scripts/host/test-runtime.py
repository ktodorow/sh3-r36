#!/usr/bin/env python3
"""Run real ARM64 binary through agreed launcher seam inside reusable Docker image."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import subprocess
import sys

from r36s import ROOT, check_ignores


check_ignores()
recipe = hashlib.sha256((ROOT / "scripts/build/Dockerfile").read_bytes()).hexdigest()
image = "sh3-r36s-build:" + recipe[:16]
out = ROOT / ".port-cache" / "runtime-tests" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
out.mkdir(parents=True)
argv = ["docker", "run", "--rm", "--platform", "linux/arm64"]
for folder in ["tests", "ports", "scripts", "dist"]:
    argv += ["--mount", f"type=bind,src={ROOT / folder},dst=/work/{folder},readonly"]
argv += ["-e", "SH3_RUNTIME_BINARY=/work/dist/runtime/sh3", "-e", "PYTHONDONTWRITEBYTECODE=1",
         image, "python3", "-m", "unittest", "discover", "-s", "tests", "-v"]
with (out / "stdout.txt").open("w") as stdout, (out / "stderr.txt").open("w") as stderr:
    status = subprocess.run(argv, stdout=stdout, stderr=stderr).returncode
(out / "exit-status.txt").write_text(str(status) + "\n")
print((out / "stderr.txt").read_text(), end="")
print("Evidence:", out.relative_to(ROOT))
sys.exit(status)
