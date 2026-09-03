"""Data model and file compatibility for PAPARA(ZZ)I text files."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import os
import shutil
import tempfile


@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Segment:
    start: Point
    end: Point


@dataclass(frozen=True, slots=True)
class Annotation:
    point: Point
    keyword: str
    length: Segment | None = None
    width: Segment | None = None

    @classmethod
    def parse(cls, line: str) -> "Annotation":
        fields = line.rstrip("\r\n").split("\t")
        if len(fields) not in (3, 7, 11):
            raise ValueError(
                f"Annotation benötigt 3, 7 oder 11 Tab-Felder, gefunden: {len(fields)}"
            )
        if not fields[2].strip():
            raise ValueError("Das Keyword einer Annotation darf nicht leer sein")
        numbers = [float(value) for value in fields[:2]]
        length = None
        width = None
        if len(fields) >= 7:
            values = [float(value) for value in fields[3:7]]
            length = Segment(Point(values[0], values[1]), Point(values[2], values[3]))
        if len(fields) == 11:
            values = [float(value) for value in fields[7:11]]
            width = Segment(Point(values[0], values[1]), Point(values[2], values[3]))
        return cls(Point(*numbers), fields[2], length, width)

    def format(self) -> str:
        fields = [_number(self.point.x), _number(self.point.y), self.keyword]
        if self.length is not None:
            fields.extend(
                _number(value)
                for value in (
                    self.length.start.x,
                    self.length.start.y,
                    self.length.end.x,
                    self.length.end.y,
                )
            )
        if self.width is not None:
            if self.length is None:
                raise ValueError("Eine Breitenmessung benötigt eine Längenmessung")
            fields.extend(
                _number(value)
                for value in (
                    self.width.start.x,
                    self.width.start.y,
                    self.width.end.x,
                    self.width.end.y,
                )
            )
        return "\t".join(fields)

    def renamed(self, keyword: str, *, keep_measurements: bool = True) -> "Annotation":
        if keep_measurements:
            return replace(self, keyword=keyword)
        return replace(self, keyword=keyword, length=None, width=None)


@dataclass(frozen=True, slots=True)
class ScaleBar:
    start: Point
    end: Point
    metres: float

    @classmethod
    def parse(cls, text: str) -> "ScaleBar":
        values = text.strip().split("\t")
        if len(values) != 5:
            raise ValueError("Maßstabsdatei benötigt fünf Tab-getrennte Zahlen")
        numbers = [float(value) for value in values]
        return cls(Point(numbers[0], numbers[1]), Point(numbers[2], numbers[3]), numbers[4])

    def format(self) -> str:
        return "\t".join(
            _number(value)
            for value in (
                self.start.x,
                self.start.y,
                self.end.x,
                self.end.y,
                self.metres,
            )
        )


@dataclass(frozen=True, slots=True)
class UsableArea:
    kind: str
    points: tuple[Point, ...]

    @classmethod
    def rectangle(cls, start: Point, end: Point) -> "UsableArea":
        left, right = sorted((start.x, end.x))
        top, bottom = sorted((start.y, end.y))
        return cls(
            "rectangle",
            (
                Point(left, top),
                Point(right, top),
                Point(right, bottom),
                Point(left, bottom),
            ),
        )

    @classmethod
    def parse(cls, text: str) -> "UsableArea":
        fields = text.strip().split("\t")
        if not fields:
            raise ValueError("Leere Datei für nutzbare Fläche")
        if fields[0].lower() == "rectangle" and len(fields) == 5:
            x, y, width, height = (float(value) for value in fields[1:])
            return cls.rectangle(Point(x, y), Point(x + width, y + height))
        if fields[0].lower() == "polygon" and len(fields) >= 7 and len(fields) % 2 == 1:
            values = [float(value) for value in fields[1:]]
            return cls(
                "polygon",
                tuple(Point(values[index], values[index + 1]) for index in range(0, len(values), 2)),
            )
        # Compatibility with PAPARA(ZZ)I versions before 2.9.
        if len(fields) == 4:
            x, y, width, height = (float(value) for value in fields)
            return cls.rectangle(Point(x, y), Point(x + width, y + height))
        raise ValueError("Ungültige Datei für nutzbare Fläche")

    def format(self) -> str:
        if self.kind == "rectangle":
            left = min(point.x for point in self.points)
            top = min(point.y for point in self.points)
            right = max(point.x for point in self.points)
            bottom = max(point.y for point in self.points)
            return "\t".join(
                ["rectangle", *(_number(value) for value in (left, top, right - left, bottom - top))]
            )
        if self.kind == "polygon" and len(self.points) >= 3:
            values: list[str] = ["polygon"]
            for point in self.points:
                values.extend((_number(point.x), _number(point.y)))
            return "\t".join(values)
        raise ValueError("Unbekannte oder unvollständige nutzbare Fläche")

    def contains(self, point: Point) -> bool:
        # Ray casting with an explicit edge check.
        inside = False
        count = len(self.points)
        for index, first in enumerate(self.points):
            second = self.points[(index + 1) % count]
            if _point_on_segment(point, first, second):
                return True
            if (first.y > point.y) != (second.y > point.y):
                crossing_x = (second.x - first.x) * (point.y - first.y) / (second.y - first.y) + first.x
                if point.x < crossing_x:
                    inside = not inside
        return inside

    def pixel_area(self) -> float:
        total = 0.0
        for index, first in enumerate(self.points):
            second = self.points[(index + 1) % len(self.points)]
            total += first.x * second.y - second.x * first.y
        return abs(total) / 2.0


def read_annotations(path: Path) -> list[Annotation]:
    if not path.exists():
        return []
    annotations: list[Annotation] = []
    for line_number, line in enumerate(read_text_compatible(path).splitlines(), 1):
        if not line.strip():
            continue
        try:
            annotations.append(Annotation.parse(line))
        except (ValueError, IndexError) as error:
            raise ValueError(f"{path.name}, Zeile {line_number}: {error}") from error
    return annotations


def write_annotations(path: Path, annotations: list[Annotation]) -> None:
    atomic_write(path, "".join(annotation.format() + "\r\n" for annotation in annotations))


def atomic_write(path: Path, text: str) -> None:
    """Replace a text file atomically and retain PAPARA's CRLF line endings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            shutil.copy2(path, backup_path(path))
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def read_text_compatible(path: Path) -> str:
    """Read modern UTF-8 and legacy Windows keyword/annotation files."""
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def backup_path(path: Path) -> Path:
    return path.with_name(path.name + ".bak")


def _number(value: float) -> str:
    # MATLAB used %f throughout its compatibility files.
    return f"{value:.6f}"


def _point_on_segment(point: Point, first: Point, second: Point, epsilon: float = 1e-8) -> bool:
    cross = (point.y - first.y) * (second.x - first.x) - (point.x - first.x) * (
        second.y - first.y
    )
    if abs(cross) > epsilon:
        return False
    return (
        min(first.x, second.x) - epsilon <= point.x <= max(first.x, second.x) + epsilon
        and min(first.y, second.y) - epsilon <= point.y <= max(first.y, second.y) + epsilon
    )
