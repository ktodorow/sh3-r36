#!/usr/bin/env python3
"""Unattended SH3 deployment, saved device execution and failure-safe collection."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[2]
FILES = ["scripts/device/inventory.sh", "scripts/device/run.sh",
         "scripts/device/check-data.sh", "scripts/device/runtime.sh", "scripts/required-data.txt",
         "scripts/scenes.json",
         "scripts/device/monitor-game.sh",
         "ports/Silent Hill 3.sh", "ports/Silent Hill 3 Runtime Diagnostics.sh",
         "ports/Silent Hill 3 Graphics Diagnostics.sh", "ports/Silent Hill 3 Game.sh",
         "ports/game-session.sh", "ports/restore-frontend.sh"]


def config():
    values = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.removeprefix("export ").partition("=")
        if not sep or not re.fullmatch(r"[A-Z_][A-Z0-9_]*", key.strip()):
            raise ValueError("Invalid .env assignment; shell evaluation is disabled")
        parts = shlex.split(value, comments=True)
        if len(parts) > 1:
            raise ValueError("Quote configuration values containing spaces")
        values[key.strip()] = parts[0] if parts else ""
    return values


def check_ignores():
    for path in [".env", "SILENT HILL 3/sh3.exe", "game/sh3.exe", "tmpRepo/check",
                 "build/check", ".port-cache/check", "r36s-dumps/check", ".cache/check"]:
        if subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode != 0:
            raise ValueError("Required private-artifact ignore coverage missing")


def main():
    from scenes import SCENES, scene_identity, seed_hashes

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["inventory", "preflight", "runtime", "gles", "game"])
    parser.add_argument("--reviewed-helpers", type=Path,
                        help="Prior collected inventory directory whose helpers were reviewed")
    parser.add_argument("--hash-data", action="store_true", help="Record complete asset SHA-256 identities during preflight")
    parser.add_argument("--scene", choices=SCENES, help="Replay shared desktop/device scene plan")
    parser.add_argument("--seed-session", type=Path, help="Copy explicit checkpoint into isolated scene session")
    args = parser.parse_args()
    if args.hash_data and args.action != "preflight":
        parser.error("--hash-data requires preflight action")
    if (args.scene or args.seed_session) and args.action != "game":
        parser.error("Scene replay requires game action")
    if args.seed_session and not args.scene:
        parser.error("--seed-session requires --scene")
    if args.scene and SCENES[args.scene]["seed"] and not args.seed_session:
        parser.error("Selected scene requires --seed-session")
    if args.seed_session:
        args.seed_session = args.seed_session.resolve()
        for name in ("savedata/data.001", "savedata/data.sys"):
            if not (args.seed_session / name).is_file():
                parser.error("Missing collected checkpoint files")
    check_ignores()
    cfg = config()
    port = cfg.get("R36S_PORT", "")
    host = cfg.get("R36S_HOST", "")
    tcp = cfg.get("R36S_SSH_PORT") or "22"
    if port != "sh3":
        raise ValueError("R36S_PORT must match documented SH3 package folder: sh3")
    if not re.fullmatch(r"[A-Za-z0-9_.@-]+", host) or host.startswith("-"):
        raise ValueError("Invalid SSH destination in private config")
    if not tcp.isdigit() or not 1 <= int(tcp) <= 65535:
        raise ValueError("Invalid R36S_SSH_PORT")
    review = None
    if args.action in {"preflight", "runtime", "gles", "game"}:
        if not args.reviewed_helpers:
            raise ValueError("Run inventory and review helpers before preflight")
        review = (args.reviewed_helpers / "device" / "portmaster-files.sha256").read_bytes()
        if not review.strip():
            raise ValueError("Reviewed inventory has no PortMaster helpers")
    runtime_files = []
    if args.action in {"runtime", "gles", "game"}:
        package = ROOT / "dist/runtime"
        binary = (package / "sh3").read_bytes()
        if binary[:6] != b"\x7fELF\x02\x01" or int.from_bytes(binary[18:20], "little") != 183:
            raise ValueError("Runtime must be ELF64 little-endian AArch64")
        build = json.loads((package / "build-inputs.json").read_text())
        selected = Path(cfg.get("SH3_GAME_DIR") or ROOT / "SILENT HILL 3") / "sh3.exe"
        if hashlib.sha1(selected.read_bytes()).hexdigest() != build["input_sha1"]:
            raise ValueError("Runtime generated from different owner input")
        runtime_files = ["sh3", "build-inputs.json", "packages.txt", "compiler.txt", "libc.txt",
                         "python.txt", "elf.txt", "readelf.txt", "artifacts.sha256"]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ-") + uuid.uuid4().hex[:6]
    out = ROOT / "r36s-dumps" / port / run_id
    out.mkdir(parents=True)
    scene = scene_identity(args.scene, args.seed_session) if args.scene else None
    if scene:
        (out / "scene-identity.json").write_text(json.dumps(scene, indent=2) + "\n")
    remote = f"/roms2/ports/{port}/runs/{run_id}"
    remote_payload = remote + "/payload"
    statuses = {"run_id": run_id, "action": args.action, "execution": "not-attempted",
                "collection": "not-attempted"}
    private = [v for k, v in cfg.items() if v and
               (k in {"R36S_HOST", "R36S_SSH_PASSWORD", "SH3_GAME_DIR"} or k.startswith("REFERENCE_"))]
    # SSH errors usually omit user@ prefix; redact endpoint components as well.
    private.append(host.rsplit("@", 1)[-1])
    private.sort(key=len, reverse=True)

    def scrub(data):
        for value in private:
            data = data.replace(value, "[private]")
        return data

    def save(name, data):
        (out / name).write_text(scrub(data))

    ssh_cache = ROOT / ".port-cache" / "ssh"
    ssh_cache.mkdir(parents=True, exist_ok=True)
    askpass = ROOT / "scripts/host/ssh-askpass.sh"
    askpass.chmod(0o700)
    env = {**os.environ, "SSH_ASKPASS": str(askpass), "SSH_ASKPASS_REQUIRE": "force",
           "DISPLAY": "sh3-askpass:0", "R36S_SSH_PASSWORD": cfg.get("R36S_SSH_PASSWORD", "")}
    options = ["-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=10",
               "-o", "NumberOfPasswordPrompts=1", "-o", "LogLevel=ERROR",
               "-o", f"UserKnownHostsFile={ssh_cache / 'known_hosts'}"]

    def command(name, argv, timeout=60):
        process = subprocess.Popen(argv, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            code = process.returncode
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate()
            code = 124
        save(name + ".stdout.txt", stdout.decode(errors="replace"))
        save(name + ".stderr.txt", stderr.decode(errors="replace"))
        statuses[name] = code
        return code

    def ssh(name, script, timeout=60):
        return command(name, ["ssh", *options, "-p", tcp, host, script], timeout)

    identity = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}
    for name in ["scripts/host/r36s.py", "scripts/host/ssh-askpass.sh", "scripts/host/scenes.py"]:
        identity[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    save("source-identity.json", json.dumps({"base_commit": commit, "files": identity}, indent=2) + "\n")
    data_root = Path(cfg.get("SH3_GAME_DIR") or ROOT / "SILENT HILL 3").expanduser()
    result = subprocess.run(["bash", str(ROOT / "scripts/device/check-data.sh"), str(data_root)],
                            capture_output=True, text=True,
                            env={**os.environ, "SH3_DATA_HASHES": "1" if args.hash_data else "0"})
    save("local-data.stdout.txt", result.stdout)
    save("local-data.stderr.txt", result.stderr)
    statuses["local-data"] = result.returncode
    # No original assets are deployed by this preflight-only workflow.
    try:
        with tempfile.TemporaryDirectory(prefix="sh3-payload-", dir=ROOT / ".port-cache") as temp:
            payload = Path(temp) / "payload"
            for name in FILES:
                dest = payload / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((ROOT / name).read_bytes())
            if runtime_files:
                runtime = payload / "runtime"
                runtime.mkdir()
                for name in runtime_files:
                    (runtime / name).write_bytes((ROOT / "dist/runtime" / name).read_bytes())
            if review:
                (payload / "reviewed-helpers.sha256").write_bytes(review)
            if args.hash_data:
                (payload / "hash-data").touch()
            if scene:
                (payload / "scene-plan.json").write_text(json.dumps(scene["plan"], indent=2) + "\n")
                if args.seed_session:
                    for name in scene["seed_sha256"]:
                        dest = payload / "scene-seed" / name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes((args.seed_session / name).read_bytes())
            code = ssh("prepare", "mkdir -p " + shlex.quote(f"/roms2/ports/{port}/runs") +
                       " && mkdir " + shlex.quote(remote))
            if code == 0:
                code = command("deploy", ["scp", *options, "-P", tcp, "-r", str(payload),
                                          host + ":" + remote + "/"], timeout=120)
            if code == 0:
                script = shlex.join(["bash", remote_payload + "/scripts/device/run.sh",
                                     args.action, f"/roms2/ports/{port}", run_id, remote_payload])
                execution_limit = 600 if args.hash_data else 180 if args.action == "game" else 120
                if scene:
                    execution_limit = scene["plan"]["seconds"] + 100
                statuses["execution"] = ssh("execute", script, timeout=execution_limit)
            else:
                statuses["execution"] = "deployment-failed"
    finally:
        # Always attempt collection, including after preparation/deployment/execution failure.
        statuses["collection"] = command(
            "collect", ["scp", *options, "-P", tcp, "-r", host + ":" + remote + "/",
                        str(out / "device")], timeout=120)
        if args.action in {"preflight", "runtime", "gles", "game"}:
            statuses["launcher-collection"] = command(
                "collect-launcher", ["scp", *options, "-P", tcp, "-r",
                                     host + ":" + remote + "-launch/", str(out / "launcher")], timeout=120)
        if args.action == "game":
            statuses["service-collection"] = command(
                "collect-service", ["scp", *options, "-P", tcp, "-r",
                                    host + ":" + remote + "-launch-service/", str(out / "service")], timeout=120)
        if scene:
            scene["source_preserved"] = not args.seed_session or seed_hashes(args.seed_session) == scene["seed_sha256"]
            (out / "scene-identity.json").write_text(json.dumps(scene, indent=2) + "\n")
            statuses["source-preserved"] = scene["source_preserved"]
        save("status.json", json.dumps(statuses, indent=2) + "\n")
    print("Evidence:", out.relative_to(ROOT))
    print("Local data:", statuses["local-data"], "Execution:", statuses["execution"],
          "Collection:", statuses["collection"])
    return 0 if (statuses["execution"] == 0 and statuses["collection"] == 0 and
                 statuses.get("launcher-collection", 0) == 0 and
                 statuses.get("service-collection", 0) == 0 and
                 statuses.get("source-preserved", True)) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as error:
        print("Workflow configuration:", str(error), file=sys.stderr)
        sys.exit(3)
    except OSError as error:
        # Configuration errors do not echo raw values or command lines.
        print("Workflow failed:", type(error).__name__, file=sys.stderr)
        sys.exit(3)
