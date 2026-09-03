from __future__ import annotations

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image

from paparazzi_py.analysis import export_results
from paparazzi_py.model import Annotation, Point, ScaleBar, Segment, UsableArea
from paparazzi_py.project import Project


class ProjectAndAnalysisTests(unittest.TestCase):
    def test_legacy_rectangle_folder_is_migrated(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            Image.new("RGB", (20, 10), "gray").save(root / "bild.png")
            legacy = root / "test_rectangle"
            legacy.mkdir()
            (legacy / "bild.txt").write_text("1\t2\t3\t4\r\n", encoding="ascii")
            project = Project(root, "test")
            area = project.load_usable_area(root / "bild.png")
            self.assertIsNotNone(area)
            self.assertEqual(area.pixel_area(), 12)

    def test_layout_ignore_and_export(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "bild_eins.png"
            second = root / "bild_zwei.jpg"
            Image.new("RGB", (100, 50), "gray").save(first)
            Image.new("RGB", (40, 40), "navy").save(second)
            project = Project(root, "Ada Lovelace")
            self.assertEqual(project.user, "ada_lovelace")
            self.assertEqual([path.name for path in project.images()], ["bild_eins.png", "bild_zwei.jpg"])

            annotations = [
                Annotation(Point(10, 10), "Sand", Segment(Point(10, 10), Point(20, 10))),
                Annotation(Point(75, 25), "Kies"),
            ]
            project.save_annotations(first, annotations)
            project.save_scale(first, ScaleBar(Point(0, 0), Point(10, 0), 1.0))
            project.save_usable_area(first, UsableArea.rectangle(Point(0, 0), Point(50, 50)))
            self.assertEqual(project.load_annotations(first), annotations)

            changed, files = project.replace_keyword("Kies", "Geröll")
            self.assertEqual((changed, files), (1, 1))
            annotations[1] = annotations[1].renamed("Geröll")
            self.assertEqual(project.load_annotations(first), annotations)

            project.set_ignored(second, True)
            self.assertEqual(project.ignored_images(), {"bild_zwei.jpg"})
            project.set_ignored(second, False)
            self.assertEqual(project.ignored_images(), set())

            exported = export_results(project, datetime(2026, 9, 3, 12, 0, 0))
            whole = exported / "abundance-tables" / "ada_lovelace_WholeImage_Abundances.txt"
            usable = exported / "abundance-tables" / "ada_lovelace_UsableArea_Abundances.txt"
            whole_lines = whole.read_text(encoding="utf-8").splitlines()
            usable_lines = usable.read_text(encoding="utf-8").splitlines()
            self.assertEqual(whole_lines[0].split("\t")[-2:], ["Geröll", "Sand"])
            self.assertEqual(whole_lines[1].split("\t")[0], "bild_eins_100x50")
            self.assertEqual(whole_lines[1].split("\t")[8], "50.000000")
            self.assertEqual(whole_lines[1].split("\t")[-2:], ["1", "1"])
            self.assertEqual(usable_lines[1].split("\t")[8], "25.000000")
            self.assertEqual(usable_lines[1].split("\t")[-2:], ["0", "1"])
            self.assertTrue((exported / "size-distributions" / "ada_lovelace_Legend.txt").exists())


if __name__ == "__main__":
    unittest.main()
