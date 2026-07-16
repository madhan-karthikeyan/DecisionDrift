def symbols_query() -> str:
    return """
    (class name: (constant) @class.name)
    (method name: (identifier) @method.name)
    (singleton_method name: (identifier) @method.name)
    (method name: (identifier) @function.name)
    (singleton_method name: (identifier) @function.name)
    """


def imports_query() -> str:
    return """
    (require path: (string) @import)
    (require_relative path: (string) @import)
    (require_all path: (string) @import)
    """


def api_calls_query() -> str:
    return """
    (call receiver: [(identifier) (constant)] method: (identifier) @call)
    (call method: (identifier) @call)
    """
