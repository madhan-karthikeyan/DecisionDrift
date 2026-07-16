def symbols_query() -> str:
    return """
    (class_declaration name: (identifier) @class.name)
    (method_declaration name: (identifier) @method.name)
    (interface_declaration name: (identifier) @class.name)
    (record_declaration name: (identifier) @class.name)
    (struct_declaration name: (identifier) @class.name)
    """


def imports_query() -> str:
    return """
    (using_directive name: (identifier) @import)
    (using_directive name: (qualified_name) @import)
    """


def api_calls_query() -> str:
    return """
    (invocation_expression function: (member_access_expression name: (identifier) @call))
    (invocation_expression function: (identifier) @call)
    (object_creation_expression type: (identifier) @call)
    """
