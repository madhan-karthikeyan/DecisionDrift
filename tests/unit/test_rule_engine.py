from __future__ import annotations

from pathlib import Path

from decisiondrift.models.schema import ConfidenceLevel, DecisionRecord
from decisiondrift.rules.engine import (
    _extract_deps_from_file,
    _is_config_file,
    _scan_api_calls,
    _scan_config_pattern,
    _scan_imports_in_diff,
    enforce,
    enforce_from_adrs,
)
from decisiondrift.rules.models import Action, Rule, RuleSet, RuleType


class TestDependencyExtraction:
    def test_requirements_txt(self, tmp_path: Path):
        f = tmp_path / "requirements.txt"
        f.write_text("flask==2.0\nredis>=4.0\n# comment\n-e .\n")
        deps = _extract_deps_from_file(f)
        assert "flask" in deps
        assert "redis" in deps
        assert len(deps) == 2

    def test_pyproject_toml(self, tmp_path: Path):
        f = tmp_path / "pyproject.toml"
        f.write_text('[project]\nname = "test"\ndependencies = ["flask>=2.0", "redis"]\n')
        deps = _extract_deps_from_file(f)
        assert "flask" in deps
        assert "redis" in deps

    def test_package_json(self, tmp_path: Path):
        f = tmp_path / "package.json"
        f.write_text('{"dependencies": {"express": "^4.0"}, "devDependencies": {"jest": "^29.0"}}')
        deps = _extract_deps_from_file(f)
        assert "express" in deps
        assert "jest" in deps

    def test_empty_file(self, tmp_path: Path):
        f = tmp_path / "requirements.txt"
        f.write_text("")
        deps = _extract_deps_from_file(f)
        assert deps == []

    def test_missing_file(self, tmp_path: Path):
        deps = _extract_deps_from_file(tmp_path / "nonexistent.txt")
        assert deps == []


class TestImportScanning:
    def test_basic_imports(self, tmp_path: Path):
        py_file = tmp_path / "app.py"
        py_file.write_text("import flask\nfrom redis import StrictRedis\nimport os\n")
        from decisiondrift.impact.models import ChangedFile

        files = [ChangedFile(path="app.py", language="python", change_type="modified")]
        imports = _scan_imports_in_diff(files, tmp_path)
        import_names = [imp for imp, _ in imports]
        assert "flask" in import_names
        assert "redis" in import_names
        assert "os" in import_names

    def test_no_python_files(self, tmp_path: Path):
        from decisiondrift.impact.models import ChangedFile

        files = [ChangedFile(path="app.js", language="javascript", change_type="modified")]
        imports = _scan_imports_in_diff(files, tmp_path)
        assert imports == []

    def test_missing_file_skipped(self, tmp_path: Path):
        from decisiondrift.impact.models import ChangedFile

        files = [ChangedFile(path="missing.py", language="python", change_type="added")]
        imports = _scan_imports_in_diff(files, tmp_path)
        assert imports == []

    def test_syntax_error_skipped(self, tmp_path: Path):
        py_file = tmp_path / "broken.py"
        py_file.write_text("def broken(")
        from decisiondrift.impact.models import ChangedFile

        files = [ChangedFile(path="broken.py", language="python", change_type="modified")]
        imports = _scan_imports_in_diff(files, tmp_path)
        assert imports == []


class TestAPIScanning:
    def test_method_calls(self, tmp_path: Path):
        py_file = tmp_path / "service.py"
        py_file.write_text("db.session.execute(query)\napp.run(debug=True)\n")
        calls = _scan_api_calls(py_file)
        assert "db.session.execute" in calls
        assert "app.run" in calls

    def test_function_calls(self, tmp_path: Path):
        py_file = tmp_path / "test.py"
        py_file.write_text("print('hello')\nhelper(data)\n")
        calls = _scan_api_calls(py_file)
        assert "print" in calls
        assert "helper" in calls

    def test_empty_file(self, tmp_path: Path):
        py_file = tmp_path / "empty.py"
        py_file.write_text("")
        calls = _scan_api_calls(py_file)
        assert calls == []

    def test_missing_file(self, tmp_path: Path):
        calls = _scan_api_calls(tmp_path / "nonexistent.py")
        assert calls == []

    def test_syntax_error_returns_empty(self, tmp_path: Path):
        py_file = tmp_path / "broken.py"
        py_file.write_text("def broken(")
        calls = _scan_api_calls(py_file)
        assert calls == []


class TestConfigFileDetection:
    def test_config_extensions(self):
        assert _is_config_file("app.yaml")
        assert _is_config_file("config.yml")
        assert _is_config_file("settings.json")
        assert _is_config_file("tox.ini")
        assert _is_config_file("app.cfg")
        assert _is_config_file(".env")
        assert not _is_config_file("app.py")
        assert not _is_config_file("readme.md")

    def test_config_pattern_scan(self, tmp_path: Path):
        f = tmp_path / "config.yml"
        f.write_text("debug: true\nport: 8080\n# comment\n")
        matches = _scan_config_pattern(f, "debug")
        assert len(matches) > 0

    def test_config_missing_file(self, tmp_path: Path):
        matches = _scan_config_pattern(tmp_path / "missing.yml", "debug")
        assert matches == []


class TestRuleEnforcement:
    def test_dependency_rule_blocks(self, tmp_path: Path):
        req = tmp_path / "requirements.txt"
        req.write_text("flask==3.0\n")
        diff = "diff --git a/requirements.txt b/requirements.txt\n--- /dev/null\n+++ b/requirements.txt\n@@ -0,0 +1 @@\n+flask==3.0\n"
        rules = RuleSet(
            rules=[
                Rule(
                    id="R1",
                    type=RuleType.DEPENDENCY,
                    match="flask",
                    action=Action.BLOCK,
                    source_adr="ADR-0001",
                    confidence=ConfidenceLevel.HIGH,
                ),
            ]
        )
        result = enforce(rules, repo_path=str(tmp_path), diff_text=diff)
        assert len(result.findings) > 0
        assert result.findings[0].action == Action.BLOCK

    def test_import_rule_violation(self, tmp_path: Path):
        py_file = tmp_path / "app.py"
        py_file.write_text("import flask\n")
        diff = "diff --git a/app.py b/app.py\n--- /dev/null\n+++ b/app.py\n@@ -0,0 +1 @@\n+import flask\n"
        rules = RuleSet(
            rules=[
                Rule(
                    id="R2",
                    type=RuleType.IMPORT,
                    match="flask",
                    action=Action.BLOCK,
                    source_adr="ADR-0001",
                    confidence=ConfidenceLevel.HIGH,
                ),
            ]
        )
        result = enforce(rules, repo_path=str(tmp_path), diff_text=diff)
        assert len(result.findings) > 0

    def test_path_rule_match(self, tmp_path: Path):
        diff = "diff --git a/src/legacy/old.py b/src/legacy/old.py\n--- /dev/null\n+++ b/src/legacy/old.py\n@@ -0,0 +1 @@\n+# old\n"
        rules = RuleSet(
            rules=[
                Rule(
                    id="R3",
                    type=RuleType.PATH,
                    match=r"^src/legacy/",
                    action=Action.WARN,
                    source_adr="ADR-0002",
                    confidence=ConfidenceLevel.HIGH,
                ),
            ]
        )
        result = enforce(rules, repo_path=str(tmp_path), diff_text=diff)
        assert len(result.findings) > 0

    def test_config_rule_match(self, tmp_path: Path):
        f = tmp_path / "config.yml"
        f.write_text("debug: true\n")
        diff = "diff --git a/config.yml b/config.yml\n--- /dev/null\n+++ b/config.yml\n@@ -0,0 +1 @@\n+debug: true\n"
        rules = RuleSet(
            rules=[
                Rule(
                    id="R4",
                    type=RuleType.CONFIG,
                    match="debug",
                    action=Action.BLOCK,
                    source_adr="ADR-0003",
                    confidence=ConfidenceLevel.HIGH,
                ),
            ]
        )
        result = enforce(rules, repo_path=str(tmp_path), diff_text=diff)
        assert len(result.findings) > 0

    def test_api_rule_match(self, tmp_path: Path):
        py_file = tmp_path / "service.py"
        py_file.write_text("db.session.execute(query)\n")
        diff = "diff --git a/service.py b/service.py\n--- /dev/null\n+++ b/service.py\n@@ -0,0 +1 @@\n+db.session.execute(query)\n"
        rules = RuleSet(
            rules=[
                Rule(
                    id="R5",
                    type=RuleType.API,
                    match="db.session.execute",
                    action=Action.WARN,
                    source_adr="ADR-0004",
                    confidence=ConfidenceLevel.HIGH,
                ),
            ]
        )
        result = enforce(rules, repo_path=str(tmp_path), diff_text=diff)
        assert len(result.findings) > 0

    def test_no_violations(self, tmp_path: Path):
        req = tmp_path / "requirements.txt"
        req.write_text("fastapi==0.100\n")
        diff = "diff --git a/requirements.txt b/requirements.txt\n--- /dev/null\n+++ b/requirements.txt\n@@ -0,0 +1 @@\n+fastapi==0.100\n"
        rules = RuleSet(
            rules=[
                Rule(
                    id="R1",
                    type=RuleType.DEPENDENCY,
                    match="flask",
                    action=Action.BLOCK,
                    source_adr="ADR-0001",
                    confidence=ConfidenceLevel.HIGH,
                ),
            ]
        )
        result = enforce(rules, repo_path=str(tmp_path), diff_text=diff)
        assert len(result.findings) == 0

    def test_empty_diff(self, tmp_path: Path):
        rules = RuleSet(
            rules=[
                Rule(
                    id="R1",
                    type=RuleType.DEPENDENCY,
                    match="flask",
                    action=Action.BLOCK,
                    source_adr="ADR-0001",
                    confidence=ConfidenceLevel.HIGH,
                ),
            ]
        )
        result = enforce(rules, repo_path=str(tmp_path), diff_text="")
        assert len(result.findings) == 0

    def test_full_repo_scan(self, tmp_path: Path):
        (tmp_path / "app.py").write_text("import flask\n")
        (tmp_path / "requirements.txt").write_text("flask==3.0\n")
        rules = RuleSet(
            rules=[
                Rule(
                    id="R1",
                    type=RuleType.DEPENDENCY,
                    match="flask",
                    action=Action.BLOCK,
                    source_adr="ADR-0001",
                    confidence=ConfidenceLevel.HIGH,
                ),
                Rule(
                    id="R2",
                    type=RuleType.IMPORT,
                    match="flask",
                    action=Action.BLOCK,
                    source_adr="ADR-0001",
                    confidence=ConfidenceLevel.HIGH,
                ),
            ]
        )
        result = enforce(rules, repo_path=str(tmp_path))
        assert len(result.findings) > 0


class TestEnforceFromADRs:
    def test_single_adr_violation(self, tmp_path: Path, approved_adr: DecisionRecord):
        (tmp_path / "requirements.txt").write_text("flask==3.0\n")
        diff = "diff --git a/requirements.txt b/requirements.txt\n--- /dev/null\n+++ b/requirements.txt\n@@ -0,0 +1 @@\n+flask==3.0\n"
        result = enforce_from_adrs([approved_adr], repo_path=str(tmp_path), diff_text=diff)
        assert len(result.findings) > 0

    def test_no_violations(self, tmp_path: Path, approved_adr: DecisionRecord):
        (tmp_path / "requirements.txt").write_text("fastapi==0.100\n")
        diff = "diff --git a/requirements.txt b/requirements.txt\n--- /dev/null\n+++ b/requirements.txt\n@@ -0,0 +1 @@\n+fastapi==0.100\n"
        result = enforce_from_adrs([approved_adr], repo_path=str(tmp_path), diff_text=diff)
        assert len(result.findings) == 0

    def test_empty_adrs(self, tmp_path: Path):
        result = enforce_from_adrs([], repo_path=str(tmp_path))
        assert len(result.findings) == 0

    def test_multiple_rules_per_adr(self, tmp_path: Path, approved_adr: DecisionRecord):
        (tmp_path / "requirements.txt").write_text("flask==3.0\ndjango==4.0\n")
        (tmp_path / "app.py").write_text("import flask\nimport django\n")
        result = enforce_from_adrs([approved_adr], repo_path=str(tmp_path))
        assert len(result.findings) >= 2

    def test_load_custom_rules_from_dict(self):
        from decisiondrift.config import load_custom_rules

        config = {
            "rules": [
                {"match": "bad-lib", "type": "dependency", "action": "block", "description": "Block bad-lib"},
                {"match": "evil", "type": "import", "action": "warn", "description": "Warn on evil imports"},
            ]
        }
        ruleset = load_custom_rules(config)
        assert len(ruleset.rules) == 2
        assert ruleset.rules[0].match == "bad-lib"
        assert ruleset.rules[0].action.value == "block"
        assert ruleset.rules[1].type.value == "import"

    def test_load_custom_rules_empty(self):
        from decisiondrift.config import load_custom_rules

        ruleset = load_custom_rules({"rules": []})
        assert len(ruleset.rules) == 0

    def test_load_custom_rules_defaults(self):
        from decisiondrift.config import load_custom_rules

        ruleset = load_custom_rules({})
        assert len(ruleset.rules) == 0

    def test_custom_rules_combined_with_adr_rules(self, tmp_path: Path, approved_adr: DecisionRecord):
        from decisiondrift.config import load_custom_rules
        from decisiondrift.rules.models import Action, Rule, RuleSet, RuleType

        custom = RuleSet(
            rules=[
                Rule(
                    id="custom-1",
                    type=RuleType.DEPENDENCY,
                    match="pypopular",
                    action=Action.WARN,
                    source_adr="custom-rule",
                    description="Custom block rule",
                ),
            ]
        )
        (tmp_path / "requirements.txt").write_text("flask==3.0\npypopular==1.0\n")
        diff = "diff --git a/requirements.txt b/requirements.txt\n--- /dev/null\n+++ b/requirements.txt\n@@ -0,0 +1,2 @@\n+flask==3.0\n+pypopular==1.0\n"
        result = enforce_from_adrs([approved_adr], repo_path=str(tmp_path), diff_text=diff, custom_rules=custom)
        custom_findings = [f for f in result.findings if f.rule_id == "custom-1"]
        assert len(custom_findings) == 1
        assert "pypopular" in custom_findings[0].match_value
