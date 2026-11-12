"""Checks real collected preflight observations; never substitutes for hardware runs."""
import os
from pathlib import Path
import re
import unittest


@unittest.skipUnless(os.environ.get("SH3_TARGET_EVIDENCE"), "requires actual collected R36S run")
class TargetEvidenceTests(unittest.TestCase):
    def test_physical_menu_launch_logs_are_collected(self):
        run = Path(os.environ["SH3_TARGET_EVIDENCE"])
        launches = [p for p in (run / "device/previous-launches").glob("*/exit-status.txt")
                    if re.fullmatch(r"\d{8}T\d{6}Z-\d+", p.parent.name)]
        self.assertTrue(launches, "physical launch evidence not collected")
        failures = [f.parent for f in launches if f.read_text().strip() == "2"]
        self.assertTrue(any("Missing sh3.exe" in (p / "data.stderr.txt").read_text()
                            for p in failures))

    def test_preflight_records_installed_graphics_and_sdl_library_identities(self):
        run = Path(os.environ["SH3_TARGET_EVIDENCE"])
        libraries = (run / "device/libraries.txt").read_text()
        for library in ("libEGL", "libGLESv2", "libSDL2"):
            with self.subTest(library=library):
                self.assertIn(library, libraries)
        self.assertIn("[hash]", libraries)

    def test_installed_portmaster_dependencies_are_available_for_review(self):
        run = Path(os.environ["SH3_TARGET_EVIDENCE"])
        helpers = run / "device/helpers/opt/system/Tools/PortMaster"
        # Dependencies read from installed control.txt/funcs.txt, not SH3 implementation.
        for name in ("PortMasterDialog.txt", "mapper.py", "pugwash"):
            with self.subTest(name=name):
                self.assertTrue((helpers / name).is_file(), f"unreviewed dependency: {name}")


if __name__ == "__main__":
    unittest.main()
