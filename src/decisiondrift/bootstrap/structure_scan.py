from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

MAX_DEPTH = 4


@dataclass
class ProjectStructure:
    root: str
    dirs: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    indicator_files: list[str] = field(default_factory=list)
    top_level_dirs: list[str] = field(default_factory=list)
    top_level_files: list[str] = field(default_factory=list)

    def has_subdir(self, *parts: str) -> bool:
        target = "/".join(parts)
        return any(d.startswith(target) for d in self.dirs)

    def has_file(self, name: str) -> bool:
        return name in self.top_level_files or any(f.endswith("/" + name) for f in self.files)


INDICATOR_FILES = {
    "requirements.txt": "python",
    "Pipfile": "python",
    "pyproject.toml": "python",
    "setup.py": "python",
    "package.json": "node",
    "yarn.lock": "node",
    "composer.json": "php",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "Gemfile": "ruby",
    "manage.py": "django",
    "celery_worker.py": "celery",
    "alembic.ini": "alembic",
    "vite.config.js": "vite",
    "vite.config.ts": "vite",
    "webpack.config.js": "webpack",
    "Dockerfile": "docker",
    "docker-compose.yml": "docker",
    "Makefile": "make",
    "Rakefile": "ruby",
}


def scan_repo(repo_path: str | Path, max_depth: int = MAX_DEPTH) -> ProjectStructure:
    root = Path(repo_path).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"{root} is not a directory")

    seen: set[Path] = set()
    dirs: list[str] = []
    files: list[str] = []
    indicator_files: list[str] = []
    top_level_dirs: list[str] = []
    top_level_files: list[str] = []

    for entry in root.rglob("*"):
        if entry.is_symlink():
            continue

        rel = entry.relative_to(root)
        parts = rel.parts

        # Depth check
        if len(parts) > max_depth:
            continue

        # Exclusion check — skip if any component is excluded
        skip = False
        for i, part in enumerate(parts):
            if part in EXCLUDED_DIRS:
                skip = True
                break
        if skip:
            continue

        # Exclude migrations/versions/ but not migrations/
        if len(parts) >= 2 and parts[:2] == ("migrations", "versions"):
            continue

        if entry.is_dir():
            rel_str = str(rel)
            dirs.append(rel_str)
            if len(parts) == 1:
                top_level_dirs.append(rel_str)
        elif entry.is_file():
            rel_str = str(rel)
            files.append(rel_str)
            basename = entry.name
            if basename in INDICATOR_FILES:
                indicator_files.append(rel_str)
            if len(parts) == 1:
                top_level_files.append(rel_str)

    return ProjectStructure(
        root=str(root),
        dirs=sorted(dirs),
        files=sorted(files),
        indicator_files=sorted(indicator_files),
        top_level_dirs=sorted(top_level_dirs),
        top_level_files=sorted(top_level_files),
    )
