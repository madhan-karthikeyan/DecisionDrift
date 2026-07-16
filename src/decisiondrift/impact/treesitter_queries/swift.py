def symbols_query() -> str:
    return """
    (class_declaration name: (type_identifier) @class.name)
    (protocol_declaration name: (type_identifier) @class.name)
    (struct_declaration name: (type_identifier) @class.name)
    (enum_declaration name: (type_identifier) @class.name)
    (function_declaration name: (simple_identifier) @method.name)
    (method_declaration name: (simple_identifier) @method.name)
    (function_declaration name: (simple_identifier) @function.name)
    (method_declaration name: (simple_identifier) @function.name)
    """


def imports_query() -> str:
    return """
    (import_declaration path: (identifier) @import)
    """


def api_calls_query() -> str:
    return """
    (call_expression function: (identifier) @call)
    (call_expression function: (member_access_expression name: (simple_identifier) @call))
    """
