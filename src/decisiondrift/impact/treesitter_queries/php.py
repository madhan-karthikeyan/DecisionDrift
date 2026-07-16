def symbols_query() -> str:
    return """
    (class_declaration name: (name) @class.name)
    (method_declaration name: (name) @method.name)
    (function_definition name: (name) @function.name)
    """


def imports_query() -> str:
    return """
    (namespace_use_clause name: (name) @import)
    (namespace_use_group_clause name: (name) @import)
    """


def api_calls_query() -> str:
    return """
    (function_call_expression function: (qualified_name) @call)
    (method_call object: (expression) name: (name) @call)
    (scoped_call_expression scope: (expression) name: (name) @call)
    """
