from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from paparazzi_py.keywords import KeywordList, color_from_id
from paparazzi_py.model import (
    Annotation,
    Point,
    ScaleBar,
    Segment,
    UsableArea,
    backup_path,
    read_annotations,
    read_text_compatible,
    write_annotations,
)


class AnnotationTests(unittest.TestCase):
    def test_matlab_formats_round_trip(self) -> None:
        samples = (
            "12.500000\t20.250000\tSand",
            "12.500000\t20.250000\tSand\t1.000000\t2.000000\t3.000000\t4.000000",
            "12.500000\t20.250000\tSand\t1.000000\t2.000000\t3.000000\t4.000000\t5.000000\t6.000000\t7.000000\t8.000000",
        )
        for sample in samples:
            with self.subTest(sample=sample):
                self.assertEqual(Annotation.parse(sample).format(), sample)

    def test_annotation_files_use_crlf_and_are_readable(self) -> None:
        annotation = Annotation(
            Point(10, 20),
            "Kies",
            Segment(Point(1, 2), Point(3, 4)),
            Segment(Point(5, 6), Point(7, 8)),
        )
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "annotations.txt"
            write_annotations(path, [annotation])
            self.assertTrue(path.read_bytes().endswith(b"\r\n"))
            self.assertEqual(read_annotations(path), [annotation])
            changed = annotation.renamed("Geröll")
            write_annotations(path, [changed])
            self.assertEqual(read_annotations(backup_path(path)), [annotation])
            self.assertEqual(read_annotations(path), [changed])

    def test_legacy_cp1252_text_is_supported(self) -> None:
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "legacy.txt"
            path.write_bytes("Geröll\r\n".encode("cp1252"))
            self.assertEqual(read_text_compatible(path), "Geröll\r\n")

    def test_scale_round_trip(self) -> None:
        scale = ScaleBar(Point(1, 2), Point(11, 2), 0.5)
        self.assertEqual(ScaleBar.parse(scale.format()), scale)


class AreaTests(unittest.TestCase):
    def test_rectangle_format_and_contains(self) -> None:
        area = UsableArea.rectangle(Point(50, 40), Point(10, 20))
        self.assertEqual(area.format(), "rectangle\t10.000000\t20.000000\t40.000000\t20.000000")
        self.assertTrue(area.contains(Point(20, 30)))
        self.assertTrue(area.contains(Point(10, 20)))
        self.assertFalse(area.contains(Point(5, 30)))
        self.assertEqual(area.pixel_area(), 800)

    def test_polygon_round_trip(self) -> None:
        area = UsableArea("polygon", (Point(0, 0), Point(10, 0), Point(0, 10)))
        self.assertEqual(UsableArea.parse(area.format()), area)
        self.assertTrue(area.contains(Point(2, 2)))
        self.assertFalse(area.contains(Point(8, 8)))
        self.assertEqual(area.pixel_area(), 50)


class KeywordTests(unittest.TestCase):
    def test_individual_colours_and_groups(self) -> None:
        keywords = KeywordList.parse(
            "#MODE=INDIVIDUAL\n#DEFAULT=2\n_Grund_\nSand\t8\nKies\n"
        )
        self.assertEqual([entry.name for entry in keywords.selectable], ["Sand", "Kies"])
        self.assertEqual(keywords.color_for("Sand"), color_from_id(8))
        self.assertEqual(keywords.color_for("Kies"), color_from_id(2))

    def test_single_colour(self) -> None:
        keywords = KeywordList.parse("#MODE=SINGLE\n#COLOR=5\nSand\t8\nKies\n")
        self.assertEqual(keywords.color_for("Sand"), color_from_id(5))
        self.assertEqual(keywords.color_for("Kies"), color_from_id(5))


if __name__ == "__main__":
    unittest.main()
