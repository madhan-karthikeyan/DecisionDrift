from __future__ import annotations

from decisiondrift.impact.ast_python import extract_symbols


class TestExtractSymbols:
    def test_class_extraction(self):
        source = """
class UserRepository:
    def find_by_id(self):
        pass

    async def find_all(self):
        pass
"""
        symbols = extract_symbols("test.py", source)
        classes = [s for s in symbols if s.symbol_type == "class"]
        methods = [s for s in symbols if s.symbol_type == "method"]
        assert len(classes) == 1
        assert classes[0].name == "UserRepository"
        assert len(methods) == 2
        assert {m.name for m in methods} == {"find_by_id", "find_all"}

    def test_function_extraction(self):
        source = """
def get_user():
    pass

async def create_user():
    pass
"""
        symbols = extract_symbols("test.py", source)
        funcs = [s for s in symbols if s.symbol_type == "function"]
        assert len(funcs) == 2
        assert {f.name for f in funcs} == {"get_user", "create_user"}

    def test_module_level_and_methods(self):
        source = """
import os


def helper():
    pass


class UserService:
    def create(self):
        pass


class PostgresAdapter:
    def connect(self):
        pass
"""
        symbols = extract_symbols("test.py", source)
        classes = [s for s in symbols if s.symbol_type == "class"]
        funcs = [s for s in symbols if s.symbol_type == "function"]
        methods = [s for s in symbols if s.symbol_type == "method"]
        assert {c.name for c in classes} == {"UserService", "PostgresAdapter"}
        assert {f.name for f in funcs} == {"helper"}
        assert {m.name for m in methods} == {"create", "connect"}

    def test_syntax_error_does_not_crash(self):
        source = "def broken("
        symbols = extract_symbols("broken.py", source)
        assert symbols == []

    def test_empty_file(self):
        symbols = extract_symbols("empty.py", "")
        assert symbols == []

    def test_line_numbers(self):
        source = """def hello():
    print("hi")


class Foo:
    def bar(self):
        pass
"""
        symbols = extract_symbols("test.py", source)
        hello = next(s for s in symbols if s.name == "hello")
        assert hello.start_line == 1
        assert hello.end_line == 2
        foo = next(s for s in symbols if s.name == "Foo")
        assert foo.start_line == 5
        assert foo.end_line == 7
