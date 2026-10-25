from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from PIL import Image, UnidentifiedImageError

from . import __version__

DEFAULT_EXCLUDES = {".git", ".svn", "node_modules", "__pycache__", ".asset-sieve"}
SUPPORTED = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def _files(root: Path, excludes: set[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part.casefold() in excludes for part in path.relative_to(root).parts):
            continue
        if path.is_symlink() or not path.is_file() or path.suffix.casefold() not in SUPPORTED:
            continue
        yield path


def scan(root: Path, *, max_file_mb: float = 16, max_dimension: int = 8192,
         excludes: Iterable[str] = ()) -> dict:
    root = root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    if not math.isfinite(max_file_mb) or max_file_mb <= 0:
        raise ValueError("max_file_mb must be finite and greater than zero")
    if isinstance(max_dimension, bool) or not isinstance(max_dimension, int) or max_dimension <= 0:
        raise ValueError("max_dimension must be a positive integer")
    excluded = DEFAULT_EXCLUDES | {item.casefold() for item in excludes}
    records, unreadable = [], []
    for path in _files(root, excluded):
        try:
            size = path.stat().st_size
            digest = _digest(path)
            with Image.open(path) as image:
                width, height = image.size
                image_format = (image.format or path.suffix.lstrip(".")).upper()
                frames = getattr(image, "n_frames", 1)
                image.verify()
            records.append({
                "path": path.relative_to(root).as_posix(), "bytes": size,
                "width": width, "height": height, "format": image_format,
                "frames": frames, "sha256": digest,
            })
        except (OSError, SyntaxError, UnidentifiedImageError, ValueError, Image.DecompressionBombError) as exc:
            unreadable.append({"path": path.relative_to(root).as_posix(), "reason": str(exc)})

    records.sort(key=lambda record: record["path"].casefold())
    unreadable.sort(key=lambda record: record["path"].casefold())
    by_hash = defaultdict(list)
    records_by_path = {r["path"]: r for r in records}
    for record in records:
        by_hash[record["sha256"]].append(record["path"])
    duplicates = [
        {"sha256": digest, "paths": sorted(paths),
         "wasted_bytes": records_by_path[paths[0]]["bytes"] * (len(paths) - 1)}
        for digest, paths in by_hash.items() if len(paths) > 1
    ]
    oversized = [r for r in records if r["bytes"] > max_file_mb * 1024 * 1024]
    large_dimensions = [r for r in records if max(r["width"], r["height"]) > max_dimension]
    totals_by_folder = defaultdict(lambda: {"files": 0, "bytes": 0})
    totals_by_format = defaultdict(lambda: {"files": 0, "bytes": 0})
    for record in records:
        folder = str(Path(record["path"]).parent).replace("\\", "/")
        if folder == ".":
            folder = "(root)"
        bucket = totals_by_folder[folder]
        bucket["files"] += 1
        bucket["bytes"] += record["bytes"]
        fmt = record["format"]
        totals_by_format[fmt]["files"] += 1
        totals_by_format[fmt]["bytes"] += record["bytes"]

    warnings = []
    warnings += [{"kind": "duplicate", "paths": d["paths"], "detail": f'{d["wasted_bytes"]} duplicate bytes'} for d in duplicates]
    warnings += [{"kind": "large-file", "path": r["path"], "detail": f'{r["bytes"]} bytes exceeds {max_file_mb:g} MiB'} for r in oversized]
    warnings += [{"kind": "large-dimensions", "path": r["path"], "detail": f'{r["width"]}x{r["height"]} exceeds {max_dimension}px'} for r in large_dimensions]
    warnings += [{"kind": "unreadable", **item} for item in unreadable]
    return {
        "tool": "Asset Sieve", "version": __version__, "root": str(root),
        "summary": {
            "images": len(records), "total_bytes": sum(r["bytes"] for r in records),
            "duplicates": len(duplicates), "duplicate_bytes": sum(d["wasted_bytes"] for d in duplicates),
            "oversized_files": len(oversized), "oversized_dimensions": len(large_dimensions),
            "unreadable": len(unreadable), "warnings": len(warnings),
        },
        "limits": {"max_file_mb": max_file_mb, "max_dimension_px": max_dimension},
        "by_format": dict(sorted(totals_by_format.items())),
        "by_folder": dict(sorted(totals_by_folder.items())),
        "assets": records,
        "duplicates": sorted(duplicates, key=lambda d: d["paths"][0].casefold()),
        "oversized_files": oversized,
        "oversized_dimensions": large_dimensions,
        "unreadable": unreadable,
        "warnings": warnings,
    }


def markdown(report: dict) -> str:
    s = report["summary"]
    mb = s["total_bytes"] / (1024 * 1024)
    lines = [
        f"# Asset Sieve report — v{report['version']}", "",
        f"- Folder: {report['root']}",
        f"- Images: {s['images']} ({mb:.2f} MiB)",
        f"- Duplicate groups: {s['duplicates']} ({s['duplicate_bytes']} duplicate bytes)",
        f"- Files over size limit: {s['oversized_files']}",
        f"- Images over dimension limit: {s['oversized_dimensions']}",
        f"- Unreadable images: {s['unreadable']}", "",
    ]
    if report["duplicates"]:
        lines += ["## Identical files", ""]
        for group in report["duplicates"]:
            lines.append(f"- {group['wasted_bytes']} duplicate bytes")
            lines.extend(f"  - {path}" for path in group["paths"])
        lines.append("")
    for title, key in (("Oversized files", "oversized_files"), ("Large dimensions", "oversized_dimensions")):
        if report[key]:
            lines += [f"## {title}", ""]
            for item in report[key]:
                lines.append(f"- {item['path']} — {item['bytes']} bytes, {item['width']}x{item['height']}")
            lines.append("")
    if report["unreadable"]:
        lines += ["## Unreadable images", ""]
        lines.extend(f"- {item['path']} — {item['reason']}" for item in report["unreadable"])
        lines.append("")
    lines += ["## By format", "", "| Format | Files | MiB |", "|---|---:|---:|"]
    lines.extend(f"| {fmt} | {data['files']} | {data['bytes'] / (1024 * 1024):.2f} |" for fmt, data in report["by_format"].items())
    lines += ["", "## By folder", "", "| Folder | Files | MiB |", "|---|---:|---:|"]
    lines.extend(f"| {folder} | {data['files']} | {data['bytes'] / (1024 * 1024):.2f} |" for folder, data in report["by_folder"].items())
    lines += ["", "This report is diagnostic. Asset Sieve does not modify or delete source files.", ""]
    return "\n".join(lines)
