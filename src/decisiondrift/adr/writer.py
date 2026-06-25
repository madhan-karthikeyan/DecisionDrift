from __future__ import annotations

from pathlib import Path
from typing import Any

import frontmatter


def read_adr(path: Path) -> tuple[dict[str, Any], str]:
    post = frontmatter.load(str(path))
    return dict(post.metadata), post.content


def write_adr(path: Path, metadata: dict[str, Any], body: str) -> None:
    post = frontmatter.Post(body, **metadata)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        f.write(frontmatter.dumps(post))
    tmp.replace(path)


def set_status(path: Path, new_status: str, rejected_reason: str | None = None) -> None:
    metadata, body = read_adr(path)
    metadata["status"] = new_status
    if rejected_reason is not None:
        metadata["rejected_reason"] = rejected_reason
    write_adr(path, metadata, body)
