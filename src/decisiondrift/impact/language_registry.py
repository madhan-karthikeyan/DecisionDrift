from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class LanguageInfo:
    name: str
    extensions: list[str]
    treesitter_grammar: str | None = None
    dependency_files: list[str] = field(default_factory=list)


LANGUAGE_REGISTRY: dict[str, LanguageInfo] = {
    "python": LanguageInfo(
        name="python",
        extensions=[".py"],
        treesitter_grammar="python",
        dependency_files=["requirements.txt", "pyproject.toml", "setup.py"],
    ),
    "javascript": LanguageInfo(
        name="javascript",
        extensions=[".js", ".jsx"],
        treesitter_grammar="javascript",
        dependency_files=["package.json"],
    ),
    "typescript": LanguageInfo(
        name="typescript",
        extensions=[".ts"],
        treesitter_grammar="typescript",
        dependency_files=["package.json"],
    ),
    "tsx": LanguageInfo(
        name="tsx",
        extensions=[".tsx"],
        treesitter_grammar="tsx",
        dependency_files=["package.json"],
    ),
    "go": LanguageInfo(
        name="go",
        extensions=[".go"],
        treesitter_grammar="go",
        dependency_files=["go.mod"],
    ),
    "rust": LanguageInfo(
        name="rust",
        extensions=[".rs"],
        treesitter_grammar="rust",
        dependency_files=["Cargo.toml"],
    ),
    "java": LanguageInfo(
        name="java",
        extensions=[".java"],
        treesitter_grammar="java",
        dependency_files=["pom.xml", "build.gradle", "build.gradle.kts"],
    ),
    "ruby": LanguageInfo(
        name="ruby",
        extensions=[".rb"],
        treesitter_grammar="ruby",
        dependency_files=["Gemfile", "Gemfile.lock"],
    ),
    "php": LanguageInfo(
        name="php",
        extensions=[".php"],
        treesitter_grammar="php",
        dependency_files=["composer.json"],
    ),
    "c_sharp": LanguageInfo(
        name="c_sharp",
        extensions=[".cs"],
        treesitter_grammar="c_sharp",
        dependency_files=["*.csproj"],
    ),
    "kotlin": LanguageInfo(
        name="kotlin",
        extensions=[".kt", ".kts"],
        treesitter_grammar="kotlin",
        dependency_files=["build.gradle.kts"],
    ),
    "swift": LanguageInfo(
        name="swift",
        extensions=[".swift"],
        treesitter_grammar="swift",
        dependency_files=["Package.swift"],
    ),
    "c": LanguageInfo(
        name="c",
        extensions=[".c", ".h"],
        treesitter_grammar="c",
    ),
    "cpp": LanguageInfo(
        name="cpp",
        extensions=[".cpp", ".hpp"],
        treesitter_grammar="cpp",
    ),
}


EXTENSION_TO_LANGUAGE: dict[str, str] = {}
for lang_name, info in LANGUAGE_REGISTRY.items():
    for ext in info.extensions:
        EXTENSION_TO_LANGUAGE[ext] = lang_name


def language_for_extension(ext: str) -> str | None:
    return EXTENSION_TO_LANGUAGE.get(ext.lower())


def extensions_for_language(name: str) -> list[str]:
    info = LANGUAGE_REGISTRY.get(name)
    return list(info.extensions) if info else []
