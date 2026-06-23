from __future__ import annotations

import sys
from pathlib import Path

from decisiondrift.impact.ast_python import extract_symbols
from decisiondrift.impact.diff_parser import parse_diff
from decisiondrift.impact.models import ImpactReport
from decisiondrift.impact.reference_scan import generate_search_terms


def analyze_diff(diff_text: str, repo_path: str | Path = ".") -> ImpactReport:
    repo = Path(repo_path).resolve()
    if not repo.exists():
        print(f"Warning: repository path does not exist: {repo}", file=sys.stderr)
        return ImpactReport(files=[], symbols=[])

    files = parse_diff(diff_text)

    if not files:
        return ImpactReport(files=[], symbols=[])

    symbols = []
    for file in files:
        if file.language != "python" or file.change_type == "deleted":
            continue
        abs_path = repo / file.path
        file_symbols = extract_symbols(str(abs_path))
        for s in file_symbols:
            s.file_path = file.path
        symbols.extend(file_symbols)

    report = ImpactReport(files=files, symbols=symbols)
    return report
