import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "validate_assets.py"


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.image = Image.new("RGBA", (8, 4))
        self.image.putpixel((1, 1), (255, 0, 0, 255))
        self.mapping = {
            "sourceCommit": "a" * 40, "atlasPath": "atlas.webp", "atlasSha256": "",
            "width": 8, "height": 4, "columns": 2, "rows": 1,
            "cellWidth": 4, "cellHeight": 4, "unmappedRows": [],
            "states": {"idle": {"row": 0, "columns": [0], "fps": None, "loop": None,
                                "status": "provisional", "evidence": "test"}},
        }
        (self.root / "pet.json").write_text(json.dumps({"spritesheetPath": "atlas.webp"}))

    def run_validator(self, hash_override=None):
        atlas = self.root / "atlas.webp"
        self.image.save(atlas, "WEBP", lossless=True)
        self.mapping["atlasSha256"] = hash_override or hashlib.sha256(atlas.read_bytes()).hexdigest()
        map_path = self.root / "map.json"
        map_path.write_text(json.dumps(self.mapping))
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), "--map", str(map_path)],
                                capture_output=True, text=True, check=False)
        return result.returncode, json.loads(result.stdout)

    def test_valid_map(self):
        code, result = self.run_validator()
        self.assertEqual(code, 0)
        self.assertEqual((result["nonemptyCells"], result["emptyCells"]), (1, 1))

    def test_out_of_range_and_empty_assigned_cell_fail(self):
        self.mapping["states"]["idle"]["columns"] = [2]
        code, result = self.run_validator()
        self.assertNotEqual(code, 0)
        self.assertIn("column out of range", result["errors"][0])
        self.mapping["states"]["idle"]["columns"] = [1]
        code, result = self.run_validator()
        self.assertNotEqual(code, 0)
        self.assertTrue(any("empty assigned cell 0,1" in error for error in result["errors"]))

    def test_unexpected_nonempty_and_boundary_fail(self):
        self.image.putpixel((5, 1), (255, 0, 0, 255))
        self.image.putpixel((0, 1), (255, 0, 0, 255))
        code, result = self.run_validator()
        self.assertNotEqual(code, 0)
        self.assertIn("unexpected non-empty cell 0,1", result["errors"])
        self.assertIn("alpha touches cell boundary 0,0", result["errors"])

    def test_overlapping_cells_fail(self):
        self.mapping["states"]["idle"]["columns"] = [0, 0]
        code, result = self.run_validator()
        self.assertNotEqual(code, 0)
        self.assertIn("duplicate or overlapping cell", result["errors"][0])

    def test_hash_and_frame_duration_mismatch_fail(self):
        code, result = self.run_validator(hash_override="b" * 64)
        self.assertNotEqual(code, 0)
        self.assertIn("SHA-256 does not match", result["errors"][0])
        state = self.mapping["states"]["idle"]
        del state["fps"]
        state["durationMs"] = [100, 100]
        code, result = self.run_validator()
        self.assertNotEqual(code, 0)
        self.assertIn("invalid durationMs", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
