"""Assertions over collected real game/input observations, never fabricated target files."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import struct
import unittest

REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("SH3_CHECKPOINT_EVIDENCE"), "requires actual checkpoint replay")
class CheckpointGameEvidenceTests(unittest.TestCase):
    def test_playable_checkpoint_has_capture_before_scripted_movement(self):
        run = REPO / os.environ["SH3_CHECKPOINT_EVIDENCE"]
        frames = []
        for row in (run / "launcher/stderr.txt").read_text().splitlines():
            if (row.startswith("peek frame ") and "0072D2C0=000000D2" in row and
                    "008984E0=C66B4B22 008984E8=46973350" in row):
                frames.append(int(row.split()[2].rstrip(":")))
        self.assertGreater(len(frames), 1, "checkpoint never settles before movement")
        captures = run / "launcher/shots"
        self.assertTrue(any((captures / f"frame{frame:05d}.ppm").is_file() for frame in frames[1:]),
                        "missing settled checkpoint image at original player position")

    def test_saved_probe_replays_checkpoint_at_640x480_and_moves_player(self):
        run = REPO / os.environ["SH3_CHECKPOINT_EVIDENCE"]
        logs = (run / "launcher/stderr.txt").read_text()
        live = []
        for row in logs.splitlines():
            if not row.startswith("peek frame "):
                continue
            values = {int(k, 16): int(v, 16) for k, v in re.findall(r"([0-9A-F]{8})=([0-9A-F]{8})", row)}
            if values.get(0x72D2C0) == 210:
                self.assertEqual((values[0x72BFD0], values[0x72BFD4]), (640, 480))
                f32 = lambda address: struct.unpack("<f", struct.pack("<I", values[address]))[0]
                live.append((f32(0x8984E8), f32(0x8984E0)))
        self.assertGreater(len(live), 1, "saved probe did not reach matched playable checkpoint")
        self.assertAlmostEqual(live[0][0], 19353.65625, delta=1)
        self.assertAlmostEqual(live[0][1], -15058.783203125, delta=1)
        self.assertGreater(max(math.dist(live[0], point) for point in live), 5, "input did not move Heather")
        self.assertIn("ExitProcess(0)", logs)
        for error in ("FATAL", "framebuffer incomplete", "GL error", "shader compile failed"):
            self.assertNotIn(error, logs)
        state = json.loads((run / "status.json").read_text())
        for stage in ("execution", "collection", "launcher-collection", "service-collection"):
            self.assertEqual(state[stage], 0, stage)
        self.assertIn("OK", (run / "device/checkpoint-source-after.txt").read_text())


@unittest.skipUnless(os.environ.get("SH3_FRONTEND_INVENTORY"), "requires actual frontend-service inventory")
class FrontendInventoryEvidenceTests(unittest.TestCase):
    def test_current_frontend_service_and_launcher_cgroup_are_recorded(self):
        run = REPO / os.environ["SH3_FRONTEND_INVENTORY"]
        snapshot = run / "device/frontend-service.txt"
        self.assertTrue(snapshot.is_file(), "saved inventory lacks current frontend service/cgroup evidence")
        text = snapshot.read_text()
        for expected in ["systemd ", "Id=emulationstation.service", "LoadState=loaded",
                         "ActiveState=active", "ControlGroup=", "KillMode=", "[probe-cgroup]"]:
            self.assertIn(expected, text)


@unittest.skipUnless(os.environ.get("SH3_DATA_EVIDENCE"), "requires actual uploaded-data hash run")
class GameDataEvidenceTests(unittest.TestCase):
    def test_all_uploaded_asset_hashes_match_independent_local_originals(self):
        run = REPO / os.environ["SH3_DATA_EVIDENCE"]
        state = json.loads((run / "status.json").read_text())
        self.assertEqual(state["execution"], 0)
        self.assertEqual(state["collection"], 0)
        self.assertEqual(state["launcher-collection"], 0)
        logs = (run / "launcher/stdout.txt").read_text()
        self.assertIn("Input profile: owner-cd-d851669e", logs)
        actual = {row.split("\t")[1]: row.split("\t")[2]
                  for row in logs.splitlines() if row.startswith("data-sha256\t")}
        required = {row for row in (REPO / "scripts/required-data.txt").read_text().splitlines()
                    if row and not row.startswith("#")}
        self.assertEqual(set(actual), required, "target lacks full original-asset identities")
        original = Path(os.environ.get("SH3_TEST_OWNER_DATA", REPO / "SILENT HILL 3"))
        for name in sorted(required):
            digest = hashlib.sha256()
            with (original / name).open("rb") as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
            self.assertEqual(actual[name], digest.hexdigest(), name)


@unittest.skipUnless(os.environ.get("SH3_GAME_EVIDENCE"), "requires actual native game run")
class GameSessionEvidenceTests(unittest.TestCase):
    def test_native_game_presents_and_closes_without_owned_process_or_firmware_change(self):
        run = REPO / os.environ["SH3_GAME_EVIDENCE"]
        state = json.loads((run / "status.json").read_text())
        for name in ["execution", "collection", "launcher-collection"]:
            self.assertEqual(state[name], 0, name)
        self.assertEqual((run / "launcher/exit-status.txt").read_text().strip(), "0")
        logs = (run / "launcher/stderr.txt").read_text()
        for expected in ["output: requested 640x480 drawable 640x480", "CreateDevice 640x480",
                         "GL: Mali-G31 / OpenGL ES 3.2", "ExitProcess(0)"]:
            self.assertIn(expected, logs)
        for failure in ["FATAL", "shader compile failed", "program link failed"]:
            self.assertNotIn(failure, logs)
        capture = run / "launcher/present.ppm"
        if not capture.is_file():
            sequence = sorted((run / "launcher/shots").glob("frame*.ppm"))
            self.assertTrue(sequence, "missing presented game-frame evidence")
            capture = sequence[-1]
        header = capture.read_bytes().split(b"\n", 3)
        self.assertEqual(header[:3], [b"P6", b"640 480", b"255"])
        self.assertEqual(len(header[3]), 640 * 480 * 3)
        self.assertGreater(len(set(header[3])), 32)
        before = (run / "device/frontend-before.txt").read_text().splitlines()
        after = (run / "device/frontend-after.txt").read_text().splitlines()
        if (run / "service").is_dir():
            self.assertNotEqual({row.split()[0] for row in before}, {row.split()[0] for row in after})
            self.assertTrue(after)
        else:
            self.assertEqual({row.split()[0] for row in before}, {row.split()[0] for row in after})
        self.assertTrue(before)
        self.assertEqual((run / "device/runtime-pids-after.txt").read_text(), "")
        self.assertEqual((run / "device/port-mounts-before.txt").read_text(),
                         (run / "device/port-mounts-after.txt").read_text())
        firmware = (run / "device/firmware-libraries-after.txt").read_text().splitlines()
        self.assertTrue(firmware)
        self.assertTrue(all(row.endswith(": OK") for row in firmware))


@unittest.skipUnless(os.environ.get("SH3_GAME_SERVICE_EVIDENCE"), "requires actual detached game run")
class FrontendSessionEvidenceTests(unittest.TestCase):
    def test_native_session_stops_frontend_and_restores_it_after_normal_game_close(self):
        run = REPO / os.environ["SH3_GAME_SERVICE_EVIDENCE"]
        service = run / "service"
        self.assertTrue(service.is_dir(), "missing actual detached-service evidence")
        state = json.loads((run / "status.json").read_text())
        self.assertEqual(state["service-collection"], 0)
        self.assertEqual((service / "exit-status.txt").read_text().strip(), "0")
        self.assertNotIn("emulationstation.service", (service / "cgroup.txt").read_text())
        self.assertIn("sh3-r36s-game.service", (service / "cgroup.txt").read_text())
        self.assertIn("ActiveState=inactive", (service / "frontend-game.txt").read_text())
        self.assertIn("MainPID=0", (service / "frontend-game.txt").read_text())
        self.assertIn("ActiveState=active", (service / "frontend-restored.txt").read_text())
        self.assertFalse((service / "frontend-stopped").exists())
        for name in ["memory-before.txt", "memory-game.txt", "memory-restored.txt"]:
            self.assertIn("Mem:", (service / name).read_text())


@unittest.skipUnless(os.environ.get("SH3_PERFORMANCE_EVIDENCE"), "requires actual low-overhead game probe")
class GamePerformanceEvidenceTests(unittest.TestCase):
    def test_sparse_probe_records_clock_memory_and_native_process_samples(self):
        run = REPO / os.environ["SH3_PERFORMANCE_EVIDENCE"]
        samples = run / "service/performance.txt"
        self.assertTrue(samples.is_file(), "missing repeatable live performance samples")
        text = samples.read_text()
        self.assertGreaterEqual(text.count("[sample "), 3)
        for expected in ["scaling_governor", "scaling_cur_freq", "MemAvailable:",
                         "VmRSS:", "cpu ", "[native-process "]:
            self.assertIn(expected, text)
        probe = (run / "device/game-probe.txt").read_text()
        self.assertIn("continuous_capture=0", probe)
        frames = sorted(int(path.stem.removeprefix("frame"))
                        for path in (run / "launcher/shots").glob("frame*.ppm"))
        sparse = [frame for frame in frames if frame >= 10]
        self.assertTrue(sparse, "missing sparse scene captures")
        self.assertTrue(all(right - left >= 60 for left, right in zip(sparse, sparse[1:])),
                        "probe captures too often after startup")


@unittest.skipUnless(os.environ.get("SH3_GAME_PHYSICAL_EVIDENCE"), "requires physical game exit observation")
class PhysicalGameEvidenceTests(unittest.TestCase):
    def test_completed_physical_session_collects_created_checkpoint_without_game_assets(self):
        launches = REPO / os.environ["SH3_GAME_PHYSICAL_EVIDENCE"] / "device/previous-launches"
        session = launches / "20261112T204903Z-230962/session"
        self.assertEqual((session / "savedata/data.001").stat().st_size, 9952)
        self.assertEqual((session / "savedata/data.sys").stat().st_size, 296)
        self.assertFalse((session / "data").exists())

    def test_completed_physical_session_preserves_display_settings_for_replay(self):
        launches = REPO / os.environ["SH3_GAME_PHYSICAL_EVIDENCE"] / "device/previous-launches"
        candidates = [path for path in launches.iterdir()
                      if (path / "stderr.txt").is_file() and
                      "window close requested: Select+Start" in (path / "stderr.txt").read_text()]
        self.assertTrue(candidates, "no completed physical game session")
        session = sorted(candidates)[-1] / "session"
        self.assertIn("resolution=640x480", (session / "sh3.ini").read_text())
        self.assertTrue((session / "savedata/disp.ini").is_file(), "missing game display preferences")

    def test_physical_select_start_exit_and_frontend_recovery_are_collected(self):
        run = REPO / os.environ["SH3_GAME_PHYSICAL_EVIDENCE"]
        launches = run / "device/previous-launches"
        candidates = [path for path in launches.iterdir()
                      if (path / "stderr.txt").is_file() and
                      "window close requested: Select+Start" in (path / "stderr.txt").read_text()]
        self.assertTrue(candidates, "physical game Select+Start exit not observed")
        launch = sorted(candidates)[-1]
        logs = (launch / "stderr.txt").read_text()
        self.assertIn("ExitProcess(0)", logs)
        self.assertIn("GL: Mali-G31 / OpenGL ES 3.2", logs)
        self.assertEqual((launch / "exit-status.txt").read_text().strip(), "0")
        service = launch / "service"
        self.assertEqual((service / "exit-status.txt").read_text().strip(), "0")
        self.assertIn("ActiveState=inactive", (service / "frontend-game.txt").read_text())
        self.assertIn("ActiveState=active", (service / "frontend-restored.txt").read_text())
        self.assertFalse((service / "frontend-stopped").exists())


if __name__ == "__main__":
    unittest.main()
