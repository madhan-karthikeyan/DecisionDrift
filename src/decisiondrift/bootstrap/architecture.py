from __future__ import annotations

from collections import defaultdict

from decisiondrift.bootstrap.detectors import DetectedTechnology


class ArchitectureModel:
    """Aggregated architecture model built from technology detections."""

    def __init__(self, findings: list[DetectedTechnology]):
        self.findings = sorted(findings, key=lambda f: f.confidence, reverse=True)
        self._by_category: dict[str, list[DetectedTechnology]] = defaultdict(list)
        for f in self.findings:
            self._by_category[f.category].append(f)

    def by_category(self, category: str) -> list[DetectedTechnology]:
        return self._by_category.get(category, [])

    def categories(self) -> list[str]:
        return sorted(self._by_category.keys())

    def count(self) -> int:
        return len(self.findings)

    def high_confidence(self) -> list[DetectedTechnology]:
        return [f for f in self.findings if f.confidence >= 0.8]

    def coverage(self, governed_names: set[str]) -> float:
        """Ratio of detected technologies that are covered by existing ADRs."""
        if not self.findings:
            return 0.0
        covered = sum(1 for f in self.findings if f.name.lower() in governed_names)
        return covered / len(self.findings)

    def summary(self) -> str:
        """Human-readable architecture summary."""
        lines = [
            "Architecture Summary",
            "",
        ]
        for cat in self.categories():
            techs = self.by_category(cat)
            cat_label = cat.replace("_", " ").title()
            lines.append(f"  {cat_label}:")
            for t in techs:
                bars = "■" * int(t.confidence * 10) + "□" * (10 - int(t.confidence * 10))
                label = f"    {t.name}  [{bars}] {t.confidence:.0%}"
                lines.append(label)
            lines.append("")

        lines.append(f"  Total technologies detected: {self.count()}")
        return "\n".join(lines)

    def report_missing(self, governed_names: set[str]) -> list[str]:
        """Return names of detected technologies not covered by ADRs."""
        missing = []
        for f in self.findings:
            if f.name.lower() not in governed_names and f.confidence >= 0.7:
                missing.append(f.name)
        return missing
