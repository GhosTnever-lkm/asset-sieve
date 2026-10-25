# Asset Sieve

[![CI](https://github.com/GhosTnever-lkm/asset-sieve/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/GhosTnever-lkm/asset-sieve/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/GhosTnever-lkm/asset-sieve)](https://github.com/GhosTnever-lkm/asset-sieve/releases/latest)

**Local texture and image-asset audit for game projects.** Find byte-identical images, unusually large files, oversized dimensions, and unreadable assets. Export Markdown or JSON reports for review.

Asset Sieve only reads the selected folder. It never rewrites, moves, optimizes, or deletes source assets. It works across Unity, Unreal, Godot, and custom projects because it scans ordinary image files rather than engine internals.

## Quick start

Requires Python 3.10+.

    py -m pip install "git+https://github.com/GhosTnever-lkm/asset-sieve.git@v0.1.7"
    asset-sieve "D:\Games\MyProject\Assets" --md asset-report.md --json asset-report.json

Run from a source checkout:

    py -m pip install .
    asset-sieve "D:\Games\MyProject\Assets" --md report.md

## What it reports

- Identical files by SHA-256, with duplicate bytes grouped by path.
- Per-file dimensions, image format, frame count, file size, and SHA-256 in JSON.
- Files over the configurable size threshold (default 16 MiB). The legacy `--max-file-mb` option is measured in MiB (1 MiB = 1,048,576 bytes).
- Images with a width or height over the configurable limit (default 8192 px).
- Files Pillow cannot verify or open.
- Total sizes by image format and directory in both Markdown and JSON reports.
- Markdown and JSON output suitable for code review or release checklists.
- Report output paths cannot overwrite a scanned image or point both formats at the same file.

Examples:

    asset-sieve ./Assets --max-file-mb 8 --max-dimension 4096 --md texture-audit.md
    asset-sieve ./Art --exclude Cache --exclude Thumbnails --json audit.json --fail-on-warning

The fail-on-warning option returns exit code 2 when findings exist; input or filesystem errors return 1. The default is informational and returns 0 even when findings are present.

## Scope and limits

Supported formats: PNG, JPEG, WebP, GIF, BMP, and TIFF. Pillow verifies each file before it is included; damaged images are listed as unreadable. Duplicate detection is byte-for-byte; visually similar images encoded differently are not reported as duplicates. Thresholds are general signals, not platform-specific texture budgets. The tool does not inspect engine import settings, mipmaps, GPU memory, compression presets, or runtime usage.

Reports contain local paths and should be reviewed before sharing. No files are uploaded. Reports can be saved inside the scanned folder, but not over a scanned image.

## License

MIT. See LICENSE.

## Development

Run the unit and CLI checks with:

    python -m unittest discover -s tests -v

## Support / Pro Version

Asset Sieve is free and open source under MIT. There is no separate Pro build or paid feature set yet. If it helps your project, support development on [Boosty](https://boosty.to/azizazimov), [Buy Me a Coffee](https://buymeacoffee.com/azizazimov8), or [Gumroad](https://azimovian22.gumroad.com/).

Optional donations:

| Network | Receive address |
|---|---|
| Bitcoin | bc1qn75pj4n7gyl2k5kf2f97elvyenz52q6nn2g30u |
| TRON (USDT TRC20) | TCBSy38X57hA6w2onJcxom24x1febc1mP1 |
| BNB Smart Chain (BEP20) | 0xD431a917961E0b086B96D9F72b5C8fF19b19068a |

Send assets only on the listed network. Sending through another network may result in a permanent loss.
