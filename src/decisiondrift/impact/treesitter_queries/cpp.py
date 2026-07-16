def symbols_query() -> str:
    return """
    (class_specifier name: (type_identifier) @class.name)
    (function_definition declarator: (function_declarator declarator: (identifier) @function.name))
    """


def imports_query() -> str:
    return """
    (preproc_include path: (string_literal) @import)
    (preproc_include path: (system_lib_string) @import)
    (using_declaration name: (identifier) @import)
    """


def api_calls_query() -> str:
    return """
    (call_expression function: (identifier) @call)
    (call_expression function: (field_expression) @call)
    """
