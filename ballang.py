from abc import ABC
from typing import Dict, List, Optional, TypeVar, cast

from .grammar import AnyNumber, AnyString, AnyWord, Capture, Labeled, Maybe, Multiple, Sequence, Symbol, SymbolParser, Word
from .lexer import TokenStream, lex
from .node import CodeFileNode, FuncArgNode, FunctionDefNode, Node, NumberNode, ReturnNode, StringNode, SymbolNode, TwoSideOpNode, UnaryOpNode,  VarNode, VarDefNode, AssignNode, FuncCallNode, CodeBlockNode, IfNode, WordNode, whileNode
from .tostring_visitor import ToStringVisitor


def parse_op(symbol: str, left: Node, right: Node):
    assert symbol in ["+", "-", "*", "/", "<", ">", "==",
                      "!=", "<=", ">=", "&&", "||"], f"unknown symbol {symbol}"
    return TwoSideOpNode(symbol, left, right)
   # raise Exception("unknown symbol")


def twoside_op_capture(x: Dict[str, Node]) -> Node:
    if "right" in x:
        symbol = x["symbol"]
        assert isinstance(symbol, SymbolNode)
        return parse_op(symbol.symbol, x["left"], x["right"])
    else:
        return x["left"]


def unary_op_capture(x: Dict[str, Node]) -> Node:
    sign = x["sign"]
    assert isinstance(sign, SymbolNode)
    return UnaryOpNode(sign.symbol, x["node"])


NodeT = TypeVar("NodeT")


def extract_multiple(x: Dict[str, Node], key: str) -> List[Node]:
    i = 0
    items = []
    while f"{key}{i}" in x:
        items.append(x[f"{key}{i}"])
        i += 1

    return items


def block_capture(x: Dict[str, Node]) -> CodeBlockNode:
    statements = extract_multiple(x, "statement")
    return CodeBlockNode(statements)


def if_capture(x: Dict[str, Node]) -> IfNode:
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
    nameNode = x["name"]
    assert isinstance(nameNode, WordNode)
    return VarNode(nameNode.word)


def var_def_capture(x: Dict[str, Node]) -> Node:
    nameNode = x["name"]
    assert isinstance(nameNode, WordNode)
    if "value" in x:
        valueNode = x["value"]
        return VarDefNode(nameNode.word, valueNode)
    return VarDefNode(nameNode.word)


def assign_capture(x: Dict[str, Node]) -> Node:
    lhandNode = x["lhand"]
    assert isinstance(lhandNode, Node)
    if "rhand" in x:
        rhandNode = x["rhand"]
        assert isinstance(lhandNode, VarNode)
        return AssignNode(lhandNode, rhandNode)
    return lhandNode


def func_call_capture(x: Dict[str, Node]) -> Node:
    varNode = x["var"]
    assert isinstance(varNode, VarNode)
    args = extract_multiple(x, "arg")
    return FuncCallNode(varNode, args)


def while_capture(x: Dict[str, Node]) -> Node:
    condition = x["condition"]
    then_block = x["body"]
    assert isinstance(then_block, CodeBlockNode)
    return whileNode(condition, then_block)


def func_arg_capture(x: Dict[str, Node]) -> Node:
    nameNode = x["name"]
    assert isinstance(nameNode, WordNode)
    return FuncArgNode(nameNode.word)


def func_def_capture(x: Dict[str, Node]) -> Node:
    nameNode = x["name"]
    assert isinstance(nameNode, WordNode)
    args = extract_multiple(x, "arg")
    for arg in args:
        assert isinstance(arg, FuncArgNode)
    body = x["body"]
    assert isinstance(body, CodeBlockNode)
    return FunctionDefNode(nameNode.word, body, cast(List[FuncArgNode], args))


def file_capture(x: Dict[str, Node]) -> Node:
    functions = extract_multiple(x, "function")
    for func in functions:
        assert isinstance(func, FunctionDefNode)
    return CodeFileNode(cast(List[FunctionDefNode], functions))


def return_capture(x: Dict[str, Node]) -> Node:
    if "value" in x:
        return ReturnNode(x["value"])
    return ReturnNode()


def get_grammar():
    PLUS = SymbolParser("+", SymbolNode)
    MINUS = SymbolParser("-", SymbolNode)
    MULT = SymbolParser("*", SymbolNode)
    DIV = SymbolParser("/", SymbolNode)
    EQ = SymbolParser("==", SymbolNode)
    NEQ = SymbolParser("!=", SymbolNode)
    LEQ = SymbolParser("<=", SymbolNode)
    GEQ = SymbolParser(">=", SymbolNode)
    LT = SymbolParser("<", SymbolNode)
    GT = SymbolParser(">", SymbolNode)
    NOT = SymbolParser("!", SymbolNode)

    AND = SymbolParser("&&", SymbolNode)
    OR = SymbolParser("||", SymbolNode)

    semicolon = Symbol(";")

    anyWord = AnyWord(WordNode)
    anyNumber = AnyNumber(NumberNode)
    anyString = AnyString(StringNode)

    plusminus = Capture(func=twoside_op_capture)
    dotdiv = Capture(func=twoside_op_capture)
    comparison = Capture(func=twoside_op_capture)
    logical_op = Capture(func=twoside_op_capture)

    IF = Word("if")
    ELSE = Word("else")
    WHILE = Word("while")
    LET = Word("let")

    expression = logical_op
    var_def: Capture[Node] = Capture(Sequence([
        LET,
        Labeled(anyWord, "name"),
        Maybe(Sequence([
            Symbol("="),
            Labeled(expression, "value")
        ]))
    ]), func=var_def_capture)
    var = Capture(Labeled(anyWord, "name"), func=var_capture)
    assignment = Capture(Sequence([
        Labeled(expression, "lhand"),
        Maybe(Sequence([
            Symbol("="),
            Labeled(expression, "rhand")
        ]))
    ]), func=assign_capture)

    func_call: Capture[Node] = Capture(Sequence([
        Labeled(var, "var"),
        Symbol("("),
        Multiple(
            Sequence([
            Labeled(expression, "arg{#id}"),
            Maybe(
                Symbol(",") # fix this 
            )])
        ),
        Symbol(")")
    ]), func=func_call_capture)

    return_ = Capture(Sequence([
        Word("return"),
        Maybe(Labeled(expression, "value"))
    ]), func=return_capture)

    statement = return_ | var_def | func_call | assignment

    block = Capture(func=block_capture)
    if_statement = Capture(func=if_capture)
    while_loop = Capture(func=while_capture)
    function_def = Capture(func=func_def_capture)
    block.set(Sequence([
        Symbol("{"),
        Multiple(
            Labeled(if_statement, "statement{#id}")
            | Labeled(while_loop, "statement{#id}")
            | Sequence([
                Labeled(statement, "statement{#id}"),
                semicolon
            ])),
        Symbol("}")
    ]))

    if_statement.set(Sequence([
        IF,
        Labeled(expression, "condition"),
        Labeled(block, "then_block"),
        Multiple(Sequence([
            ELSE,
            IF,
            Labeled(expression, "elif_cond{#id}"),
            Labeled(block, "elif_block{#id}"),
        ])),
        Maybe(Sequence([
            ELSE,
            Labeled(block, "else_block")
        ]))
    ]))
    while_loop.set(Sequence([
        WHILE,
        Labeled(expression, "condition"),
        Labeled(block, "body")
    ]))
    func_arg = Capture(Sequence([
        Labeled(anyWord, "name"),
    ]), func=func_arg_capture)

    function_def.set(Sequence([
        Word("def"),
        Labeled(anyWord, "name"),
        Symbol("("),
        Multiple(Sequence([
            Labeled(func_arg, "arg{#id}"),
            Maybe(
                Symbol(",") # fix this 
            )]
        )),
        Symbol(")"),
        Labeled(block, "body")
    ]))

    file = Capture(func=file_capture)
    file.set(Multiple(Labeled(function_def, "function{#id}")))

    paren: Capture[Node] = Capture(Sequence([
        Symbol("("),
        Labeled(expression, "x"),
        Symbol(")")
    ]), func=lambda x: x["x"])
    unary_op = Capture(func=unary_op_capture)
    primary = func_call | var | anyNumber | anyString | paren | unary_op

    unary_op.set(Sequence([
        Labeled(NOT | MINUS, "sign"),
        Labeled(primary, "node")
    ]))

    dotdiv.set(Sequence([
        Labeled(primary, "left"),
        Maybe(
            Sequence([
                Labeled(MULT | DIV, "symbol"),
                Labeled(dotdiv, "right")
            ])
        )
    ]))

    plusminus.set(Sequence([
        Labeled(dotdiv, "left"),
        Maybe(Sequence([
            Labeled(PLUS | MINUS, "symbol"),
            Labeled(plusminus, "right")
        ])
        )
    ]))

    comparison.set(Sequence([
        Labeled(plusminus, "left"),
        Maybe(Sequence([
            Labeled(EQ | NEQ | LEQ | GEQ | LT | GT, "symbol"),
            Labeled(plusminus, "right")
        ]))
    ]))
    logical_op.set(Sequence([
        Labeled(comparison, "left"),
        Maybe(Sequence([
            Labeled(AND | OR, "symbol"),
            Labeled(logical_op, "right")
        ]))
    ]))

    return file


def parse(code: str) -> Node:
    tokens = lex(code, symbol_chars="+-*/(){};=<>!&|,",
                 multi_symbols=["==", "<=", ">=", "!=", "&&", "||"])
    stream = TokenStream(tokens)
    grammar = get_grammar()
    return grammar.parse(stream)


if __name__ == "__main__":
    # print(parse("{var_a*(3+var_b+c*2);}"))
    if True:
        parse("{print('test');}")
        text = """
        def test()
        {
            let a = 1;
            let result = "";
            if a == 1 {
                result = result + "a";
            } else if a == 2 {
                result = result + "b";
            } else if a == 3 {
                result = result + "c";
            }
            else{
                result = result + "d";
            }
            result = result + "e";
            print("got result: " + result);
            let i = 0;
            while i < 10 {
                print("i is " + i);
                i = i + 1;
            }
        }
        """
        parsed = parse(text)

        # text = parsed.accept(ToStringVisitor())
        # print(text)
        print(parsed)
        # print("result: ")
        # evaluate
        from .evaluate import evaluate
        evaluate(text, "test")
        # parsed.accept(EvalVisitor(entry_function="test"))
