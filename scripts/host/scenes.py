"""Shared declarative scene plans and immutable source identities; no device access."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENES = json.loads((ROOT / "scripts/scenes.json").read_text())


def seed_hashes(seed):
    return {name: hashlib.sha256((seed / name).read_bytes()).hexdigest()
            for name in ("savedata/data.001", "savedata/data.sys", "savedata/disp.ini",
                         "savedata/key.ini", "sh3-progs.bin", "sh3-gl-cache.bin") if (seed / name).is_file()}


def scene_identity(name, seed=None):
    return {"scene": name, "plan": SCENES[name],
            "plan_sha256": hashlib.sha256(json.dumps(SCENES[name], sort_keys=True).encode()).hexdigest(),
            "runtime_sha256": hashlib.sha256((ROOT / "dist/runtime/sh3").read_bytes()).hexdigest(),
            "seed_sha256": seed_hashes(seed) if seed else {}}
