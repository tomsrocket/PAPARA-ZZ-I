"""PAPARA(ZZ)I keyword lists, including the local colour extension."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .model import read_text_compatible


PALETTE: tuple[tuple[int, int, int], ...] = (
    (26, 89, 230),
    (242, 115, 13),
    (26, 166, 64),
    (140, 51, 204),
    (0, 166, 166),
    (230, 26, 26),
    (217, 26, 140),
    (242, 191, 13),
    (0, 0, 0),
    (128, 128, 128),
    (255, 255, 255),
    (13, 38, 140),
)


@dataclass(frozen=True, slots=True)
class KeywordEntry:
    name: str
    color_id: int
    selectable: bool = True


@dataclass(frozen=True, slots=True)
class KeywordList:
    entries: tuple[KeywordEntry, ...]
    mode: str = "individual"
    default_color_id: int = 1

    @property
    def selectable(self) -> tuple[KeywordEntry, ...]:
        return tuple(entry for entry in self.entries if entry.selectable)

    def color_for(self, keyword: str) -> tuple[int, int, int]:
        color_id = self.default_color_id
        if self.mode == "individual":
            match = next((entry for entry in self.entries if entry.name == keyword), None)
            if match is not None:
                color_id = match.color_id
        return color_from_id(color_id)

    @classmethod
    def parse(cls, text: str) -> "KeywordList":
        mode = "individual"
        default = 1
        raw_entries: list[tuple[str, int | None, bool]] = []
        for raw_line in text.splitlines():
            line = raw_line.strip("\ufeff\r\n")
            stripped = line.strip()
            if not stripped:
                raw_entries.append(("", None, False))
                continue
            if stripped.startswith("#"):
                key, separator, value = stripped[1:].partition("=")
                if not separator:
                    continue
                key = key.strip().upper()
                value = value.strip()
                if key == "MODE" and value.upper() in {"INDIVIDUAL", "SINGLE"}:
                    mode = value.lower()
                elif key in {"DEFAULT", "COLOR"}:
                    default = _valid_color_id(value, default)
                continue
            parts = line.split("\t")
            name = parts[0].strip()
            color_id = _valid_color_id(parts[1], default) if len(parts) > 1 else None
            is_group = len(name) >= 2 and name.startswith("_") and name.endswith("_")
            raw_entries.append((name, color_id, bool(name) and not is_group))
        entries = tuple(
            KeywordEntry(name, default if mode == "single" else color_id or default, selectable)
            for name, color_id, selectable in raw_entries
        )
        return cls(entries, mode, default)

    @classmethod
    def load(cls, path: Path) -> "KeywordList":
        return cls.parse(read_text_compatible(path))


def color_from_id(color_id: int) -> tuple[int, int, int]:
    normalized = (max(1, round(color_id)) - 1) % len(PALETTE)
    return PALETTE[normalized]


def color_hex(color: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % color


def _valid_color_id(value: str, fallback: int) -> int:
    try:
        parsed = round(float(value))
    except ValueError:
        return fallback
    return parsed if parsed >= 1 else fallback
