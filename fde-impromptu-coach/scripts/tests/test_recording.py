"""The recorder choice for the audio practices (pronunciation, legato).

The scenarios live in tests/features/recording.feature; each has exactly one test in
RecordingFeature, named after it and written Given / When / Then;
test_every_scenario_has_one_test_and_back fails if the two drift apart.

Everything runs in-process in a dry-run home: QuickTime helpers are mocked, the
ffmpeg capture class is mocked, and only the ordering of _record_once is measured.
Run from the skill folder:

    python3 -m unittest discover -s scripts/tests -p "test_recording.py" -v
"""
from __future__ import annotations

import os
import re
import unittest
from pathlib import Path
from unittest import mock

from test_coach import Home  # noqa: E402  (also puts scripts/ on sys.path)

from fdecoach import macos, practice  # noqa: E402
from fdecoach.config import Paths, load_config  # noqa: E402

TESTS = Path(__file__).resolve().parent
FEATURE = TESTS / "features" / "recording.feature"


def scenarios() -> list:
    return re.findall(r"^\s*Scenario: (.+?)\s*$", FEATURE.read_text(encoding="utf-8"), re.MULTILINE)


def scenario_test_name(scenario: str) -> str:
    slug = re.sub(r"['’]", "", scenario.lower())
    return "test_" + re.sub(r"[^a-z0-9]+", "_", slug).strip("_")


class RecordingFeature(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Home(claude=False)
        self.addCleanup(self.home.cleanup)
        env = dict(os.environ)
        env.update({"FDE_COACH_HOME": str(self.home.dir / "home"),
                    "FDE_COACH_DRYRUN": "1",
                    "FDE_COACH_RECORDINGS": str(self.home.dir / "movies"),
                    "FDE_COACH_NOW": "2026-11-10T06:00:00"})
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.paths = Paths()
        self.paths.ensure()

    def _record(self, cfg_overrides: dict, quicktime_ok: bool = True) -> dict:
        cfg = load_config(self.paths)
        for dotted, value in cfg_overrides.items():
            node = cfg
            keys = dotted.split(".")
            for k in keys[:-1]:
                node = node.setdefault(k, {})
            node[keys[-1]] = value
        session = {"date": "2026-11-10", "day_number": 42,
                   "deck_path": "/tmp/deck.pptx", "show_path": "/tmp/deck.pptx"}
        dest = None

        def capture_stub(dest_arg, device):  # noqa: ANN001
            nonlocal dest
            dest = dest_arg

            class Cap:
                def start(self, warmup: float = 1.0) -> bool:
                    return True

                def stop(self, min_bytes: int = 100_000):
                    dest.write_bytes(b"\0" * 1024)
                    return dest

            return Cap()

        with mock.patch.object(macos, "quicktime_start_audio_recording", return_value=quicktime_ok) as qt_start, \
                mock.patch.object(macos, "quicktime_stop_audio_save",
                                  side_effect=lambda d, since: (d.write_bytes(b"\0" * 1024), (True, "dry-run"))[1]), \
                mock.patch.object(macos, "quit_app"), \
                mock.patch.object(practice.audio, "AudioCapture", side_effect=capture_stub) as cap:
            result = practice._record_once(session, cfg, self.paths, practice.spec_for("pronunciation"))
        result["_qt_start_called"] = qt_start.called
        result["_capture_called"] = cap.called
        return result

    def test_audio_practices_record_through_ffmpeg_by_default(self):
        # Given the default settings
        # When a pronunciation session records its audio
        result = self._record({})
        # Then ffmpeg captures the take and QuickTime audio recording is never started
        self.assertTrue(result["ok"], result.get("error"))
        self.assertEqual(result["method"], "ffmpeg")
        self.assertTrue(result["_capture_called"])
        self.assertFalse(result["_qt_start_called"])

    def test_quicktime_records_first_when_audio_recorder_is_quicktime(self):
        # Given recording.audio_recorder is set to quicktime
        # When a pronunciation session records its audio
        result = self._record({"recording.audio_recorder": "quicktime"})
        # Then QuickTime starts an audio recording and the ffmpeg capture is never constructed
        self.assertTrue(result["ok"], result.get("error"))
        self.assertTrue(result["method"].startswith("quicktime"), result["method"])
        self.assertTrue(result["_qt_start_called"])
        self.assertFalse(result["_capture_called"])

    def test_a_failed_quicktime_start_falls_back_to_ffmpeg(self):
        # Given recording.audio_recorder is set to quicktime
        # And QuickTime cannot start an audio recording
        # When a pronunciation session records its audio
        result = self._record({"recording.audio_recorder": "quicktime"}, quicktime_ok=False)
        # Then the take is captured through ffmpeg instead and still saved
        self.assertTrue(result["ok"], result.get("error"))
        self.assertEqual(result["method"], "ffmpeg")
        self.assertTrue(result["_qt_start_called"])
        self.assertTrue(result["_capture_called"])

    def test_every_scenario_has_one_test_and_back(self):
        wanted = {scenario_test_name(s) for s in scenarios()} | {"test_every_scenario_has_one_test_and_back"}
        have = {n for n in dir(self) if n.startswith("test_")}
        self.assertEqual(wanted - have, set(), "scenarios without a test")
        self.assertEqual(have - wanted, set(), "tests without a scenario")


if __name__ == "__main__":
    unittest.main()
