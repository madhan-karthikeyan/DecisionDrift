from __future__ import annotations

from pathlib import Path

from decisiondrift.impact.service import analyze_diff


class TestService:
    def test_analyze_diff_end_to_end(self, tmp_path: Path):
        repo = tmp_path / "repo"
        repo.mkdir()

        # Create a Python file in the repo
        src_dir = repo / "backend" / "services"
        src_dir.mkdir(parents=True)
        src_file = src_dir / "user_service.py"
        src_file.write_text("""class UserService:
    def get_user(self):
        pass

    def create_user(self):
        pass


def helper_util():
    pass
""")

        diff = """diff --git a/backend/services/user_service.py b/backend/services/user_service.py
index abc..def 100644
--- a/backend/services/user_service.py
+++ b/backend/services/user_service.py
@@ -1,3 +1,4 @@
 class UserService:
     def get_user(self):
-        pass
+        return db.query(User).first()
"""
        report = analyze_diff(diff, repo_path=str(repo))
        assert len(report.files) == 1
        assert report.files[0].path == "backend/services/user_service.py"
        assert report.files[0].change_type == "modified"
        assert report.files[0].language == "python"

        symbols_by_name = {s.name: s for s in report.symbols}
        assert "UserService" in symbols_by_name
        assert symbols_by_name["UserService"].symbol_type == "class"
        assert "get_user" in symbols_by_name
        assert symbols_by_name["get_user"].symbol_type == "method"
        assert "create_user" in symbols_by_name
        assert symbols_by_name["create_user"].symbol_type == "method"
        assert "helper_util" in symbols_by_name
        assert symbols_by_name["helper_util"].symbol_type == "function"

        summary = report.summary()
        assert "Files changed: 1" in summary
        assert "Symbols detected: 4" in summary
        assert "UserService" in summary
        assert "get_user" in summary
        assert "create_user" in summary
        assert "helper_util" in summary

    def test_analyze_diff_deleted_file_skips_ast(self, tmp_path: Path):
        repo = tmp_path / "repo"
        repo.mkdir()

        diff = """diff --git a/backend/old.py b/dev/null
deleted file mode 100644
index abc..000 100644
--- a/backend/old.py
+++ /dev/null
@@ -1,5 +0,0 @@
-def old_func():
-    pass
"""
        report = analyze_diff(diff, repo_path=str(repo))
        assert len(report.symbols) == 0

    def test_analyze_diff_non_python_skipped(self, tmp_path: Path):
        repo = tmp_path / "repo"
        repo.mkdir()

        diff = """diff --git a/frontend/app.js b/frontend/app.js
--- a/frontend/app.js
+++ b/frontend/app.js
@@ -1 +1,2 @@
 console.log("hello")
+console.log("world")
"""
        report = analyze_diff(diff, repo_path=str(repo))
        assert len(report.files) == 1
        assert report.files[0].language == "javascript"
        assert len(report.symbols) == 0
