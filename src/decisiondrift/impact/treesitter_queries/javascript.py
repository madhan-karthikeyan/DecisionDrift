def symbols_query() -> str:
    return """
    (class_declaration name: (identifier) @class.name)
    (method_definition name: (property_identifier) @method.name)
    (function_declaration name: (identifier) @function.name)
    (lexical_declaration (variable_declarator name: (identifier) @function.name value: [(arrow_function) (function)]))
    """


def imports_query() -> str:
    return """
    (import_statement source: (string) @import)
    (call_expression
      function: (identifier) @require
      (#eq? @require "require")
      arguments: (arguments (string) @import))
    """


def api_calls_query() -> str:
    return """
    (call_expression function: (member_expression property: (property_identifier) @call))
    (call_expression function: (identifier) @call)
    """
