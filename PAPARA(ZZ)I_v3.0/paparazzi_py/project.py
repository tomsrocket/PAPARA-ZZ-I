"""Project layout and persistence compatible with PAPARA(ZZ)I 3.0."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil

from PIL import Image

from .model import (
    Annotation,
    ScaleBar,
    UsableArea,
    atomic_write,
    read_text_compatible,
    read_annotations,
    write_annotations,
)


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".tif", ".tiff", ".png"}
VALID_USER = re.compile(r"[^a-zA-Z0-9_.-]+")


@dataclass(slots=True)
class Project:
    image_dir: Path
    user: str

    def __post_init__(self) -> None:
        self.image_dir = self.image_dir.resolve()
        self.user = VALID_USER.sub("_", self.user.strip().lower()).strip("_")
        if not self.user:
            raise ValueError("Bitte einen Benutzernamen angeben")
        if not self.image_dir.is_dir():
            raise ValueError("Der Bilderordner existiert nicht")
        self.annotations_dir.mkdir(parents=True, exist_ok=True)
        legacy_areas = self.image_dir / f"{self.user}_rectangle"
        if not self.usable_area_dir.exists() and legacy_areas.is_dir():
            shutil.copytree(legacy_areas, self.usable_area_dir)
        else:
            self.usable_area_dir.mkdir(parents=True, exist_ok=True)
        self.scale_dir.mkdir(parents=True, exist_ok=True)

    @property
    def annotations_dir(self) -> Path:
        return self.image_dir / f"{self.user}_annotations"

    @property
    def usable_area_dir(self) -> Path:
        return self.image_dir / f"{self.user}_usable-area"

    @property
    def scale_dir(self) -> Path:
        return self.image_dir / f"{self.user}_scale"

    @property
    def exported_images_dir(self) -> Path:
        return self.image_dir / f"{self.user}_exported_images" / "free_annotations"

    @property
    def ignore_file(self) -> Path:
        return self.annotations_dir / "ignorelist.txt"

    def images(self) -> list[Path]:
        return sorted(
            (path for path in self.image_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES),
            key=lambda path: path.name.casefold(),
        )

    def image_size(self, image_path: Path) -> tuple[int, int]:
        with Image.open(image_path) as image:
            return image.size

    def annotation_file(self, image_path: Path) -> Path:
        width, height = self.image_size(image_path)
        return self.annotations_dir / f"{image_path.stem}_{width}x{height}.txt"

    def scale_file(self, image_path: Path) -> Path:
        return self.scale_dir / f"{image_path.stem}.txt"

    def usable_area_file(self, image_path: Path) -> Path:
        return self.usable_area_dir / f"{image_path.stem}.txt"

    def load_annotations(self, image_path: Path) -> list[Annotation]:
        return read_annotations(self.annotation_file(image_path))

    def save_annotations(self, image_path: Path, annotations: list[Annotation]) -> None:
        write_annotations(self.annotation_file(image_path), annotations)

    def load_scale(self, image_path: Path) -> ScaleBar | None:
        path = self.scale_file(image_path)
        return ScaleBar.parse(read_text_compatible(path)) if path.exists() else None

    def save_scale(self, image_path: Path, scale: ScaleBar) -> None:
        atomic_write(self.scale_file(image_path), scale.format() + "\r\n")

    def load_usable_area(self, image_path: Path) -> UsableArea | None:
        path = self.usable_area_file(image_path)
        return UsableArea.parse(read_text_compatible(path)) if path.exists() else None

    def save_usable_area(self, image_path: Path, area: UsableArea) -> None:
        atomic_write(self.usable_area_file(image_path), area.format() + "\r\n")

    def ignored_images(self) -> set[str]:
        if not self.ignore_file.exists():
            return set()
        return {
            line.strip()
            for line in read_text_compatible(self.ignore_file).splitlines()
            if line.strip()
        }

    def set_ignored(self, image_path: Path, ignored: bool) -> None:
        names = self.ignored_images()
        if ignored:
            names.add(image_path.name)
        else:
            names.discard(image_path.name)
        ordered = [path.name for path in self.images() if path.name in names]
        atomic_write(self.ignore_file, "".join(name + "\r\n" for name in ordered))

    def replace_keyword(self, old: str, new: str) -> tuple[int, int]:
        """Replace a keyword in all free-annotation files.

        Returns ``(changed_annotations, changed_files)``. Existing ``.bak``
        files are maintained by the atomic writer.
        """
        changed_annotations = 0
        changed_files = 0
        for path in self.annotations_dir.glob("*.txt"):
            if path.name in {"ignorelist.txt", "randomlist.txt"}:
                continue
            annotations = read_annotations(path)
            count = sum(annotation.keyword == old for annotation in annotations)
            if not count:
                continue
            write_annotations(
                path,
                [annotation.renamed(new) if annotation.keyword == old else annotation for annotation in annotations],
            )
            changed_annotations += count
            changed_files += 1
        return changed_annotations, changed_files
