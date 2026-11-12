#!/usr/bin/env python3
"""Build selected owner input in reusable, pinned native Linux ARM64 Docker image."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from r36s import ROOT, check_ignores, config


def main():
    check_ignores()
    cfg = config()
    game = Path(cfg.get("SH3_GAME_DIR") or ROOT / "SILENT HILL 3").expanduser().resolve()
    validation = subprocess.run(["bash", "scripts/device/check-data.sh", str(game)],
                                cwd=ROOT, capture_output=True, text=True)
    if validation.returncode:
        print(validation.stdout + validation.stderr, end="")
        return validation.returncode
    source = (game / "sh3.exe").read_bytes()
    input_sha1 = hashlib.sha1(source).hexdigest()
    evidence = ROOT / ".port-cache/builds" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    evidence.mkdir(parents=True)
    dockerfile = ROOT / "scripts/build/Dockerfile"
    recipe = hashlib.sha256(dockerfile.read_bytes()).hexdigest()
    image = "sh3-r36s-build:" + recipe[:16]
    (evidence / "build-inputs.json").write_text(json.dumps({
        "input_sha1": input_sha1, "input_size": len(source), "recipe_sha256": recipe,
    }, indent=2) + "\n")
    probe = subprocess.run(["docker", "image", "inspect", image], capture_output=True, text=True)
    if probe.returncode:
        with (evidence / "image.stdout.txt").open("w") as stdout, (evidence / "image.stderr.txt").open("w") as stderr:
            status = subprocess.run(["docker", "build", "--platform", "linux/arm64", "-t", image,
                                     "-f", str(dockerfile), str(dockerfile.parent)], stdout=stdout, stderr=stderr).returncode
        if status:
            (evidence / "exit-status.txt").write_text(str(status) + "\n")
            print("Image build failed. Evidence:", evidence.relative_to(ROOT))
            return status
    info = json.loads(subprocess.check_output(["docker", "image", "inspect", image]))[0]
    if info["Os"] != "linux" or info["Architecture"] != "arm64":
        raise ValueError("Build image must be Linux ARM64")
    out = ROOT / "build/arm64"
    out.mkdir(parents=True, exist_ok=True)
    paths = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode().split("\0")
    inputs = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths
              if p and (p == "CMakeLists.txt" or p.startswith(("src/", "tools/", "assets/", "third_party/", "scripts/build/", "scripts/host/"))) and (ROOT / p).is_file()}
    identity = {"input_sha1": input_sha1, "input_size": len(source), "image_id": info["Id"],
                "recipe_sha256": recipe, "source": inputs,
                "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    generation = {p: digest for p, digest in inputs.items()
                  if p.startswith(("tools/", "third_party/")) or p == "src/game/sh3.c"}
    generation.update(input_sha1=input_sha1, image_id=info["Id"])
    trace = ROOT / "build/trace.json"
    if trace.is_file():
        generation["trace_sha256"] = hashlib.sha256(trace.read_bytes()).hexdigest()
    identity["generation_key"] = hashlib.sha256(json.dumps(generation, sort_keys=True).encode()).hexdigest()
    (evidence / "build-inputs.json").write_text(json.dumps(identity, indent=2) + "\n")
    epoch = subprocess.check_output(["git", "show", "-s", "--format=%ct", "HEAD"], cwd=ROOT, text=True).strip()
    # Snapshot excludes private config and original game data. Selected EXE mounts read-only.
    with tempfile.TemporaryDirectory(prefix="sh3-source-", dir=ROOT / ".port-cache") as temp:
        stage = Path(temp)
        for name in inputs:
            dest = stage / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, dest)
        for name in ["build", "dist", "src/recomp/gen", "owner"]:
            (stage / name).mkdir(parents=True, exist_ok=True)
        (stage / "owner/sh3.exe").touch()
        generated = ROOT / "src/recomp/gen"
        generated.mkdir(parents=True, exist_ok=True)
        artifacts = evidence / "artifacts"
        artifacts.mkdir()
        argv = ["docker", "run", "--rm", "--platform", "linux/arm64", "--label", "org.sh3-r36s.build=native-arm64",
                "--mount", f"type=bind,src={stage},dst=/work,readonly",
                "--mount", f"type=bind,src={game / 'sh3.exe'},dst=/work/owner/sh3.exe,readonly",
                "--mount", f"type=bind,src={ROOT / 'build'},dst=/work/build",
                "--mount", f"type=bind,src={generated},dst=/work/src/recomp/gen",
                "--mount", f"type=bind,src={artifacts},dst=/work/dist",
                "-e", "SH3_EXE=/work/owner/sh3.exe", "-e", f"SOURCE_DATE_EPOCH={epoch}",
                "-e", "SH3_GENERATION_KEY=" + identity["generation_key"],
                "-e", "SH3_BUILD_JOBS=" + os.environ.get("SH3_BUILD_JOBS", "2"), image,
                "bash", "scripts/build/native.sh"]
        with (evidence / "build.stdout.txt").open("w") as stdout, (evidence / "build.stderr.txt").open("w") as stderr:
            status = subprocess.run(argv, stdout=stdout, stderr=stderr).returncode
    (evidence / "exit-status.txt").write_text(str(status) + "\n")
    for name in ["packages.txt", "compiler.txt", "libc.txt", "python.txt", "generation.stdout.txt", "generation.stderr.txt"]:
        if (out / name).is_file():
            shutil.copy2(out / name, evidence / name)
    for name in ["generated.sha256", "generation-key.txt", "recomp/summary.json", "recomp.log", "disasm.log", "abi.log", "arm64/compile_commands.json"]:
        if (ROOT / "build" / name).is_file():
            shutil.copy2(ROOT / "build" / name, evidence / Path(name).name)
    if hashlib.sha1((game / "sh3.exe").read_bytes()).hexdigest() != input_sha1:
        raise ValueError("Original input changed during build")
    if status == 0:
        dest = ROOT / "dist/runtime"
        package = evidence / "artifacts/runtime"
        for name in ["build-inputs.json", "packages.txt", "compiler.txt", "libc.txt", "python.txt"]:
            shutil.copy2(evidence / name, package / name)
        dest.parent.mkdir(exist_ok=True)
        if dest.exists():
            dest.rename(dest.with_name("runtime-previous-" + evidence.name))
        shutil.copytree(package, dest)
    print("Build status:", status, "Evidence:", evidence.relative_to(ROOT))
    return status


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("Build workflow failed:", type(error).__name__, file=sys.stderr)
        sys.exit(3)
