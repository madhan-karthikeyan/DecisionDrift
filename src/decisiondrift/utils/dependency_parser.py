from __future__ import annotations

import json
import re
from pathlib import Path


def parse_requirements_txt(path: Path) -> list[str]:
    deps: list[str] = []
    if not path.exists():
        return deps
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return deps
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        pkg = re.split(r"[=<>!~\[ ;]", stripped)[0].strip()
        if pkg:
            deps.append(pkg)
    return deps


def parse_pyproject_toml(path: Path) -> list[tuple[str, str]]:
    deps: list[tuple[str, str]] = []
    if not path.exists():
        return deps
    try:
        import tomllib

        data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (ImportError, OSError, ValueError):
        try:
            import tomli as tomllib

            data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (ImportError, OSError, ValueError):
            return deps

    seen: set[str] = set()
    project = data.get("project", {})
    for dep in project.get("dependencies", []):
        if isinstance(dep, str):
            name = _dep_name(dep)
            if name and name not in seen:
                seen.add(name)
                deps.append((name, "runtime"))
    for group_name, group in project.get("optional-dependencies", {}).items():
        role = "test" if any(t in group_name.lower() for t in ("test", "pytest", "tox")) else "dev"
        if isinstance(group, list):
            for dep in group:
                if isinstance(dep, str):
                    name = _dep_name(dep)
                    if name and name not in seen:
                        seen.add(name)
                        deps.append((name, role))
    for group_name, group in data.get("dependency-groups", {}).items():
        role = "test" if any(t in group_name.lower() for t in ("test", "pytest", "tox")) else "dev"
        if isinstance(group, list):
            for dep in group:
                if isinstance(dep, str):
                    name = _dep_name(dep)
                    if name and name not in seen:
                        seen.add(name)
                        deps.append((name, role))
    return deps


def parse_package_json(path: Path) -> list[tuple[str, str]]:
    deps: list[tuple[str, str]] = []
    if not path.exists():
        return deps
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return deps
    sections = {
        "dependencies": "runtime",
        "devDependencies": "dev",
        "peerDependencies": "optional",
        "optionalDependencies": "optional",
    }
    seen: set[str] = set()
    for section, role in sections.items():
        values = data.get(section, {})
        if isinstance(values, dict):
            for pkg in values:
                if pkg and pkg not in seen:
                    seen.add(pkg)
                    deps.append((pkg, role))
    return deps


def parse_go_mod(path: Path) -> tuple[str | None, list[str]]:
    if not path.exists():
        return None, []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, []
    module_match = re.search(r"^module\s+(\S+)", text, re.MULTILINE)
    module_name = module_match.group(1) if module_match else None
    deps: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        m = re.match(r"^\s+([^\s]+)\s+v", line)
        if m:
            pkg = m.group(1).strip()
            if pkg and pkg not in seen:
                seen.add(pkg)
                deps.append(pkg)
    return module_name, deps


def parse_cargo_toml(path: Path) -> tuple[str | None, list[tuple[str, str]]]:
    if not path.exists():
        return None, []
    try:
        import tomllib

        data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (ImportError, OSError, ValueError):
        try:
            import tomli as tomllib

            data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (ImportError, OSError, ValueError):
            return None, []
    pkg = data.get("package", {})
    package_name = pkg.get("name") if isinstance(pkg, dict) else None
    deps: list[tuple[str, str]] = []
    seen: set[str] = set()
    for section, role in (
        ("dependencies", "runtime"),
        ("dev-dependencies", "dev"),
        ("build-dependencies", "tooling"),
    ):
        section_deps = data.get(section, {})
        if isinstance(section_deps, dict):
            for dep in section_deps:
                if dep and dep not in seen:
                    seen.add(dep)
                    deps.append((dep, role))
    return package_name, deps


def parse_gemfile(path: Path) -> list[tuple[str, str]]:
    deps: list[tuple[str, str]] = []
    if not path.exists():
        return deps
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return deps
    seen: set[str] = set()
    in_group: str = "runtime"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("group"):
            if "test" in stripped.lower() or "development" in stripped.lower():
                in_group = "dev"
            else:
                in_group = "runtime"
        elif stripped.startswith("end"):
            in_group = "runtime"
        elif stripped.startswith("gem "):
            parts = stripped.split()
            if len(parts) >= 2:
                name = parts[1].strip("\"',")
                if name and name not in seen:
                    seen.add(name)
                    deps.append((name, in_group))
    return deps


def parse_gemfile_lock(path: Path) -> list[tuple[str, str]]:
    deps: list[tuple[str, str]] = []
    if not path.exists():
        return deps
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return deps
    seen: set[str] = set()
    in_specs = False
    for line in text.splitlines():
        if line.strip() == "GEM":
            in_specs = False
            continue
        if line.strip().startswith("specs:"):
            in_specs = True
            continue
        if in_specs:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("PLATFORMS") and not stripped.startswith("DEPENDENCIES"):
                name = stripped.split()[0].strip("()")
                if name and name not in seen:
                    seen.add(name)
                    deps.append((name, "runtime"))
            elif stripped == "" or stripped.startswith("PLATFORMS"):
                in_specs = False
    return deps


def parse_composer_json(path: Path) -> list[tuple[str, str]]:
    deps: list[tuple[str, str]] = []
    if not path.exists():
        return deps
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return deps
    seen: set[str] = set()
    for section, role in (("require", "runtime"), ("require-dev", "dev")):
        entries = data.get(section, {})
        if isinstance(entries, dict):
            for pkg in entries:
                if pkg and pkg not in seen:
                    seen.add(pkg)
                    deps.append((pkg, role))
    return deps


def parse_csproj(path: Path) -> list[tuple[str, str]]:
    deps: list[tuple[str, str]] = []
    if not path.exists():
        return deps
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return deps
    seen: set[str] = set()
    for m in re.finditer(r'PackageReference\s+Include="([^"]+)"', text):
        pkg = m.group(1)
        if pkg and pkg not in seen:
            seen.add(pkg)
            deps.append((pkg, "runtime"))
    return deps


def parse_build_gradle_kts(path: Path) -> list[tuple[str, str]]:
    deps: list[tuple[str, str]] = []
    if not path.exists():
        return deps
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return deps
    seen: set[str] = set()
    config_role = {
        "implementation": "runtime",
        "api": "runtime",
        "compileOnly": "runtime",
        "runtimeOnly": "runtime",
        "testImplementation": "dev",
        "testRuntimeOnly": "dev",
        "androidTestImplementation": "dev",
        "kapt": "tooling",
        "ksp": "tooling",
    }
    for config, role in config_role.items():
        for m in re.finditer(
            rf'{re.escape(config)}\s*\(\s*"([^"]+)"',
            text,
        ):
            pkg = m.group(1).strip()
            if pkg and pkg not in seen:
                seen.add(pkg)
                deps.append((pkg, role))
    return deps


def parse_package_swift(path: Path) -> list[tuple[str, str]]:
    deps: list[tuple[str, str]] = []
    if not path.exists():
        return deps
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return deps
    seen: set[str] = set()
    for m in re.finditer(r'\.package\(url:\s*"([^"]+)"', text):
        url = m.group(1)
        name = url.rstrip("/").split("/")[-1].replace(".git", "")
        if name and name not in seen:
            seen.add(name)
            deps.append((name, "runtime"))
    for m in re.finditer(r'//\s*dependency\s+"([^"]+)"', text):
        name = m.group(1)
        if name and name not in seen:
            seen.add(name)
            deps.append((name, "runtime"))
    return deps


def _dep_name(value: str) -> str:
    return re.split(r"[=<>!~\[ ;]", value.strip())[0].strip()
