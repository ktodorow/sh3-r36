"""Launcher failure/cleanup fixtures, not hardware capability tests."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


class LauncherFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.port = self.root / "sh3"
        self.data = self.port / "gamedata"
        self.data.mkdir(parents=True)
        self.save = self.data / "savedata" / "keep.dat"
        self.save.parent.mkdir()
        self.save.write_bytes(b"owner save remains unchanged")
        self.pm = self.root / "xdg" / "PortMaster"
        self.pm.mkdir(parents=True)
        (self.pm / "control.txt").write_text(
            'get_controls() { :; }\n'
            'pm_finish() { printf "frontend ready\\n"; }\n'
        )

    def launch(self, **extra_env):
        return subprocess.run(
            ["bash", str(REPO / "ports" / "Silent Hill 3.sh")],
            env={**os.environ, "SH3_PORT_ROOT": str(self.port),
                 "SH3_RUN_ID": "fixture", "SH3_PACKAGE_DIR": str(REPO),
                 "XDG_DATA_HOME": str(self.root / "xdg"), **extra_env},
            capture_output=True, text=True, timeout=20,
        )


class PreflightLauncherTests(LauncherFixture):
    @unittest.skipUnless((REPO / "SILENT HILL 3/data").is_dir(), "requires owner game data")
    def test_warm_checkpoint_reuses_program_cache_without_changing_source(self):
        original = REPO / "SILENT HILL 3"
        (self.data / "sh3.exe").symlink_to(original / "sh3.exe")
        (self.data / "data").symlink_to(original / "data", target_is_directory=True)
        seed = self.root / "checkpoint"
        (seed / "savedata").mkdir(parents=True)
        for name in ("data.001", "data.sys"):
            (seed / "savedata" / name).write_text("checkpoint")
        (seed / "sh3-progs.bin").write_bytes(b"previous program keys")
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        runtime.write_text('#!/bin/sh\ncat sh3-progs.bin\nprintf changed > sh3-progs.bin\nexit 7\n')
        runtime.chmod(0o755)
        result = self.launch(SH3_MODE="game", SH3_SEED_SESSION=str(seed))
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertIn("previous program keys", result.stdout)
        self.assertEqual((seed / "sh3-progs.bin").read_bytes(), b"previous program keys")

    @unittest.skipUnless((REPO / "SILENT HILL 3/data").is_dir(), "requires owner game data")
    def test_game_replays_checkpoint_in_fresh_session_without_changing_source(self):
        original = REPO / "SILENT HILL 3"
        (self.data / "sh3.exe").symlink_to(original / "sh3.exe")
        (self.data / "data").symlink_to(original / "data", target_is_directory=True)
        seed = self.root / "checkpoint/savedata"
        seed.mkdir(parents=True)
        (seed / "data.001").write_bytes(b"checkpoint one")
        (seed / "data.sys").write_bytes(b"checkpoint index")
        (seed / "unrelated.dat").write_bytes(b"leave behind")
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        runtime.write_text('#!/bin/sh\ncat savedata/data.001 savedata/data.sys\n'
                           'test ! -e savedata/unrelated.dat || exit 8\n'
                           'printf changed > savedata/data.001\nexit 7\n')
        runtime.chmod(0o755)
        result = self.launch(SH3_MODE="game", SH3_SEED_SESSION=str(seed.parent))
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertIn("checkpoint onecheckpoint index", result.stdout)
        self.assertEqual((seed / "data.001").read_bytes(), b"checkpoint one")
        self.assertEqual(self.save.read_bytes(), b"owner save remains unchanged")

    @unittest.skipUnless((REPO / "SILENT HILL 3/data").is_dir(), "requires owner game data")
    def test_game_failure_records_640x480_session_and_preserves_originals(self):
        original = REPO / "SILENT HILL 3"
        (self.data / "sh3.exe").symlink_to(original / "sh3.exe")
        (self.data / "data").symlink_to(original / "data", target_is_directory=True)
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        runtime.write_text('#!/bin/sh\nprintf "game cwd=%s\\n" "$PWD"\n'
                           'cat sh3.ini\nprintf "game boot failed\\n" >&2\nexit 7\n')
        runtime.chmod(0o755)
        commands = self.root / "bin"
        commands.mkdir()
        # External filesystem operation unavailable on exFAT, as observed on R36S.
        link = commands / "ln"
        link.write_text('#!/bin/sh\necho "Operation not permitted" >&2\nexit 1\n')
        link.chmod(0o755)
        result = self.launch(SH3_MODE="game", PATH=f"{commands}:{os.environ['PATH']}")
        run = self.port / "runs/fixture"
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertIn(f"game cwd={run / 'session'}", result.stdout)
        self.assertIn("resolution=640x480", result.stdout)
        self.assertIn("game boot failed", (run / "stderr.txt").read_text())
        self.assertEqual((run / "exit-status.txt").read_text().strip(), "7")
        self.assertEqual(self.save.read_bytes(), b"owner save remains unchanged")
        self.assertIn("frontend ready", result.stdout)

    def test_missing_executable_reports_actionable_error_and_preserves_save(self):
        result = self.launch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing sh3.exe", result.stdout + result.stderr)
        self.assertEqual(self.save.read_bytes(), b"owner save remains unchanged")

    def test_runtime_diagnostics_report_missing_native_binary_and_return(self):
        result = self.launch(SH3_MODE="runtime-diagnostics")
        self.assertEqual(result.returncode, 3)
        self.assertIn("Native runtime missing", result.stderr)
        self.assertIn("frontend ready", result.stdout)
        self.assertEqual(self.save.read_bytes(), b"owner save remains unchanged")

    def test_runtime_failure_keeps_status_logs_and_returns_without_game_data(self):
        runtime = self.port / "runtime" / "sh3"
        runtime.parent.mkdir()
        runtime.write_text('#!/bin/sh\nprintf "native runtime failed\\n" >&2\nexit 7\n')
        runtime.chmod(0o755)
        # macOS lacks target's timeout utility; replace that external boundary only.
        commands = self.root / "bin"
        commands.mkdir()
        timeout = commands / "timeout"
        timeout.write_text('#!/bin/sh\nshift\nexec "$@"\n')
        timeout.chmod(0o755)
        result = self.launch(SH3_MODE="runtime-diagnostics", PATH=f"{commands}:{os.environ['PATH']}")
        self.assertEqual(result.returncode, 7)
        self.assertIn("native runtime failed", result.stderr)
        self.assertIn("frontend ready", result.stdout)
        self.assertEqual((self.port / "runs/fixture/exit-status.txt").read_text().strip(), "7")
        self.assertEqual(self.save.read_bytes(), b"owner save remains unchanged")

    def test_installed_runtime_menu_finds_package_without_host_port_environment(self):
        launcher = self.port / "preflight/ports/Silent Hill 3.sh"
        launcher.parent.mkdir(parents=True)
        shutil.copyfile(REPO / "ports/Silent Hill 3.sh", launcher)
        menu = self.root / "Silent Hill 3 Runtime Diagnostics.sh"
        shutil.copyfile(REPO / "ports/Silent Hill 3 Runtime Diagnostics.sh", menu)
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        runtime.write_text('#!/bin/sh\nprintf "native diagnostics reached\\n"\n')
        runtime.chmod(0o755)
        commands = self.root / "bin"
        commands.mkdir()
        timeout = commands / "timeout"
        timeout.write_text('#!/bin/sh\nshift\nexec "$@"\n')
        timeout.chmod(0o755)
        env = {k: v for k, v in os.environ.items() if not k.startswith("SH3_")}
        env.update(XDG_DATA_HOME=str(self.root / "xdg"), PATH=f"{commands}:{os.environ['PATH']}")
        result = subprocess.run(["bash", str(menu)], env=env, cwd="/", capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("native diagnostics reached", result.stdout)
        self.assertIn("frontend ready", result.stdout)
        launches = list((self.port / "runs").glob("*/exit-status.txt"))
        self.assertEqual(len(launches), 1)
        self.assertEqual(launches[0].read_text().strip(), "0")

    def test_validation_failure_returns_through_portmaster_cleanup(self):
        result = self.launch()
        self.assertIn("frontend ready", result.stdout)
        self.assertEqual(result.returncode, 2)

    def test_helper_exit_trap_cannot_replace_launcher_cleanup(self):
        with (self.pm / "control.txt").open("a") as control:
            control.write("trap 'printf \"helper trap\\n\"' EXIT\n")
        result = self.launch()
        self.assertIn("frontend ready", result.stdout)
        self.assertEqual(result.returncode, 2)

    def test_preflight_cleanup_preserves_unrelated_port_helpers(self):
        unrelated = self.root / "unrelated-port-helper"
        unrelated.write_text("another port owns this")
        (self.pm / "control.txt").write_text(
            'get_controls() { :; }\n'
            'pm_gptokeyb_finish() { rm -- "$XDG_DATA_HOME/../unrelated-port-helper"; }\n'
            'pm_finish() { pm_gptokeyb_finish; printf "frontend ready\\n"; }\n'
        )
        result = self.launch()
        self.assertEqual(result.returncode, 2)
        self.assertIn("frontend ready", result.stdout)
        self.assertTrue(unrelated.is_file())

    def test_wrong_executable_size_is_reported_without_changing_original(self):
        exe = self.data / "sh3.exe"
        exe.write_bytes(b"owner supplied wrong build")
        result = self.launch()
        self.assertEqual(result.returncode, 2)
        self.assertIn("expected 3338240 bytes", result.stdout + result.stderr)
        self.assertEqual(exe.read_bytes(), b"owner supplied wrong build")

    def test_same_size_wrong_executable_cannot_pass_on_size_alone(self):
        exe = self.data / "sh3.exe"
        exe.write_bytes(bytes(3338240))
        result = self.launch()
        self.assertEqual(result.returncode, 2)
        self.assertIn("expected SHA-1 aa2aca6dba19bf510c9c2e92eefdc15e98266581",
                      result.stdout + result.stderr)
        self.assertEqual(exe.stat().st_size, 3338240)

    @unittest.skipUnless((REPO / "SILENT HILL 3/sh3.exe").is_file(), "requires owner CD executable")
    def test_owner_cd_executable_is_recognized_before_missing_assets_are_reported(self):
        # Real owner input stays ignored; no game bytes or hash mocks in fixtures.
        original = REPO / "SILENT HILL 3/sh3.exe"
        before = original.read_bytes()
        shutil.copyfile(original, self.data / "sh3.exe")
        result = self.launch()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Input profile: owner-cd-d851669e", result.stdout)
        self.assertNotIn("Unsupported sh3.exe", result.stderr)
        self.assertIn("Missing or empty required data: data/movie/op.000", result.stderr)
        self.assertEqual(original.read_bytes(), before)

    def test_missing_original_movie_is_reported_even_with_invalid_executable(self):
        (self.data / "sh3.exe").write_bytes(b"wrong build")
        result = self.launch()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Missing or empty required data: data/movie/op.000",
                      result.stdout + result.stderr)

    def test_requested_asset_identity_survives_failed_preflight_without_changing_data(self):
        asset = self.data / "data/movie/op.000"
        asset.parent.mkdir(parents=True)
        asset.write_bytes(b"abc")
        result = self.launch(SH3_DATA_HASHES="1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("data-sha256\tdata/movie/op.000\t"
                      "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                      result.stdout)
        self.assertEqual(asset.read_bytes(), b"abc")
        self.assertIn("frontend ready", result.stdout)

    def test_portmaster_setup_failure_is_distinct_from_game_data_failure(self):
        (self.pm / "control.txt").write_text(
            'get_controls() { return 9; }\n'
            'pm_finish() { printf "frontend ready\\n"; }\n'
        )
        result = self.launch()
        self.assertEqual(result.returncode, 3)
        self.assertIn("PortMaster controls failed", result.stderr)
        self.assertIn("frontend ready", result.stdout)

    def test_partial_portmaster_source_failure_cleans_up_and_stays_distinct(self):
        (self.pm / "control.txt").write_text(
            'get_controls() { :; }\n'
            'pm_finish() { printf "frontend ready\\n"; }\n'
            'return 7\n'
        )
        result = self.launch()
        self.assertEqual(result.returncode, 3)
        self.assertIn("PortMaster control.txt failed", result.stderr)
        self.assertIn("frontend ready", result.stdout)

    def test_player_gets_portmaster_message_for_invalid_data(self):
        with (self.pm / "control.txt").open("a") as control:
            control.write('printf "unrelated helper warning\\n" >&2\n')
            control.write('pm_message() { printf "player message: %s\\n" "$1"; }\n')
        result = self.launch()
        self.assertIn("player message: Missing sh3.exe", result.stdout)
        self.assertEqual(result.returncode, 2)

    def test_unattended_preflight_reports_error_without_opening_display(self):
        with (self.pm / "control.txt").open("a") as control:
            control.write('pm_message() { printf "GUI opened\\n"; }\n')
        result = self.launch(SH3_PREFLIGHT_HEADLESS="1")
        self.assertNotIn("GUI opened", result.stdout)
        self.assertIn("Missing sh3.exe", result.stderr)
        self.assertIn("frontend ready", result.stdout)
        self.assertEqual(result.returncode, 2)

    def test_failure_evidence_is_separate_and_prior_logs_survive(self):
        prior = self.port / "runs" / "prior" / "stdout.txt"
        prior.parent.mkdir(parents=True)
        prior.write_text("prior evidence")
        result = self.launch()
        run = self.port / "runs" / "fixture"
        self.assertTrue((run / "exit-status.txt").is_file())
        self.assertEqual((run / "exit-status.txt").read_text().strip(), "2")
        self.assertIn("Missing sh3.exe", (run / "stderr.txt").read_text())
        self.assertIn("frontend ready", (run / "stdout.txt").read_text())
        self.assertEqual(prior.read_text(), "prior evidence")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
