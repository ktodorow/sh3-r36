"""Assertions over collected installed launcher runs on actual R36S, never mock capabilities."""
import json
import os
from pathlib import Path
import re
import unittest


@unittest.skipUnless(os.environ.get("SH3_RUNTIME_EVIDENCE"), "requires actual collected native R36S run")
class RuntimeEvidenceTests(unittest.TestCase):
    def test_all_native_diagnostics_and_target_dependency_closure_pass(self):
        run = Path(os.environ["SH3_RUNTIME_EVIDENCE"])
        output = (run / "launcher/stdout.txt").read_text()
        for observation in ["signals=PASS guard_faults=2 alternate_stack=yes",
                            "threads=PASS tls=isolated resume_before_pause=16 signal_pause_resume=16",
                            "timers=PASS", "runtime=PASS rendering=untested"]:
            self.assertIn(observation, output)
        self.assertIn("sh3: OK", (run / "device/package-integrity.txt").read_text())
        dependencies = (run / "device/runtime-dependencies.txt").read_text()
        self.assertNotIn("not found", dependencies)
        for name in ["libSDL2", "libm.so", "libc.so", "ld-linux-aarch64"]:
            self.assertIn(name, dependencies)
        self.assertGreaterEqual((run / "device/runtime-closure.txt").read_text().count("AArch64"), 5)
        self.assertEqual((run / "device/runtime-closure.stderr.txt").read_text(), "")

    def test_runtime_preserves_firmware_libraries_and_leaves_no_process_or_mount(self):
        run = Path(os.environ["SH3_RUNTIME_EVIDENCE"]) / "device"
        self.assertTrue((run / "firmware-libraries-after.txt").is_file(), "firmware preservation evidence missing")
        checks = (run / "firmware-libraries-after.txt").read_text().splitlines()
        self.assertTrue(checks)
        self.assertTrue(all(line.endswith(": OK") for line in checks))
        self.assertEqual((run / "runtime-pids-after.txt").read_text().strip(), "")
        self.assertEqual((run / "port-mounts-before.txt").read_text(), (run / "port-mounts-after.txt").read_text())

    def test_native_memory_launch_succeeds_with_small_resident_cost_and_preserved_frontend(self):
        run = Path(os.environ["SH3_RUNTIME_EVIDENCE"])
        status = json.loads((run / "status.json").read_text())
        self.assertEqual(status["collection"], 0)
        self.assertEqual(status["launcher-collection"], 0)
        self.assertEqual((run / "launcher/exit-status.txt").read_text().strip(), "0")
        output = (run / "launcher/stdout.txt").read_text()
        self.assertIn("memory=PASS arena_bytes=4294967296 committed_bytes=8392704", output)
        observations = dict(re.findall(r"(\w+_kib)=(\d+)", output))
        self.assertGreaterEqual(int(observations["reserved_vm_kib"]) - int(observations["baseline_vm_kib"]), 4194304)
        self.assertLess(int(observations["reserved_rss_kib"]) - int(observations["baseline_rss_kib"]), 4096)
        self.assertLess(int(observations["touched_rss_kib"]), 131072)
        before = {line.split()[0] for line in (run / "device/frontend-before.txt").read_text().splitlines()}
        after = {line.split()[0] for line in (run / "device/frontend-after.txt").read_text().splitlines()}
        self.assertTrue(before)
        self.assertEqual(before, after)


@unittest.skipUnless(os.environ.get("SH3_NATIVE_PHYSICAL_EVIDENCE"), "requires collected physical menu run")
class PhysicalRuntimeEvidenceTests(unittest.TestCase):
    def test_successful_physical_native_menu_run_is_collected(self):
        run = Path(os.environ["SH3_NATIVE_PHYSICAL_EVIDENCE"])
        launches = [p.parent for p in (run / "device/previous-launches").glob("*/exit-status.txt")
                    if re.fullmatch(r"\d{8}T\d{6}Z-\d+", p.parent.name) and p.read_text().strip() == "0"]
        self.assertTrue(any("runtime=PASS rendering=untested" in (p / "stdout.txt").read_text()
                            for p in launches), "no successful physical native diagnostic run collected")


if __name__ == "__main__":
    unittest.main()
