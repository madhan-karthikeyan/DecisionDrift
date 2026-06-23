from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ChangedFile(BaseModel):
    path: str
    language: str
    change_type: Literal["added", "modified", "deleted"]


class ChangedSymbol(BaseModel):
    name: str
    symbol_type: Literal["function", "class", "method"]
    file_path: str
    start_line: int
    end_line: int


class ImpactReport(BaseModel):
    files: list[ChangedFile] = []
    symbols: list[ChangedSymbol] = []

    def summary(self) -> str:
        classes = [s for s in self.symbols if s.symbol_type == "class"]
        functions = [s for s in self.symbols if s.symbol_type == "function"]
        methods = [s for s in self.symbols if s.symbol_type == "method"]
        lines = [f"Files changed: {len(self.files)}"]
        lines.append(f"Symbols detected: {len(self.symbols)}")
        if classes:
            lines.append("")
            lines.append("Classes:")
            for c in classes:
                lines.append(f"  * {c.name}")
        if functions:
            lines.append("")
            lines.append("Functions:")
            for f in functions:
                lines.append(f"  * {f.name}")
        if methods:
            lines.append("")
            lines.append("Methods:")
            for m in methods:
                lines.append(f"  * {m.name} ({m.file_path})")
        return "\n".join(lines)
