from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .core import markdown, scan


def _validate_report_paths(json_path: Path | None, md_path: Path | None, report: dict) -> None:
    targets = [("JSON", path.expanduser().resolve()) for path in (json_path,) if path]
    targets += [("Markdown", path.expanduser().resolve()) for path in (md_path,) if path]

    if len(targets) == 2 and targets[0][1] == targets[1][1]:
        raise ValueError("JSON and Markdown report paths resolve to the same file; choose different paths")

    root = Path(report["root"])
    sources = [root / item["path"] for item in report["assets"]]
    sources += [root / item["path"] for item in report["unreadable"]]
    for kind, target in targets:
        for source in sources:
            resolved_source = source.resolve()
            same_file = target == resolved_source
            if not same_file and target.exists() and resolved_source.exists():
                try:
                    same_file = os.path.samefile(target, resolved_source)
                except OSError:
                    same_file = False
            if same_file:
                raise ValueError(
                    f"{kind} report path '{target}' points to scanned source image "
                    f"'{resolved_source}'; choose a different output path"
                )


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="asset-sieve",
        description="Audit image assets locally; detect identical files and unusually large textures.",
    )
    parser.add_argument("folder", type=Path, help="game art/assets folder to inspect")
    parser.add_argument("--json", dest="json_path", type=Path, help="write a JSON report")
    parser.add_argument("--md", dest="md_path", type=Path, help="write a Markdown report")
    parser.add_argument("--max-file-mb", type=float, default=16, help="warn above this file size in MiB (default: 16 MiB)")
    parser.add_argument("--max-dimension", type=int, default=8192, help="warn above this pixel dimension (default: 8192)")
    parser.add_argument("--exclude", action="append", default=[], metavar="DIR", help="exclude a directory name (repeatable)")
    parser.add_argument("--fail-on-warning", action="store_true", help="return exit code 2 when findings exist")
    args = parser.parse_args()
    try:
        report = scan(args.folder, max_file_mb=args.max_file_mb,
                      max_dimension=args.max_dimension, excludes=args.exclude)
        _validate_report_paths(args.json_path, args.md_path, report)
        if args.json_path:
            args.json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.md_path:
            args.md_path.write_text(markdown(report), encoding="utf-8")
        summary = report["summary"]
        print(f"Asset Sieve: {summary['images']} images, {summary['duplicates']} duplicate groups, "
              f"{summary['oversized_files']} oversized files, {summary['oversized_dimensions']} large textures, "
              f"{summary['unreadable']} unreadable; {summary['warnings']} finding(s).")
        if args.json_path:
            print(f"JSON report: {args.json_path}")
        if args.md_path:
            print(f"Markdown report: {args.md_path}")
        return 2 if args.fail_on_warning and summary["warnings"] else 0
    except (OSError, ValueError) as exc:
        print(f"asset-sieve: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
