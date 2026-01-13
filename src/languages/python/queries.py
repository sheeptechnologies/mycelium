from .handlers import *

PYTHON_QUERIES = {
    # ==========================================================================
    # MODULE
    # ==========================================================================
    # "(module)@module": [{"module": handle_module}],
    
    # ==========================================================================
    # IMPORTS (CRITICO)
    # ==========================================================================
    "(import_statement)@import_statement": [{"import_statement": handle_import_statement}],
    "(import_from_statement)@import_from_statement": [{"import_from_statement": handle_import_from_statement}],
    "(relative_import)@relative_import": [{"relative_import": handle_relative_import}],
    "(wildcard_import)@wildcard_import": [{"wildcard_import": handle_wildcard_import}],
    "(dotted_name)@dotted_name": [{"dotted_name": handle_dotted_name}],
    "(import_prefix)@import_prefix": [{"import_prefix": handle_import_prefix}],
    
    # ==========================================================================
    # DECORATORS
    # ==========================================================================
    "(decorated_definition)@decorated_definition": [{"decorated_definition": handle_decorated_definition}],
    "(decorator)@decorator": [{"decorator": handle_decorator}],
    
    # ==========================================================================
    # CONTROL FLOW
    # ==========================================================================
    "(if_statement)@if_statement": [{"if_statement": handle_if_statement}],
    "(elif_clause)@elif_clause": [{"elif_clause": handle_elif_clause}],
    "(else_clause)@else_clause": [{"else_clause": handle_else_clause}],
    "(for_statement)@for_statement": [{"for_statement": handle_for_statement}],
    "(while_statement)@while_statement": [{"while_statement": handle_while_statement}],
    "(match_statement)@match_statement": [{"match_statement": handle_match_statement}],
    "(case_clause)@case_clause": [{"case_clause": handle_case_clause}],
    
    # ==========================================================================
    # EXCEPTIONS
    # ==========================================================================
    "(try_statement)@try_statement": [{"try_statement": handle_try_statement}],
    "(except_clause)@except_clause": [{"except_clause": handle_except_clause}],
    "(finally_clause)@finally_clause": [{"finally_clause": handle_finally_clause}],
    "(raise_statement)@raise_statement": [{"raise_statement": handle_raise_statement}],
    
    # ==========================================================================
    # CONTEXT MANAGERS
    # ==========================================================================
    "(with_statement)@with_statement": [{"with_statement": handle_with_statement}],
    "(with_item)@with_item": [{"with_item": handle_with_item}],
    
    # ==========================================================================
    # STATEMENTS
    # ==========================================================================
    "(global_statement)@global_statement": [{"global_statement": handle_global_statement}],
    "(nonlocal_statement)@nonlocal_statement": [{"nonlocal_statement": handle_nonlocal_statement}],
    "(break_statement)@break_statement": [{"break_statement": handle_break_statement}],
    "(continue_statement)@continue_statement": [{"continue_statement": handle_continue_statement}],
    "(delete_statement)@delete_statement": [{"delete_statement": handle_delete_statement}],
    "(assert_statement)@assert_statement": [{"assert_statement": handle_assert_statement}],
    "(expression_statement)@expression_statement": [{"expression_statement": handle_expression_statement}],
    "(print_statement)@print_statement": [{"print_statement": handle_print_statement}],
    
    # ==========================================================================
    # DATA STRUCTURES
    # ==========================================================================
    "(tuple)@tuple": [{"tuple": handle_tuple}],
    "(list)@list": [{"list": handle_list}],
    "(dictionary)@dictionary": [{"dictionary": handle_dictionary}],
    "(set)@set": [{"set": handle_set}],
    "(pair)@pair": [{"pair": handle_pair}],
    "(list_comprehension)@list_comprehension": [{"list_comprehension": handle_list_comprehension}],
    "(dictionary_comprehension)@dictionary_comprehension": [{"dictionary_comprehension": handle_dictionary_comprehension}],
    "(set_comprehension)@set_comprehension": [{"set_comprehension": handle_set_comprehension}],
    "(generator_expression)@generator_expression": [{"generator_expression": handle_generator_expression}],
    
    # ==========================================================================
    # EXPRESSIONS
    # ==========================================================================
    "(subscript)@subscript": [{"subscript": handle_subscript}],
    "(binary_operator)@binary_operator": [{"binary_operator": handle_binary_operator}],
    "(unary_operator)@unary_operator": [{"unary_operator": handle_unary_operator}],
    "(comparison_operator)@comparison_operator": [{"comparison_operator": handle_comparison_operator}],
    "(boolean_operator)@boolean_operator": [{"boolean_operator": handle_boolean_operator}],
    "(conditional_expression)@conditional_expression": [{"conditional_expression": handle_conditional_expression}],
    "(named_expression)@named_expression": [{"named_expression": handle_named_expression}],
    "(list_splat)@list_splat": [{"list_splat": handle_list_splat}],
    "(dictionary_splat)@dictionary_splat": [{"dictionary_splat": handle_dictionary_splat}],
    "(expression_list)@expression_list": [{"expression_list": handle_expression_list}],
    
    # ==========================================================================
    # PATTERN MATCHING (Python 3.10+)
    # ==========================================================================
    "(as_pattern)@as_pattern": [{"as_pattern": handle_as_pattern}],
    "(tuple_pattern)@tuple_pattern": [{"tuple_pattern": handle_tuple_pattern}],
    "(list_pattern)@list_pattern": [{"list_pattern": handle_list_pattern}],
    "(dict_pattern)@dict_pattern": [{"dict_pattern": handle_dict_pattern}],
    "(class_pattern)@class_pattern": [{"class_pattern": handle_class_pattern}],
    "(splat_pattern)@splat_pattern": [{"splat_pattern": handle_splat_pattern}],
    "(union_pattern)@union_pattern": [{"union_pattern": handle_union_pattern}],
    "(keyword_pattern)@keyword_pattern": [{"keyword_pattern": handle_keyword_pattern}],
    "(case_pattern)@case_pattern": [{"case_pattern": handle_case_pattern}],
    "(pattern_list)@pattern_list": [{"pattern_list": handle_pattern_list}],
    
    # ==========================================================================
    # ADVANCED PARAMETERS
    # ==========================================================================
    "(default_parameter)@default_parameter": [{"default_parameter": handle_default_parameter}],
    "(list_splat_pattern)@list_splat_pattern": [{"list_splat_pattern": handle_list_splat_pattern}],
    "(dictionary_splat_pattern)@dictionary_splat_pattern": [{"dictionary_splat_pattern": handle_dictionary_splat_pattern}],
    "(lambda_parameters)@lambda_parameters": [{"lambda_parameters": handle_lambda_parameters}],
    "(argument_list)@argument_list": [{"argument_list": handle_argument_list}],
    "(keyword_argument)@keyword_argument": [{"keyword_argument": handle_keyword_argument}],
    
    # ==========================================================================
    # BLOCKS
    # ==========================================================================
    "(block)@block": [{"block": handle_block}],
    
    # ==========================================================================
    # EXISTING HANDLERS (maintained)
    # ==========================================================================
    "(assignment)@assignment": [{"assignment": handle_assignment}],
    "(call)@call": [{"call": handle_call}],
    "(attribute)@attribute": [{"attribute": handle_attribute}],
    "(identifier)@identifier": [{"identifier": handle_identifier}],
    "(class_definition)@class_definition": [{"class_definition": handle_class_definition}],
    "(function_definition)@function_definition": [{"function_definition": handle_function_definition}],
    "(return_statement)@return_statement": [{"return_statement": handle_return_statement}],
    "(lambda)@lambda": [{"lambda": handle_lambda}],
    "(typed_parameter)@typed_parameter": [{"typed_parameter": handle_typed_parameter}],
    "(typed_default_parameter)@typed_default_parameter": [{"typed_default_parameter": handle_typed_default_parameter}],

    # ==========================================================================
    # ASYNC/AWAIT CONSTRUCTS
    # ==========================================================================
    "(decorated_definition)@async_function": [{"async_function": handle_async_function_definition}],
    "(with_statement)@async_with": [{"async_with": handle_async_with_statement}],
    "(for_statement)@async_for": [{"async_for": handle_async_for_statement}],
    "(await)@await": [{"await": handle_await_expression}],

    # ==========================================================================
    # YIELD CONSTRUCTS
    # ==========================================================================
    "(yield)@yield": [{"yield": handle_yield_statement}],
    "(expression_statement (yield))@yield_stmt": [{"yield_stmt": handle_yield_statement}],

    # ==========================================================================
    # AUGMENTED ASSIGNMENT
    # ==========================================================================
    "(augmented_assignment)@augmented_assignment": [{"augmented_assignment": handle_augmented_assignment}],
}
