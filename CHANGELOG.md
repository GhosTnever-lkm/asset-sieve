# Changelog

## 0.1.6 - 2026-10-24

- Reject non-integer, non-finite, and non-positive dimension limits passed to the Python API.
- Add regression coverage for NaN, infinity, fractional, and boolean limits.

## 0.1.5 - 2026-10-12

- Refuse report destinations that resolve to a scanned image, preventing accidental replacement of source assets.
- Refuse JSON and Markdown destinations that resolve to the same file.

## 0.1.4 - 2026-10-12

- Add a Python 3.10–3.13 CI matrix for unit tests, package installation, and CLI startup.
- Run the package-and-publish workflow only for version tags; ordinary branch and pull-request checks use the read-only CI workflow.
- Keep the report version sourced from package metadata and test version consistency.

## 0.1.3 - 2026-10-10

- Verify image files before including them in reports so damaged images are listed as unreadable.
- Include per-folder totals in Markdown reports.

## 0.1.2 - 2026-10-10

- Make report ordering deterministic and reject non-finite size thresholds.
- Add the unit/CLI suite to release validation.

## 0.1.1 - 2026-10-10

- Clarify installation from the public GitHub tag; the project is not published on PyPI.

## 0.1.0 - 2026-10-10

- Initial release: local image inventory, identical-file groups, size and dimension findings, unreadable-image list, Markdown and JSON reports, and a non-mutating CLI.
