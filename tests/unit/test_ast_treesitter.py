from __future__ import annotations

from pathlib import Path

import pytest

from decisiondrift.impact.ast_treesitter import HAS_TREESITTER, extract_symbols_treesitter

pytestmark = pytest.mark.skipif(
    not HAS_TREESITTER,
    reason="tree-sitter not installed (pip install decisiondrift[ast])",
)


class TestTreeSitterJavaScript:
    def test_extract_class_and_function(self, tmp_path: Path):
        js_file = tmp_path / "app.js"
        js_file.write_text("""
class UserController {
    getUser(id) { return id; }
    async createUser(data) { return data; }
}
function helper() { return null; }
""")
        symbols = extract_symbols_treesitter(str(js_file), "javascript")
        names = {s.name for s in symbols}
        assert "UserController" in names
        assert "getUser" in names
        assert "createUser" in names
        assert "helper" in names

    def test_arrow_function(self, tmp_path: Path):
        js_file = tmp_path / "arrow.js"
        js_file.write_text("const greet = (name) => `Hello ${name}`;\n")
        symbols = extract_symbols_treesitter(str(js_file), "javascript")
        assert len(symbols) >= 1

    def test_malformed_source_does_not_crash(self, tmp_path: Path):
        js_file = tmp_path / "broken.js"
        js_file.write_text("const x = ")
        symbols = extract_symbols_treesitter(str(js_file), "javascript")
        assert isinstance(symbols, list)

    def test_empty_file(self, tmp_path: Path):
        js_file = tmp_path / "empty.js"
        js_file.write_text("")
        symbols = extract_symbols_treesitter(str(js_file), "javascript")
        assert symbols == []


class TestTreeSitterTypeScript:
    def test_extract_class_and_method(self, tmp_path: Path):
        ts_file = tmp_path / "app.ts"
        ts_file.write_text("""
class UserService {
    findById(id: string): Promise<User> {
        return Promise.resolve({} as User);
    }
}
function helper(): void {}
""")
        symbols = extract_symbols_treesitter(str(ts_file), "typescript")
        names = {s.name for s in symbols}
        assert "UserService" in names
        assert "findById" in names
        assert "helper" in names

    def test_interface_not_extracted_as_class(self, tmp_path: Path):
        ts_file = tmp_path / "types.ts"
        ts_file.write_text("interface User { id: string; name: string; }\n")
        symbols = extract_symbols_treesitter(str(ts_file), "typescript")
        class_names = {s.name for s in symbols if s.symbol_type == "class"}
        assert "User" not in class_names


class TestTreeSitterGo:
    def test_extract_struct_and_function(self, tmp_path: Path):
        go_file = tmp_path / "main.go"
        go_file.write_text("""
package main

type Server struct {
    Port int
}

func (s *Server) Listen() error {
    return nil
}

func main() {}
""")
        symbols = extract_symbols_treesitter(str(go_file), "go")
        names = {s.name for s in symbols}
        assert "Server" in names
        assert "Listen" in names
        assert "main" in names

    def test_malformed_source_does_not_crash(self, tmp_path: Path):
        go_file = tmp_path / "broken.go"
        go_file.write_text("package main\nfunc ")
        symbols = extract_symbols_treesitter(str(go_file), "go")
        assert isinstance(symbols, list)


class TestTreeSitterJava:
    def test_extract_class_and_method(self, tmp_path: Path):
        java_file = tmp_path / "App.java"
        java_file.write_text("""
public class App {
    public static void main(String[] args) {}
    private String getName() { return ""; }
}
""")
        symbols = extract_symbols_treesitter(str(java_file), "java")
        names = {s.name for s in symbols}
        assert "App" in names
        assert "main" in names
        assert "getName" in names

    def test_empty_class(self, tmp_path: Path):
        java_file = tmp_path / "Empty.java"
        java_file.write_text("public class Empty {}\n")
        symbols = extract_symbols_treesitter(str(java_file), "java")
        class_names = {s.name for s in symbols if s.symbol_type == "class"}
        assert "Empty" in class_names


class TestTreeSitterRust:
    def test_extract_struct_and_function(self, tmp_path: Path):
        rs_file = tmp_path / "main.rs"
        rs_file.write_text("""
struct Config {
    port: u16,
}

impl Config {
    fn load() -> Self {
        Config { port: 8080 }
    }
}

fn main() {}
""")
        symbols = extract_symbols_treesitter(str(rs_file), "rust")
        names = {s.name for s in symbols}
        assert "Config" in names
        assert "load" in names
        assert "main" in names

    def test_malformed_source_does_not_crash(self, tmp_path: Path):
        rs_file = tmp_path / "broken.rs"
        rs_file.write_text("fn main( ")
        symbols = extract_symbols_treesitter(str(rs_file), "rust")
        assert isinstance(symbols, list)

    def test_unsupported_language_returns_empty(self, tmp_path: Path):
        rb_file = tmp_path / "test.rb"
        rb_file.write_text("class Foo; end\n")
        symbols = extract_symbols_treesitter(str(rb_file), "ruby")
        assert symbols == []
