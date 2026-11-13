"""Physical-input evidence checks; fixtures cannot pass handheld controls."""
import json
import os
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("SH3_INPUT_INVENTORY"), "requires actual input inventory")
class InputInventoryEvidenceTests(unittest.TestCase):
    def test_current_controller_mapping_and_kernel_identity_are_collected(self):
        run = REPO / os.environ["SH3_INPUT_INVENTORY"] / "device"
        configs = run / "input-configs"
        self.assertTrue(configs.is_dir(), "inventory lacks current input mapping sources")
        kernel = (run / "controllers.txt").read_text()
        mappings = list(configs.glob("*/gamecontrollerdb.txt"))
        self.assertTrue(mappings, "installed PortMaster SDL mappings missing")
        database = "\n".join(path.read_text() for path in mappings)
        controllers = [node for path in configs.glob("es-input-*.cfg")
                       for node in ET.parse(path).getroot().findall("inputConfig")
                       if node.get("type") == "joystick" and node.get("deviceName", "") in kernel]
        self.assertTrue(controllers, "no configured controller matches kernel inventory")
        self.assertTrue(any(node.get("deviceGUID", "missing") in database for node in controllers),
                        "configured controller missing from installed SDL database")


@unittest.skipUnless(os.environ.get("SH3_INPUT_SESSION_EVIDENCE"), "requires completed handheld input run")
class InputSessionEvidenceTests(unittest.TestCase):
    def test_handheld_control_set_reaches_game_and_physical_exit_restores_frontend(self):
        runs = [REPO / value for value in os.environ["SH3_INPUT_SESSION_EVIDENCE"].split(os.pathsep)]
        traces, runtimes = [], set()
        for run in runs:
            status = json.loads((run / "status.json").read_text())
            self.assertIs(status.get("physical_controls"), True, "run used automated scene input")
            for stage in ("execution", "collection", "launcher-collection", "service-collection"):
                self.assertEqual(status[stage], 0, stage)
            settings = (run / "service/physical-controls.txt").read_text()
            for value in ("scripted_input=0", "input_log=1", "frame_capture=0", "performance_sampler=0"):
                self.assertIn(value, settings)
            logs = (run / "launcher/stderr.txt").read_text()
            mapping = next((line for line in logs.splitlines() if line.startswith("input controller mapping=")), "")
            # SDL 2.26+ stores a name CRC in GUID bytes2/3; ES/PortMaster may leave it zero.
            self.assertRegex(mapping, r"^input controller mapping=1900[0-9a-f]{4}4b4800000011000000010000,GO-Super Gamepad,")
            self.assertRegex(mapping, r"lefttrigger:b6.*righttrigger:b7")
            self.assertTrue("GL: Mali-G31 / OpenGL ES 3.2" in logs, "firmware GLES provider missing")
            self.assertTrue("ExitProcess(0)" in logs, "orderly game close missing")
            runtimes.add((run / "device/runtime.sha256").read_text().split()[0])
            traces.append(logs)
            for scope in ("launcher", "service"):
                self.assertEqual((run / scope / "exit-status.txt").read_text().strip(), "0")
            self.assertIn("ActiveState=active", (run / "service/frontend-restored.txt").read_text())
            self.assertEqual((run / "device/runtime-pids-after.txt").read_text(), "")
            self.assertEqual((run / "device/port-mounts-before.txt").read_text(),
                             (run / "device/port-mounts-after.txt").read_text())
            firmware = (run / "device/firmware-libraries-after.txt").read_text().splitlines()
            self.assertTrue(firmware)
            self.assertTrue(all(row.endswith(": OK") for row in firmware))
        self.assertEqual(len(runtimes), 1, "input coverage cannot mix different runtime builds")
        logs = "\n".join(traces)
        states = re.findall(r"input state ticks=\d+ axes=(-?\d+),(-?\d+),(-?\d+),(-?\d+),"
                            r"(-?\d+),(-?\d+) buttons=([0-9a-f]+) pov=(-?\d+)", logs)
        self.assertTrue(states, "no input states reached game's controller reads")
        axes = [tuple(map(int, row[:6])) for row in states]
        for index, name in enumerate(("left X", "left Y", "right X", "right Y")):
            with self.subTest(control=name):
                self.assertLess(min(row[index] for row in axes), -16000, name + " negative missing")
                self.assertGreater(max(row[index] for row in axes), 16000, name + " positive missing")
        for index, name in ((4, "L2"), (5, "R2")):
            self.assertTrue({0, 32767}.issubset({row[index] for row in axes}), name + " release/press missing")
        buttons = [int(row[6], 16) for row in states]
        for index, name in enumerate(("X", "A", "B", "Y", "L1", "R1", "L2", "R2",
                                      "Select", "Start", "L3", "R3")):
            self.assertTrue(any(value & (1 << index) for value in buttons), name + " press missing")
        self.assertTrue({0, 9000, 18000, 27000}.issubset({int(row[7]) for row in states}),
                        "d-pad cardinal direction missing")
        self.assertTrue("window close requested: Select+Start" in traces[-1],
                        "final run must demonstrate physical exit; deadline cannot pass")


if __name__ == "__main__":
    unittest.main()
