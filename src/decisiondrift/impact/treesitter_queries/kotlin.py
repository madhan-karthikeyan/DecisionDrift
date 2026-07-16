def symbols_query() -> str:
    return """
    (class_declaration name: (type_identifier) @class.name)
    (function_declaration name: (simple_identifier) @method.name)
    (object_declaration name: (simple_identifier) @class.name)
    """


def imports_query() -> str:
    return """
    (import_header path: (identifier) @import)
    """


def api_calls_query() -> str:
    return """
    (call_expression function: (simple_identifier) @call)
    (call_expression function: (navigation_expression name: (simple_identifier) @call))
    """
