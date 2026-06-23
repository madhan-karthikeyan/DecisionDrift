from __future__ import annotations

import re
from pathlib import Path


def allocate_id(adr_dir: str | Path) -> str:
    adr_path = Path(adr_dir)
    max_num = 0
    if adr_path.exists():
        for f in adr_path.glob("ADR-*.md"):
            m = re.match(r"^ADR-(\d{4})\.md$", f.name)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
    return f"ADR-{max_num + 1:04d}"
