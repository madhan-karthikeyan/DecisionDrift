from __future__ import annotations

from decisiondrift.impact.diff_parser import parse_diff


class TestParseDiff:
    def test_empty_diff(self):
        assert parse_diff("") == []

    def test_modified_file(self):
        diff = """diff --git a/backend/models/patient.py b/backend/models/patient.py
index abc..def 100644
--- a/backend/models/patient.py
+++ b/backend/models/patient.py
@@ -1,3 +1,4 @@
 class Patient:
     pass
+    def new_method(self):
+        pass"""
        files = parse_diff(diff)
        assert len(files) == 1
        assert files[0].path == "backend/models/patient.py"
        assert files[0].language == "python"
        assert files[0].change_type == "modified"

    def test_new_file(self):
        diff = """diff --git a/dev/null b/backend/utils/new_module.py
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/backend/utils/new_module.py
@@ -0,0 +1,3 @@
+def new_function():
+    pass"""
        files = parse_diff(diff)
        assert len(files) == 1
        assert files[0].path == "backend/utils/new_module.py"
        assert files[0].change_type == "added"

    def test_deleted_file(self):
        diff = """diff --git a/backend/utils/old.py b/dev/null
deleted file mode 100644
index abc1234..0000000
--- a/backend/utils/old.py
+++ /dev/null
@@ -1,5 +0,0 @@
-def old_function():
-    pass"""
        files = parse_diff(diff)
        assert len(files) == 1
        assert files[0].path == "backend/utils/old.py"
        assert files[0].change_type == "deleted"

    def test_multiple_files(self):
        diff = """diff --git a/file_a.py b/file_a.py
--- a/file_a.py
+++ b/file_a.py
@@ -1 +1,2 @@
 a
+b
diff --git a/file_b.py b/file_b.py
--- a/file_b.py
+++ b/file_b.py
@@ -1 +1,2 @@
 c
+d"""
        files = parse_diff(diff)
        assert len(files) == 2

    def test_binary_file_skipped(self):
        diff = """diff --git a/logo.png b/logo.png
new file mode 100644
index 0000000..abc1234
Binary files /dev/null and b/logo.png differ"""
        files = parse_diff(diff)
        assert len(files) == 0

    def test_vendor_dir_excluded(self):
        diff = """diff --git a/vendor/lib.py b/vendor/lib.py
--- a/vendor/lib.py
+++ b/vendor/lib.py
@@ -1 +1,2 @@
 a
+b"""
        files = parse_diff(diff)
        assert len(files) == 0

    def test_node_modules_excluded(self):
        diff = """diff --git a/node_modules/pkg/index.js b/node_modules/pkg/index.js
--- a/node_modules/pkg/index.js
+++ b/node_modules/pkg/index.js
@@ -1 +1,2 @@
 a
+b"""
        files = parse_diff(diff)
        assert len(files) == 0

    def test_rename(self):
        diff = """diff --git a/old.py b/new.py
similarity index 100%
rename from old.py
rename to new.py"""
        files = parse_diff(diff)
        assert len(files) == 1
        assert files[0].path == "new.py"
        assert files[0].change_type == "added"

    def test_language_detection(self):
        diff = """diff --git a/src/app.js b/src/app.js
--- a/src/app.js
+++ b/src/app.js
@@ -1 +1,2 @@
 a
+b"""
        files = parse_diff(diff)
        assert files[0].language == "javascript"
