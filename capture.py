"""
This module contains the functions given as parameters to the Capure objects in the ballang module. They construct the AST from the parsed grammar.
"""
from typing import Dict, List, TypeVar, cast
from .node import CodeBlockNode, IfNode, Node, SymbolNode, TwoSideOpNode, UnaryOpNode, VarNode, VarDefNode, AssignNode, FuncCallNode, FunctionDefNode, FuncArgNode, CodeFileNode, ReturnNode, whileNode, WordNode


def parse_op(symbol: str, left: Node, right: Node):
    """
    Parse a twoside operator

    Args:
        symbol (str): the operator symbol
        left (Node): the left side of the operator
        right (Node): the right side of the operator

    Returns:
        Node: the parsed operator
    """
    assert symbol in ["+", "-", "*", "/", "<", ">", "==",
                      "!=", "<=", ">=", "&&", "||"], f"unknown symbol {symbol}"
    return TwoSideOpNode(symbol, left, right)
   # raise Exception("unknown symbol")


def twoside_op_capture(x: Dict[str, Node]) -> Node:
    """
    Parse a twoside operator
    
    Args:
        x (Dict[str, Node]): the parsed operator. Should contain the keys "left", "right" and "symbol"

    Returns:
        Node: the parsed operator
    """
    if "right" in x:
        symbol = x["symbol"]
        assert isinstance(symbol, SymbolNode)
        return parse_op(symbol.symbol, x["left"], x["right"])
    else:
        return x["left"]


def unary_op_capture(x: Dict[str, Node]) -> Node:
    """
    Parse a unary operator
    
    Args:
        x (Dict[str, Node]): the parsed operator. Should contain the keys "sign" and "node"

    Returns:
        Node: the parsed operator
    """
    sign = x["sign"]
    assert isinstance(sign, SymbolNode)
    return UnaryOpNode(sign.symbol, x["node"])


NodeT = TypeVar("NodeT")


def extract_multiple(x: Dict[str, Node], key: str) -> List[Node]:
    """
    Extract multiple nodes from a dictionary, used for parsing the Multiple grammar rule

    Args:
        x (Dict[str, Node]): the dictionary to extract from
        key (str): the key to extract

    Returns:
        List[Node]: the list of nodes
    """
    i = 0
    items = []
    while f"{key}{i}" in x:
        items.append(x[f"{key}{i}"])
        i += 1

    return items


def block_capture(x: Dict[str, Node]) -> CodeBlockNode:
    """
    Parse a block of code
    
    Args:
        x (Dict[str, Node]): the parsed block. Should contain multiple "statement_{i}" keys, where i is a number

    Returns:
        CodeBlockNode: the parsed block
    """
    statements = extract_multiple(x, "statement")
    return CodeBlockNode(statements)


def if_capture(x: Dict[str, Node]) -> IfNode:
    """
    Parse an if statement with optional elif and else blocks

    Args:
        x (Dict[str, Node]): the parsed if statement. Should contain the keys "condition", "then_block", "elif_cond_{i}", "elif_block_{i}" and "else_block"

    Returns:
        IfNode: the parsed if statement
    """
    condition = x["condition"]
    then_block = x["then_block"]
    assert isinstance(then_block, CodeBlockNode)
    elif_conds = extract_multiple(x, "elif_cond")
    elif_blocks = extract_multiple(x, "elif_block")
    for block in elif_blocks:
        assert isinstance(block, CodeBlockNode)
    if "else_block" in x:
        else_block = x["else_block"]
        assert isinstance(else_block, CodeBlockNode)
        return IfNode(condition, then_block, elif_conds, cast(List[CodeBlockNode], elif_blocks), else_block)

    return IfNode(condition, then_block, elif_conds, cast(List[CodeBlockNode], elif_blocks), None)


def var_capture(x: Dict[str, Node]) -> Node:
    """
    Parse a variable
    
    Args:
        x (Dict[str, Node]): the parsed variable. Should contain the key "name"
        
    Returns:
        Node: the parsed variable
    """
    nameNode = x["name"]
    assert isinstance(nameNode, WordNode)
    return VarNode(nameNode.word)


def var_def_capture(x: Dict[str, Node]) -> Node:
    """
    Parse a variable definition with optional value
    
    Args:
        x (Dict[str, Node]): the parsed variable definition. Should contain the key "name" and optionally "value"

    Returns:
        Node: the parsed variable definition
    """
    nameNode = x["name"]
    assert isinstance(nameNode, WordNode)
    if "value" in x:
        valueNode = x["value"]
        return VarDefNode(nameNode.word, valueNode)
    return VarDefNode(nameNode.word)


def assign_capture(x: Dict[str, Node]) -> Node:#
    """
    Parse an assignment

    Args:
        x (Dict[str, Node]): the parsed assignment. Should contain the key "lhand" and optionally "rhand"

    Returns:
        Node: the parsed assignment
    """
    lhandNode = x["lhand"]
    assert isinstance(lhandNode, Node)
    if "rhand" in x:
        rhandNode = x["rhand"]
        assert isinstance(lhandNode, VarNode)
        return AssignNode(lhandNode, rhandNode)
    return lhandNode


def func_call_capture(x: Dict[str, Node]) -> Node:
    """
    Parse a function call

    Args:
        x (Dict[str, Node]): the parsed function call. Should contain the keys "var" and "arg_{i}"

    Returns:
        Node: the parsed function call
    """
    varNode = x["var"]
    assert isinstance(varNode, VarNode)
    args = extract_multiple(x, "arg")
    return FuncCallNode(varNode, args)


def while_capture(x: Dict[str, Node]) -> Node:
    """
    Parse a while loop

    Args:
        x (Dict[str, Node]): the parsed while loop. Should contain the keys "condition" and "body"

    Returns:
        Node: the parsed while loop
    """
    condition = x["condition"]
    then_block = x["body"]
    assert isinstance(then_block, CodeBlockNode)
    return whileNode(condition, then_block)


def func_arg_capture(x: Dict[str, Node]) -> Node:
    """
    Parse a function argument
    
    Args:
        x (Dict[str, Node]): the parsed function argument. Should contain the key "name"
        
    Returns:
        Node: the parsed function argument
    """
    nameNode = x["name"]
    assert isinstance(nameNode, WordNode)
    return FuncArgNode(nameNode.word)


def func_def_capture(x: Dict[str, Node]) -> Node:
    """
    Parse a function definition
    
    Args:
        x (Dict[str, Node]): the parsed function definition. Should contain the keys "name", "arg_{i}" and "body"

    Returns:
        Node: the parsed function definition
    """
    nameNode = x["name"]
    assert isinstance(nameNode, WordNode)
    args = extract_multiple(x, "arg")
    for arg in args:
        assert isinstance(arg, FuncArgNode)
    body = x["body"]
    assert isinstance(body, CodeBlockNode)
    return FunctionDefNode(nameNode.word, body, cast(List[FuncArgNode], args))


def file_capture(x: Dict[str, Node]) -> Node:
    """
    Parse a file

    Args:
        x (Dict[str, Node]): the parsed file. Should contain the keys "function

    Returns:
        Node: the parsed file
    """
    functions = extract_multiple(x, "function")
    for func in functions:
        assert isinstance(func, FunctionDefNode)
    return CodeFileNode(cast(List[FunctionDefNode], functions))


def return_capture(x: Dict[str, Node]) -> Node:
    """
    Parse a return statement

    Args:
        x (Dict[str, Node]): the parsed return statement. Should contain the key "value"

    Returns:
        Node: the parsed return statement
    """
    if "value" in x:
        return ReturnNode(x["value"])
    return ReturnNode()
