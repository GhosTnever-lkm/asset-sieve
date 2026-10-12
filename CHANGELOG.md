# Changelog

## 0.1.4 - 2026-10-12

- Add a Python 3.10–3.13 CI matrix for unit tests, package installation, and CLI startup.
- Run the package-and-publish workflow only for version tags; ordinary branch and pull-request checks use the read-only CI workflow.
- Keep the report version sourced from package metadata and test version consistency.

## 0.1.1 - 2026-10-10

- Clarify installation from the public GitHub tag; the project is not published on PyPI.

## 0.1.0 - 2026-10-10

- Initial release: local image inventory, identical-file groups, size and dimension findings, unreadable-image list, Markdown and JSON reports, and a non-mutating CLI.
