#!/usr/bin/env python3
"""Remove disposable project build tree; preserve source, final artifacts and evidence."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
LABEL = "org.sh3-r36s.build=native-arm64"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker", action="store_true", help="Also remove stopped labelled containers and unused labelled project images")
    args = parser.parse_args()
    active = subprocess.run(["docker", "ps", "-q", "--filter", "label=" + LABEL],
                            capture_output=True, text=True)
    if active.returncode or active.stdout.strip():
        print("Cannot clean: Docker unavailable or project container active.", file=sys.stderr)
        return 3
    build = ROOT / "build"
    if build.is_symlink() or build.resolve().parent != ROOT:
        print("Refusing build path outside project.", file=sys.stderr)
        return 3
    if build.exists():
        shutil.rmtree(build)
    if args.docker:
        containers = subprocess.check_output(["docker", "ps", "-aq", "--filter", "label=" + LABEL], text=True).split()
        for container in containers:
            if not re.fullmatch(r"[0-9a-f]{8,64}", container):
                raise ValueError("Invalid Docker container identity")
            subprocess.run(["docker", "container", "rm", container], check=True)
        images = subprocess.check_output(["docker", "image", "ls", "--no-trunc", "--filter", "label=" + LABEL,
                                          "--format", "{{json .}}"], text=True)
        for line in images.splitlines():
            image = json.loads(line)
            if image["Repository"] != "sh3-r36s-build":
                continue
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", image["ID"]):
                raise ValueError("Invalid Docker image identity")
            # No force: Docker preserves images still referenced by any container.
            subprocess.run(["docker", "image", "rm", image["ID"]], check=True)
    print("Disposable build tree removed; source, dist and evidence preserved.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("Cleanup failed:", type(error).__name__, file=sys.stderr)
        sys.exit(3)
