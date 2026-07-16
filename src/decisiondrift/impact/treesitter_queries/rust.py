def symbols_query() -> str:
    return """
    (struct_item name: (type_identifier) @class.name)
    (impl_item (function_item name: (identifier) @method.name))
    (function_item name: (identifier) @function.name)
    """


def imports_query() -> str:
    return """
    (use_declaration argument: (use_path (identifier) @import))
    (extern_crate_declaration name: (identifier) @import)
    """


def api_calls_query() -> str:
    return """
    (call_expression function: (field_expression field: (field_identifier) @call))
    (call_expression function: (identifier) @call)
    """
