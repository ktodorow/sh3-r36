"""Real Docker-built binary through launcher; host fixtures do not prove R36S compatibility."""
import os
import re
import shutil
import unittest

from test_preflight import LauncherFixture


@unittest.skipUnless(os.environ.get("SH3_RUNTIME_BINARY"), "requires Linux ARM64 Docker-built binary")
class RuntimeLauncherTests(LauncherFixture):
    def setUp(self):
        super().setUp()
        runtime = self.port / "runtime/sh3"
        runtime.parent.mkdir()
        shutil.copyfile(os.environ["SH3_RUNTIME_BINARY"], runtime)
        runtime.chmod(0o755)

    def test_memory_diagnostic_reports_full_guest_window_and_resident_cost_then_returns(self):
        result = self.launch(SH3_MODE="runtime-diagnostics")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("memory=PASS arena_bytes=4294967296 committed_bytes=8392704", result.stdout)
        observations = dict(re.findall(r"(baseline|reserved|touched)_rss_kib=(\d+)", result.stdout))
        self.assertEqual(set(observations), {"baseline", "reserved", "touched"})
        self.assertLess(int(observations["reserved"]) - int(observations["baseline"]), 4096)
        self.assertLess(int(observations["touched"]), 131072)
        self.assertIn("frontend ready", result.stdout)
        self.assertEqual(self.save.read_bytes(), b"owner save remains unchanged")

    def test_guest_thread_tls_and_pause_resume_complete_before_frontend_return(self):
        result = self.launch(SH3_MODE="runtime-diagnostics")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("threads=PASS tls=isolated resume_before_pause=16 signal_pause_resume=16", result.stdout)
        self.assertIn("frontend ready", result.stdout)

    def test_guest_guard_faults_reach_alternate_signal_stack_without_crashing_launcher(self):
        result = self.launch(SH3_MODE="runtime-diagnostics")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("signals=PASS guard_faults=2 alternate_stack=yes", result.stdout)
        self.assertIn("frontend ready", result.stdout)

    def test_game_timer_bridges_measure_requested_sleep_and_return(self):
        result = self.launch(SH3_MODE="runtime-diagnostics")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("timers=PASS", result.stdout)
        observations = dict(re.findall(r"(frequency_hz|elapsed_us|tick_delta_ms|multimedia_delta_ms)=(\d+)", result.stdout))
        self.assertGreater(int(observations["frequency_hz"]), 0)
        self.assertGreaterEqual(int(observations["elapsed_us"]), 20000)
        self.assertLess(int(observations["elapsed_us"]), 2000000)
        for name in ["tick_delta_ms", "multimedia_delta_ms"]:
            self.assertGreaterEqual(int(observations[name]), 20)
            self.assertLess(int(observations[name]), 2000)
        self.assertIn("frontend ready", result.stdout)

    def test_completed_session_reports_final_and_peak_resident_memory_separately_from_virtual(self):
        result = self.launch(SH3_MODE="runtime-diagnostics")
        self.assertEqual(result.returncode, 0, result.stderr)
        observations = dict(re.findall(r"(diagnostics_\w+_kib)=(\d+)", result.stdout))
        self.assertIn("diagnostics_vm_kib", observations)
        self.assertGreaterEqual(int(observations["diagnostics_vm_kib"]), 4194304)
        for name in ["diagnostics_rss_kib", "diagnostics_max_rss_kib"]:
            self.assertGreater(int(observations[name]), 0)
            self.assertLess(int(observations[name]), 131072)


if __name__ == "__main__":
    unittest.main()
