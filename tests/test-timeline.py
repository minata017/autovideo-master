import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("autovideo", Path(__file__).resolve().parents[1] / "autovideo.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class TimelineTests(unittest.TestCase):
    def test_scenes_cover_audio_including_pauses(self):
        words = [{"text": "Chào.", "start": .2, "end": 1.5},
                 {"text": "Cuối.", "start": 3, "end": 4.5}]
        scenes = app.build_scenes(words, 5)
        self.assertEqual(scenes[0]["start"], 0)
        self.assertEqual(scenes[-1]["end"], 5)
        for left, right in zip(scenes, scenes[1:]):
            self.assertEqual(left["end"], right["start"])
        self.assertAlmostEqual(sum(s["end"]-s["start"] for s in scenes), 5)

    def test_overlapping_cuts_merge_once_and_words_remap(self):
        keep = app.keep_ranges({"cuts": [{"start": 1, "end": 2}, {"start": 1.5, "end": 3}]}, 5)
        self.assertEqual(keep, [(0, 1), (3, 5)])
        words = [{"text": "bỏ", "start": 2, "end": 2.5}, {"text": "giữ", "start": 3.5, "end": 4}]
        mapped = app.remap_words(words, keep)
        self.assertEqual(len(mapped), 1)
        self.assertAlmostEqual(mapped[0]["start"], 1.5)

    def test_captions_respect_sentence_and_audio_end(self):
        words = [{"text": "Chào.", "start": 0, "end": 1}, {"text": "Cuối", "start": 1.2, "end": 5}]
        groups = app.caption_groups(words, 3)
        self.assertEqual(groups[0]["text"], "Chào.")
        self.assertEqual(groups[-1]["end"], 3)

    def test_invalid_cuts_fail_instead_of_silent_removal(self):
        with self.assertRaises(app.VideoError):
            app.keep_ranges({"cuts": [{"start": 2, "end": 1}]}, 4)
        with self.assertRaises(app.VideoError):
            app.keep_ranges({"cuts": [{"start": 0, "end": 4}]}, 4)

    def test_timestamp_rounding_carries_seconds(self):
        self.assertEqual(app.stamp(59.9999), "00:01:00,000")
        self.assertEqual(app.stamp(59.9999, True), "0:01:00.00")


if __name__ == "__main__":
    unittest.main()
