"""Saved host CLI boundary; Docker is external, fixtures never prove target runtime."""
import hashlib
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

    def test_selected_optimization_survives_unavailable_docker_in_build_identity(self):
        result = subprocess.run(["python3", str(self.root / "scripts/host/build.py"),
                                 "--optimization", "O3"],
                                cwd=self.root, env=self.env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 42, result.stderr)
        runs = list((self.root / ".port-cache/builds").iterdir())
        self.assertEqual(len(runs), 1)
        identity = json.loads((runs[0] / "build-inputs.json").read_text())
        self.assertEqual(identity.get("optimization"), "O3",
                         "requested compiler variant lost from reproducible build identity")

    @unittest.skipUnless(os.environ.get("SH3_REAL_BUILD_TESTS") == "1",
                         "requires real Linux ARM64 Docker build")
    def test_lto_variant_builds_real_artifact_and_can_restore_non_lto(self):
        source = self.root / "src/runtime/host.c"
        source.parent.mkdir(parents=True)
        source.write_text('#include <limits.h>\n#include <stdio.h>\n'
                          'extern int fold(int);\nint main(void) { volatile int n = INT_MAX; '
                          'printf("%d %d\\n", fold(n), fold(6)); }\n')
        (source.parent / "helper.c").write_text('int fold(int n) { return (n + 1) * 6; }\n')
        (self.root / "CMakeLists.txt").write_text(
            'cmake_minimum_required(VERSION 3.20)\nproject(lto_check C)\n'
            'add_executable(sh3 src/runtime/host.c src/runtime/helper.c)\n'
            'target_compile_options(sh3 PRIVATE -fwrapv -fno-strict-aliasing)\n')
        # Keep production native build script; replace only external data generation.
        shutil.copyfile(REPO / "scripts/build/native.sh", self.root / "scripts/build/native.sh")
        generator = self.root / "tools/regen.sh"
        generator.parent.mkdir()
        generator.write_text('mkdir -p src/recomp/gen\nprintf "fixture\\n" > src/recomp/gen/input.txt\n')
        (self.root / "scripts/build/shader-samples.py").write_text(
            'from pathlib import Path\nimport sys\np = Path(sys.argv[2])\n'
            'p.parent.mkdir(parents=True, exist_ok=True)\np.write_text("/* fixture */\\n")\n')
        env = {**self.env, "PATH": os.environ["PATH"]}
        image = "sh3-r36s-build:" + hashlib.sha256(
            (self.root / "scripts/build/Dockerfile").read_bytes()).hexdigest()[:16]
        for selected in (True, False):
            result = subprocess.run(["python3", str(self.root / "scripts/host/build.py"),
                                     "--optimization", "O3", *(["--lto"] if selected else [])],
                                    cwd=self.root, env=env, capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            runs = sorted((self.root / ".port-cache/builds").iterdir())
            identity = json.loads((runs[-1] / "build-inputs.json").read_text())
            self.assertEqual(identity.get("lto"), selected)
            commands = json.loads((self.root / "build/arm64/compile_commands.json").read_text())
            for command in commands:
                flags = command['command']
                self.assertEqual('-flto=2' in flags, selected)
                self.assertIn('-mcpu=cortex-a35', flags)
                self.assertIn('-O3', flags)
                self.assertIn('-fwrapv', flags)
                self.assertIn('-fno-strict-aliasing', flags)
                self.assertNotIn('-ffast-math', flags)
            output = subprocess.check_output([
                "docker", "run", "--rm", "--platform", "linux/arm64", "--network", "none",
                "--mount", f"type=bind,src={self.root / 'dist/runtime'},dst=/artifact,readonly",
                image, "/artifact/sh3"], text=True).strip()
            self.assertEqual(output, '0 42', 'compiler variant changed signed-wrap example')
            object_sections = subprocess.check_output([
                "docker", "run", "--rm", "--platform", "linux/arm64", "--network", "none",
                "--mount", f"type=bind,src={self.root / 'build/arm64'},dst=/compile,readonly",
                image, "readelf", "-SW", "/compile/CMakeFiles/sh3.dir/src/runtime/helper.c.o"], text=True)
            self.assertEqual('.gnu.lto_' in object_sections, selected,
                             'actual object does not match requested LTO mode')

    @unittest.skipUnless(os.environ.get("SH3_REAL_BUILD_TESTS") == "1",
                         "requires real Linux ARM64 Docker build")
    def test_changed_source_rebuilds_when_its_mtime_predates_cached_object(self):
        source = self.root / "src/runtime/host.c"
        source.parent.mkdir(parents=True)
        source.write_text('#include <stdio.h>\nint main(void) { puts("first"); }\n')
        (self.root / "CMakeLists.txt").write_text(
            'cmake_minimum_required(VERSION 3.20)\nproject(cache_check C)\n'
            'add_executable(sh3 src/runtime/host.c)\n')
        (self.root / "scripts/build/native.sh").write_text('''#!/bin/bash
set -euo pipefail
mkdir -p build/arm64 dist/runtime
cmake -S . -B build/arm64 -G Ninja
cmake --build build/arm64
cp build/arm64/sh3 dist/runtime/sh3
dpkg-query -W > build/arm64/packages.txt
cc --version > build/arm64/compiler.txt
getconf GNU_LIBC_VERSION > build/arm64/libc.txt
python3 --version > build/arm64/python.txt
''')
        env = {**self.env, "PATH": os.environ["PATH"]}
        image = "sh3-r36s-build:" + hashlib.sha256(
            (self.root / "scripts/build/Dockerfile").read_bytes()).hexdigest()[:16]

        def build_and_run():
            result = subprocess.run(["python3", str(self.root / "scripts/host/build.py")],
                                    cwd=self.root, env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            return subprocess.check_output([
                "docker", "run", "--rm", "--platform", "linux/arm64", "--mount",
                f"type=bind,src={self.root / 'dist/runtime'},dst=/artifact,readonly",
                image, "/artifact/sh3"], text=True).strip()

        self.assertEqual(build_and_run(), "first")
        source.write_text('#include <stdio.h>\nint main(void) { puts("second"); }\n')
        os.utime(source, ns=(1_000_000_000, 1_000_000_000))
        self.assertEqual(build_and_run(), "second",
                         "build identity changed but executable still contains old source")

        # A failed build may already have replaced objects; returning to a known
        # source revision must not reuse those partially changed objects.
        native = self.root / "scripts/build/native.sh"
        good_native, good_source = native.read_text(), source.read_text()
        source.write_text('#include <stdio.h>\nint main(void) { puts("failed revision"); }\n')
        native.write_text(good_native + 'exit 17\n')
        failed = subprocess.run(["python3", str(self.root / "scripts/host/build.py")],
                                cwd=self.root, env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(failed.returncode, 17, failed.stderr + failed.stdout)
        native.write_text(good_native)
        source.write_text(good_source)
        os.utime(source, ns=(1_000_000_000, 1_000_000_000))
        self.assertEqual(build_and_run(), "second", "failed build poisoned reverted source")


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
