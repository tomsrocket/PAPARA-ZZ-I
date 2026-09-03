"""Analysis exports compatible with the intent and layout of PAPARA(ZZ)I 3.0."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from math import atan2, degrees, hypot, isnan
from pathlib import Path
from statistics import mean, median, pstdev, stdev

from .model import Annotation, ScaleBar, UsableArea, atomic_write
from .project import Project


@dataclass(slots=True)
class ImageResult:
    name: str
    width: int
    height: int
    annotations: list[Annotation]
    usable_annotations: list[Annotation]
    scale: ScaleBar | None
    usable_area: UsableArea | None

    @property
    def scale_pixels(self) -> float:
        if self.scale is None:
            return 0.0
        return hypot(
            self.scale.end.x - self.scale.start.x,
            self.scale.end.y - self.scale.start.y,
        )

    @property
    def metres_per_pixel(self) -> float:
        pixels = self.scale_pixels
        return self.scale.metres / pixels if self.scale is not None and pixels else 0.0

    @property
    def whole_area_m2(self) -> float:
        return self.width * self.height * self.metres_per_pixel**2

    @property
    def usable_area_m2(self) -> float:
        if self.usable_area is None:
            return self.whole_area_m2
        return self.usable_area.pixel_area() * self.metres_per_pixel**2


def export_results(project: Project, now: datetime | None = None) -> Path:
    """Write free-annotation summaries and return the export directory."""
    results = _collect_results(project)
    keywords = sorted(
        {annotation.keyword for result in results for annotation in result.annotations},
        key=str.casefold,
    )
    timestamp = (now or datetime.now()).strftime("%Y-%m-%dT%H-%M-%S")
    root = project.image_dir / "data-export" / f"{timestamp}_{project.user}" / "free-annotations"
    abundance_dir = root / "abundance-tables"
    angle_dir = root / "angle-calculations"
    size_dir = root / "size-distributions"
    for directory in (abundance_dir, angle_dir, size_dir):
        directory.mkdir(parents=True, exist_ok=True)

    _write_abundance(
        abundance_dir / f"{project.user}_WholeImage_Abundances.txt",
        results,
        keywords,
        usable=False,
    )
    _write_abundance(
        abundance_dir / f"{project.user}_UsableArea_Abundances.txt",
        results,
        keywords,
        usable=True,
    )
    _write_angles(
        angle_dir / f"{project.user}_WholeImage_Angles.txt",
        results,
        keywords,
        usable=False,
    )
    _write_angles(
        angle_dir / f"{project.user}_UsableArea_Angles.txt",
        results,
        keywords,
        usable=True,
    )
    _write_sizes(size_dir, project.user, results, keywords, usable=False)
    _write_sizes(size_dir, project.user, results, keywords, usable=True)
    _write_legend(size_dir / f"{project.user}_Legend.txt", keywords)
    return root


def _collect_results(project: Project) -> list[ImageResult]:
    ignored = project.ignored_images()
    results: list[ImageResult] = []
    for image_path in project.images():
        annotation_path = project.annotation_file(image_path)
        if image_path.name in ignored or not annotation_path.exists():
            continue
        width, height = project.image_size(image_path)
        annotations = project.load_annotations(image_path)
        area = project.load_usable_area(image_path)
        usable = annotations if area is None else [a for a in annotations if area.contains(a.point)]
        results.append(
            ImageResult(
                annotation_path.stem,
                width,
                height,
                annotations,
                usable,
                project.load_scale(image_path),
                area,
            )
        )
    return results


def _write_abundance(
    path: Path,
    results: list[ImageResult],
    keywords: list[str],
    *,
    usable: bool,
) -> None:
    area_header = "usable_area_m2" if usable else "image_area_m2"
    header = [
        "image_name",
        "width_pxl",
        "height_pxl",
        "width_m",
        "height_m",
        "scale_pxl",
        "scale_m",
        "area_used",
        area_header,
        "number_of_points",
        *keywords,
    ]
    rows = ["\t".join(header)]
    total_area = 0.0
    total_counts: Counter[str] = Counter()
    lengths: dict[str, list[float]] = defaultdict(list)
    for result in results:
        annotations = result.usable_annotations if usable else result.annotations
        area = result.usable_area_m2 if usable else result.whole_area_m2
        area_used = "selected area" if usable and result.usable_area is not None else "whole image"
        scale_m = result.scale.metres if result.scale is not None else 0.0
        mpp = result.metres_per_pixel
        counts = Counter(annotation.keyword for annotation in annotations)
        total_counts.update(counts)
        total_area += area
        for annotation in annotations:
            if annotation.length is not None and mpp:
                lengths[annotation.keyword].append(_segment_pixels(annotation.length) * mpp)
        unique_points = len({(annotation.point.x, annotation.point.y) for annotation in annotations})
        row = [
            result.name,
            str(result.width),
            str(result.height),
            _float(result.width * mpp),
            _float(result.height * mpp),
            _float(result.scale_pixels),
            _float(scale_m),
            area_used,
            _float(area),
            str(unique_points),
            *(str(counts[keyword]) for keyword in keywords),
        ]
        rows.append("\t".join(row))

    label_padding = [""] * 9
    rows.append("\t".join([*label_padding, "Total annotations (in images with scale)", *(_float(total_counts[k]) for k in keywords)]))
    rows.append(
        "\t".join(
            [
                *label_padding,
                "Density (ind/m2)",
                *(_float(total_counts[k] / total_area if total_area else float("nan")) for k in keywords),
            ]
        )
    )
    rows.append("")
    statistics_rows = (
        ("Number of length measurements", lambda values: float(len(values))),
        ("Min length [m]", lambda values: min(values) if values else float("nan")),
        ("Max length [m]", lambda values: max(values) if values else float("nan")),
        ("Mean length [m]", lambda values: mean(values) if values else float("nan")),
        ("Median length [m]", lambda values: median(values) if values else float("nan")),
        ("Standard deviation (n-1) [m]", lambda values: stdev(values) if len(values) > 1 else (0.0 if values else float("nan"))),
        ("Standard deviation (n) [m]", lambda values: pstdev(values) if values else float("nan")),
    )
    for label, calculation in statistics_rows:
        rows.append(
            "\t".join(
                [*("" for _ in range(8)), label, *(_float(calculation(lengths[k])) for k in keywords)]
            )
        )
    _write_lines(path, rows)


def _write_angles(
    path: Path,
    results: list[ImageResult],
    keywords: list[str],
    *,
    usable: bool,
) -> None:
    rows = ["\t".join(["image_name", "area_used", *keywords])]
    for result in results:
        annotations = result.usable_annotations if usable else result.annotations
        area_used = "selected area" if usable and result.usable_area is not None else "whole image"
        grouped: dict[str, list[tuple[float, float]]] = defaultdict(list)
        for annotation in annotations:
            if annotation.length is not None:
                dx = annotation.length.start.x - annotation.length.end.x
                dy = -(annotation.length.start.y - annotation.length.end.y)
                length = hypot(dx, dy)
                if length:
                    grouped[annotation.keyword].append((dx / length, dy / length))
        values = []
        for keyword in keywords:
            vectors = grouped[keyword]
            if not vectors:
                values.append(_float(float("nan")))
            else:
                values.append(_float(degrees(atan2(sum(v[0] for v in vectors), sum(v[1] for v in vectors)))))
        rows.append("\t".join([result.name, area_used, *values]))
    _write_lines(path, rows)


def _write_sizes(
    directory: Path,
    user: str,
    results: list[ImageResult],
    keywords: list[str],
    *,
    usable: bool,
) -> None:
    area_name = "UsableArea" if usable else "WholeImage"
    for keyword_id, keyword in enumerate(keywords, 1):
        rows = ["image_name\tfeature\tlength\twidth\tdirection_angle"]
        for result in results:
            annotations = result.usable_annotations if usable else result.annotations
            mpp = result.metres_per_pixel
            if not mpp:
                continue
            for annotation in annotations:
                if annotation.keyword != keyword or annotation.length is None:
                    continue
                length = _segment_pixels(annotation.length) * mpp
                width = _segment_pixels(annotation.width) * mpp if annotation.width else float("nan")
                dx = annotation.length.start.x - annotation.length.end.x
                dy = -(annotation.length.start.y - annotation.length.end.y)
                angle = degrees(atan2(dx, dy))
                rows.append(
                    "\t".join(
                        [result.name, keyword, _float(length), _float(width), _float(angle)]
                    )
                )
        if len(rows) > 1:
            _write_lines(directory / f"{user}_{area_name}_SD_Keyword{keyword_id:04d}.txt", rows)


def _write_legend(path: Path, keywords: list[str]) -> None:
    _write_lines(path, [f"Keyword {index:04d}\t{keyword}" for index, keyword in enumerate(keywords, 1)])


def _segment_pixels(segment) -> float:
    return hypot(segment.end.x - segment.start.x, segment.end.y - segment.start.y)


def _float(value: float) -> str:
    if isnan(value):
        return "NaN"
    return f"{value:.6f}"


def _write_lines(path: Path, rows: list[str]) -> None:
    atomic_write(path, "".join(row + "\r\n" for row in rows))
