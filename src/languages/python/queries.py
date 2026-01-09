from .handlers import *

PYTHON_QUERIES = {

    "(module)@module": [{ "module": handle_module}],
    "(assignment)@assignment": [{"assignment" : handle_assignment}],
    "(call)@call": [{"call": handle_call},],
    "(attribute)@attribute": [{"attribute": handle_attribute}],
    "(identifier) @identifier": [{"identifier": handle_identifier}],
    "(class_definition)@class_definition":  [{"class_definition": handle_class_definition},],
    "(function_definition)@function_definition":[{"function_definition": handle_function_definition},],
    "(expression_statement (_))@expression_statement_assignment": [{"expression_statement_assignment": handle_expression_statement_assignment},],
    "(typed_parameter)@typed_parameter": [{"typed_parameter":handle_typed_parameter}],
    "(typed_default_parameter)@typed_default_parameter": [{"typed_default_parameter":handle_typed_default_parameter}],
    "(return_statement)@return_statement": [{"return_statement":handle_return_statement}],

    "(lambda) @lambda": [{"lambda": handle_lambda}],
    # "(list_comprehension) @list_comprehension": [{"list_comprehension": handle_comprehension}],
    # --- IMPORT (Critico) ---
    # "(import_statement) @import_statement": [{"import_statement": handle_import_statement}],
    # "(import_from_statement) @import_from_statement": [{"import_from_statement": handle_import_from_statement}],
    # "(subscript) @subscript": [{"subscript": handle_subscript}],
    # "(decorator) @decorator": [{"decorator": handle_decorator}],
    # "(keyword_argument) @keyword_argument": [{"keyword_argument": handle_keyword_argument}],
}
