def symbols_query() -> str:
    return """
    (class_declaration name: (identifier) @class.name)
    (method_declaration name: (identifier) @method.name)
    """


def imports_query() -> str:
    return """
    (import_declaration name: (scoped_identifier) @import)
    """


def api_calls_query() -> str:
    return """
    (method_invocation name: (identifier) @call)
    """
