from __future__ import annotations

import re
from pathlib import Path

from decisiondrift.impact.models import ChangedFile

EXCLUDED_DIRS = {
    "node_modules", "vendor", ".git", "__pycache__",
    "dist", "build", ".egg-info", "venv", ".venv",
    "migrations", ".tox", "env",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pdf", ".zip", ".tar", ".gz", ".bz2",
    ".pyc", ".pyo", ".so", ".dll", ".dylib",
    ".db", ".sqlite", ".sqlite3",
}

DEVNULL = "/dev/null"


def _detect_language(path: str) -> str:
    ext = Path(path).suffix.lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescriptreact",
        ".jsx": "javascriptreact",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
        ".sql": "sql",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".md": "markdown",
        ".txt": "text",
        ".toml": "toml",
        ".cfg": "config",
        ".ini": "config",
    }
    return mapping.get(ext, "unknown")


def _is_excluded(path: str) -> bool:
    parts = Path(path).parts
    return any(p in EXCLUDED_DIRS for p in parts)


def _is_binary(path: str) -> bool:
    return Path(path).suffix.lower() in BINARY_EXTENSIONS


def _is_devnull(path: str) -> bool:
    return path == DEVNULL or path == "dev/null"


def _commit(files: list[ChangedFile], path: str | None, change_type: str | None) -> None:
    if path is None or change_type is None:
        return
    if _is_devnull(path):
        return
    if _is_excluded(path):
        return
    if _is_binary(path):
        return
    files.append(ChangedFile(
        path=path,
        language=_detect_language(path),
        change_type=change_type,
    ))


def parse_diff(diff_text: str) -> list[ChangedFile]:
    files: list[ChangedFile] = []
    current_path: str | None = None
    change_type: str | None = None

    for raw_line in diff_text.splitlines():
        line = raw_line.rstrip("\n")

        # Detect new file
        if line.startswith("new file mode"):
            change_type = "added"
            continue

        # Detect deleted file
        if line.startswith("deleted file mode"):
            change_type = "deleted"
            continue

        if line.startswith("rename from "):
            continue

        if line.startswith("rename to "):
            current_path = line[10:]
            change_type = "added"
            continue

        # Header: diff --git a/path b/path
        m = re.match(r"^diff --git a/(.+?) b/(.+)$", line)
        if m:
            _commit(files, current_path, change_type)
            a_path = m.group(1)
            b_path = m.group(2)
            if _is_devnull(a_path):
                current_path = b_path
                change_type = "added"
            elif _is_devnull(b_path):
                current_path = a_path
                change_type = "deleted"
            else:
                current_path = b_path
                change_type = "modified"
            continue

    _commit(files, current_path, change_type)

    # Deduplicate by path (last change_type wins)
    seen: dict[str, ChangedFile] = {}
    for f in files:
        seen[f.path] = f
    return list(seen.values())
