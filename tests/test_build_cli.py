"""Saved host CLI boundary; Docker is external, fixtures never prove target runtime."""
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
class BuildCliTests(unittest.TestCase):
    def setUp(self):
        (REPO / ".port-cache").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="build-cli-", dir=REPO / ".port-cache")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ["scripts/host/build.py", "scripts/host/r36s.py", "scripts/device/check-data.sh",
                     "scripts/required-data.txt", "scripts/build/Dockerfile", ".gitignore", "CMakeLists.txt"]:
            dest = self.root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / name, dest)
        (self.root / ".env").write_text("SH3_GAME_DIR=" + shlex.quote(str(REPO / "SILENT HILL 3")) + "\n")
        commands = self.root / "bin"
        commands.mkdir()
        docker = commands / "docker"
        docker.write_text('#!/bin/sh\nprintf "Docker daemon unavailable\\n" >&2\nexit 42\n')
        docker.chmod(0o755)
        self.env = {**os.environ, "PATH": f"{commands}:{os.environ['PATH']}",
                    "GIT_DIR": str(REPO / ".git"), "GIT_WORK_TREE": str(self.root), "GIT_OPTIONAL_LOCKS": "0"}

    def test_unavailable_docker_retains_failed_build_status_and_selected_input_identity(self):
        final = self.root / "dist/runtime/sh3"
        final.parent.mkdir(parents=True)
        final.write_bytes(b"previous final artifact")
        result = subprocess.run(["python3", str(self.root / "scripts/host/build.py")],
                                cwd=self.root, env=self.env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 42, result.stderr)
        runs = list((self.root / ".port-cache/builds").iterdir())
        self.assertEqual(len(runs), 1)
        run = runs[0]
        self.assertEqual((run / "exit-status.txt").read_text().strip(), "42")
        self.assertIn("Docker daemon unavailable", (run / "image.stderr.txt").read_text())
        self.assertTrue((run / "build-inputs.json").is_file(), "failed build lost selected input identity")
        self.assertEqual(json.loads((run / "build-inputs.json").read_text())["input_sha1"],
                         "d851669ef609b3164e3581aa8dcfbfaec866cb79")
        self.assertEqual(final.read_bytes(), b"previous final artifact")


class BuildCleanupCliTests(unittest.TestCase):
    def test_optional_docker_cleanup_removes_owned_unused_resources_and_preserves_other_projects(self):
        with tempfile.TemporaryDirectory(prefix="cleanup-docker-", dir=REPO / ".port-cache") as temp:
            root = Path(temp)
            cli = root / "scripts/host/clean-build.py"
            cli.parent.mkdir(parents=True)
            shutil.copyfile(REPO / "scripts/host/clean-build.py", cli)
            resources = root / "resources"
            resources.mkdir()
            for name in ["owned-container", "owned-image", "other-container", "other-image"]:
                (resources / name).touch()
            commands = root / "bin"
            commands.mkdir()
            docker = commands / "docker"
            docker.write_text('''#!/bin/sh
case "$1 $2" in
  'ps -q') exit 0 ;;
  'ps -aq') echo abcd1234 ;;
  'image ls') echo '{"Repository":"sh3-r36s-build","Tag":"fixture","ID":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}' ;;
  'container rm') [ "$3" = abcd1234 ] && rm "$RESOURCES/owned-container" ;;
  'image rm') [ "$3" = sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa ] && rm "$RESOURCES/owned-image" ;;
  *) exit 3 ;;
esac
''')
            docker.chmod(0o755)
            result = subprocess.run(["python3", str(cli), "--docker"], cwd=root,
                                    env={**os.environ, "PATH": f"{commands}:{os.environ['PATH']}", "RESOURCES": str(resources)},
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((resources / "owned-container").exists())
            self.assertFalse((resources / "owned-image").exists())
            self.assertTrue((resources / "other-container").exists())
            self.assertTrue((resources / "other-image").exists())

    def test_cleanup_removes_only_disposable_build_tree(self):
        (REPO / ".port-cache").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cleanup-cli-", dir=REPO / ".port-cache") as temp:
            root = Path(temp)
            cli = root / "scripts/host/clean-build.py"
            cli.parent.mkdir(parents=True)
            if (REPO / "scripts/host/clean-build.py").is_file():
                shutil.copyfile(REPO / "scripts/host/clean-build.py", cli)
            preserved = ["src/keep.c", "src/recomp/gen/keep.c", "dist/runtime/sh3", ".env",
                         ".port-cache/builds/prior/stdout.txt", "r36s-dumps/sh3/prior/stdout.txt"]
            for name in [*preserved, "build/arm64/disposable.o"]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"preserve me")
            commands = root / "bin"
            commands.mkdir()
            docker = commands / "docker"
            docker.write_text("#!/bin/sh\nexit 0\n")
            docker.chmod(0o755)
            result = subprocess.run(["python3", str(cli)], cwd=root,
                                    env={**os.environ, "PATH": f"{commands}:{os.environ['PATH']}"},
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / "build").exists())
            for name in preserved:
                self.assertEqual((root / name).read_bytes(), b"preserve me", name)


if __name__ == "__main__":
    unittest.main()
