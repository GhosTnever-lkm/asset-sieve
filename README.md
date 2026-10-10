# Asset Sieve

**Local texture and image-asset audit for game projects.** Find byte-identical images, unusually large files, oversized dimensions, and unreadable assets. Export Markdown or JSON reports for review.

Asset Sieve only reads the selected folder. It never rewrites, moves, optimizes, or deletes source assets. It works across Unity, Unreal, Godot, and custom projects because it scans ordinary image files rather than engine internals.

## Quick start

Requires Python 3.10+.

    py -m pip install "git+https://github.com/GhosTnever-lkm/asset-sieve.git@v0.1.1"
    asset-sieve "D:\Games\MyProject\Assets" --md asset-report.md --json asset-report.json

Run from a source checkout:

    py -m pip install .
    asset-sieve "D:\Games\MyProject\Assets" --md report.md

## What it reports

- Identical files by SHA-256, with duplicate bytes grouped by path.
- Per-file dimensions, image format, frame count, file size, and SHA-256 in JSON.
- Files over the configurable size threshold (default 16 MiB).
- Images with a width or height over the configurable limit (default 8192 px).
- Files Pillow cannot read.
- Total sizes by image format and directory.
- Markdown and JSON output suitable for code review or release checklists.

Examples:

    asset-sieve ./Assets --max-file-mb 8 --max-dimension 4096 --md texture-audit.md
    asset-sieve ./Art --exclude Cache --exclude Thumbnails --json audit.json --fail-on-warning

The fail-on-warning option returns exit code 2 when findings exist; input or filesystem errors return 1. The default is informational and returns 0 even when findings are present.

## Scope and limits

Supported formats: PNG, JPEG, WebP, GIF, BMP, and TIFF. Image metadata is read through Pillow. Duplicate detection is byte-for-byte; visually similar images encoded differently are not reported as duplicates. Thresholds are general signals, not platform-specific texture budgets. The tool does not inspect engine import settings, mipmaps, GPU memory, compression presets, or runtime usage.

Reports contain local paths and should be reviewed before sharing. No files are uploaded.

## License

MIT. See LICENSE.

## Support / Pro Version

Asset Sieve is free and open source under MIT. There is no separate Pro build or paid feature set. If it helps your project, support development on Boosty or Buy Me a Coffee. Support does not unlock extra functionality.

