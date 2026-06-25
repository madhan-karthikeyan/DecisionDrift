from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from decisiondrift.cli import cli
from decisiondrift.impact.diff_parser import parse_diff
from decisiondrift.impact.models import ChangedFile, ChangedSymbol
from decisiondrift.impact.reference_scan import generate_search_terms


class TestImpactFlow:
    def test_impact_empty_diff(self, tmp_path: Path):
        runner = CliRunner()
        diff_file = tmp_path / "empty.diff"
        diff_file.write_text("")
        result = runner.invoke(
            cli,
            [
                "impact",
                str(diff_file),
                "--repo",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0

    def test_impact_with_python_diff(self, tmp_path: Path):
        diff_file = tmp_path / "changes.diff"
        diff_file.write_text(
            "diff --git a/app.py b/app.py\n--- /dev/null\n+++ b/app.py\n@@ -0,0 +1,3 @@\n+def handler():\n+    pass\n+\nclass Service:\n    def process(self):\n        pass\n"
        )
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "impact",
                str(diff_file),
                "--repo",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0

    def test_impact_from_git_no_repo(self, tmp_path: Path):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "impact",
                "--from-git",
                "--repo",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0

    def test_impact_no_changes(self, tmp_path: Path):
        diff_file = tmp_path / "empty.diff"
        diff_file.write_text("")
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "impact",
                str(diff_file),
                "--repo",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0

    def test_impact_report_structure(self):
        files = [
            ChangedFile(path="app.py", language="python", change_type="modified"),
        ]
        symbols = [
            ChangedSymbol(name="handler", symbol_type="function", file_path="app.py", start_line=1, end_line=3),
            ChangedSymbol(name="Service", symbol_type="class", file_path="app.py", start_line=5, end_line=7),
        ]
        from decisiondrift.impact.models import ImpactReport

        report = ImpactReport(files=files, symbols=symbols)
        summary = report.summary()
        assert "Files changed: 1" in summary
        assert "handler" in summary
        assert "Service" in summary

    def test_impact_search_terms(self):
        symbols = [
            ChangedSymbol(
                name="UserService", symbol_type="class", file_path="src/services/user.py", start_line=1, end_line=10
            ),
        ]
        terms = generate_search_terms(symbols)
        assert "UserService" in terms
        assert "user" in str(terms).lower()

    def test_diff_parser_python(self):
        diff = "diff --git a/app.py b/app.py\n--- /dev/null\n+++ b/app.py\n@@ -0,0 +1 @@\n+print('hello')\n"
        files = parse_diff(diff)
        assert len(files) == 1
        assert files[0].path == "app.py"
        assert files[0].language == "python"

    def test_diff_parser_excludes_binary(self):
        diff = "diff --git a/image.png b/image.png\n--- /dev/null\n+++ b/image.png\n@@ -0,0 +1 @@\n+BINARY\n"
        files = parse_diff(diff)
        assert len(files) == 0

    def test_diff_parser_multiple_files(self):
        diff = """diff --git a/a.py b/a.py
--- /dev/null
+++ b/a.py
@@ -0,0 +1 @@
+print('a')
diff --git a/b.py b/b.py
--- /dev/null
+++ b/b.py
@@ -0,0 +1 @@
+print('b')
"""
        files = parse_diff(diff)
        assert len(files) == 2
        assert {f.path for f in files} == {"a.py", "b.py"}
