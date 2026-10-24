import contextlib
import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from asset_sieve import __version__
from asset_sieve.cli import main
from asset_sieve.core import markdown, scan


class AssetSieveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_version_is_consistent_across_package_metadata_and_report(self):
        project = Path(__file__).resolve().parents[1]
        self.assertEqual((project / "VERSION").read_text(encoding="utf-8").strip(), __version__)
        metadata = (project / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'(?m)^version = "([^"]+)"$', metadata)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), __version__)
        self.assertEqual(scan(self.root)["version"], __version__)

    def make_image(self, relative, size=(12, 6), color=(30, 60, 90, 255)):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGBA", size, color).save(path)
        return path

    def test_groups_byte_identical_images_and_returns_inventory(self):
        first = self.make_image("Textures/stone.png")
        second = self.root / "Textures" / "stone-copy.png"
        shutil.copyfile(first, second)

        report = scan(self.root)

        self.assertEqual(report["summary"]["images"], 2)
        self.assertEqual(report["summary"]["duplicates"], 1)
        self.assertEqual(report["summary"]["duplicate_bytes"], first.stat().st_size)
        self.assertEqual([item["path"] for item in report["assets"]],
                         ["Textures/stone-copy.png", "Textures/stone.png"])
        self.assertEqual(report["assets"][0]["sha256"], report["assets"][1]["sha256"])

    def test_reports_size_and_dimension_thresholds(self):
        image = self.make_image("huge.png", size=(20, 5))

        report = scan(self.root, max_file_mb=0.000001, max_dimension=10)

        self.assertEqual(report["summary"]["oversized_files"], 1)
        self.assertEqual(report["summary"]["oversized_dimensions"], 1)
        self.assertEqual(report["oversized_dimensions"][0]["width"], 20)
        self.assertGreater(report["oversized_files"][0]["bytes"], 0)
        self.assertGreater(image.stat().st_size, 0)

    def test_lists_unreadable_supported_images(self):
        broken = self.root / "broken.png"
        broken.write_bytes(b"not an image")

        report = scan(self.root)

        self.assertEqual(report["summary"]["unreadable"], 1)
        self.assertEqual(report["unreadable"][0]["path"], "broken.png")

    def test_detects_truncated_image_after_valid_header(self):
        image_path = self.make_image("truncated.png")
        image_path.write_bytes(image_path.read_bytes()[:-12])

        report = scan(self.root)

        self.assertEqual(report["summary"]["unreadable"], 1)
        self.assertEqual(report["unreadable"][0]["path"], "truncated.png")

    def test_excludes_named_directories_and_unsupported_files(self):
        self.make_image("Cache/hidden.png")
        self.make_image("Textures/visible.png")
        (self.root / "notes.txt").write_text("not an image", encoding="utf-8")

        report = scan(self.root, excludes=["Cache"])

        self.assertEqual(report["summary"]["images"], 1)
        self.assertEqual(report["assets"][0]["path"], "Textures/visible.png")

    def test_rejects_invalid_limits(self):
        with self.assertRaises(ValueError):
            scan(self.root, max_file_mb=0)
        with self.assertRaises(ValueError):
            scan(self.root, max_file_mb=float("nan"))
        with self.assertRaises(ValueError):
            scan(self.root, max_dimension=0)
        for invalid_limit in (float("nan"), float("inf"), 10.5, True):
            with self.subTest(max_dimension=invalid_limit):
                with self.assertRaisesRegex(ValueError, "max_dimension must be a positive integer"):
                    scan(self.root, max_dimension=invalid_limit)

    def test_markdown_contains_findings_and_non_mutating_notice(self):
        image = self.make_image("a.png")
        shutil.copyfile(image, self.root / "b.png")
        output = markdown(scan(self.root))

        self.assertIn("## Identical files", output)
        self.assertIn("## By folder", output)
        self.assertIn("(root)", output)
        self.assertIn("a.png", output)
        self.assertIn("does not modify or delete source files", output)

    def test_cli_writes_json_and_markdown_reports(self):
        image = self.make_image("a.png")
        shutil.copyfile(image, self.root / "b.png")
        json_path = self.root / "report.json"
        md_path = self.root / "report.md"
        stdout = io.StringIO()
        with patch("sys.argv", ["asset-sieve", str(self.root), "--json", str(json_path), "--md", str(md_path)]):
            with contextlib.redirect_stdout(stdout):
                status = main()

        self.assertEqual(status, 0)
        self.assertEqual(json.loads(json_path.read_text(encoding="utf-8"))["summary"]["duplicates"], 1)
        self.assertIn("Identical files", md_path.read_text(encoding="utf-8"))
        self.assertIn("2 images", stdout.getvalue())

    def test_cli_warning_exit_code_is_opt_in(self):
        image = self.make_image("a.png")
        shutil.copyfile(image, self.root / "b.png")
        with patch("sys.argv", ["asset-sieve", str(self.root), "--fail-on-warning"]):
            with contextlib.redirect_stdout(io.StringIO()):
                status = main()
        self.assertEqual(status, 2)


if __name__ == "__main__":
    unittest.main()
