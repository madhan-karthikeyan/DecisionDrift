def symbols_query() -> str:
    return """
    (type_spec name: (type_identifier) @class.name type: (struct_type))
    (method_declaration name: (field_identifier) @method.name)
    (function_declaration name: (identifier) @function.name)
    """


def imports_query() -> str:
    return """
    (import_spec path: (interpreted_string_literal) @import)
    """


def api_calls_query() -> str:
    return """
    (call_expression function: (selector_expression field: (field_identifier) @call))
    (call_expression function: (identifier) @call)
    """
