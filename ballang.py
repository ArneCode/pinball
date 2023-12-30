from abc import ABC
from typing import Dict, List, Optional, TypeVar, cast

from grammar import AnyNumber, AnyWord, Capture, Labeled, Maybe, MultiWord, Multiple, Sequence, Symbol, SymbolParser, Word
from lexer import TokenStream, lex
from node import Node, PlusNode, MinusNode, TimesNode, DivNode, NumberNode, SymbolNode, EqNode, LessOrEqNode, GreaterOrEqNode, NeqNode, VarNode, VarDefNode, AssignNode, FuncCallNode, CodeBlockNode, IfNode, WordNode





def parse_op(symbol: str, left: Node, right: Node):
    if symbol == "+":
        return PlusNode(left, right)
    if symbol == "-":
        return MinusNode(left, right)
    if symbol == "*":
        return TimesNode(left, right)
    if symbol == "/":
        return DivNode(left, right)
    if symbol == "==":
        return EqNode(left, right)
    if symbol == "<=":
        return LessOrEqNode(left, right)
    if symbol == ">=":
        return GreaterOrEqNode(left, right)
    if symbol == "!=":
        return NeqNode(left, right)
    raise Exception("unknown symbol")


def op_capture(x: Dict[str, Node]) -> Node:
    if "right" in x:
        symbol = x["symbol"]
        assert isinstance(symbol, SymbolNode)
        return parse_op(symbol.symbol, x["left"], x["right"])
    else:
        return x["left"]


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
    if "arg" in x:
        argNode = x["arg"]
        return FuncCallNode(varNode, argNode)
    return varNode


def get_grammar():
    PLUS = SymbolParser("+", SymbolNode)
    MINUS = SymbolParser("-", SymbolNode)
    MULT = SymbolParser("*", SymbolNode)
    DIV = SymbolParser("/", SymbolNode)
    EQ = SymbolParser("==", SymbolNode)
    NEQ = SymbolParser("!=", SymbolNode)
    LEQ = SymbolParser("<=", SymbolNode)
    GEQ = SymbolParser(">=", SymbolNode)

    semicolon = Symbol(";")

    anyWord = AnyWord(WordNode)
    anyNumber = AnyNumber(NumberNode)

    plusminus = Capture(func=op_capture)
    dotdiv = Capture(func=op_capture)
    comparison = Capture(func=op_capture)

    IF = Word("if")
    ELSE = Word("else")
    ELSE_IF = MultiWord([ELSE, IF])
    LET = Word("let")

    expression = comparison
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

    var_or_func_call: Capture[Node] = Capture(Sequence([
        Labeled(var, "var"),
        Maybe(
            Sequence([
                Symbol("("),
                Labeled(expression, "arg"),
                Symbol(")")
            ])
        )
    ]), func=func_call_capture)

    statement = var_def | var_or_func_call |  assignment

    block = Capture(func=block_capture)
    if_statement = Capture(func=if_capture)
    block.set(Sequence([
        Symbol("{"),
        Multiple(
            Labeled(if_statement, "statement{#id}")
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
            ELSE_IF,
            Labeled(expression, "elif_cond{#id}"),
            Labeled(block, "elif_block{#id}"),
        ])),
        Maybe(Sequence([
            ELSE,
            Labeled(block, "else_block")
        ]))
    ]))

    paren: Capture[Node] = Capture(Sequence([
        Symbol("("),
        Labeled(plusminus, "x"),
        Symbol(")")
    ]), func=lambda x: x["x"])

    primary = var | anyNumber | paren

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
            Labeled(EQ | NEQ | LEQ | GEQ, "symbol"),
            Labeled(plusminus, "right")
        ]))
    ]))

    return block


def parse(code: str) -> Node:
    tokens = lex(code, symbol_chars="+-*/(){};=",
                 multi_symbols=["==", "<=", ">="])
    stream = TokenStream(tokens)
    grammar = get_grammar()
    return grammar.parse(stream)


if __name__ == "__main__":
    #print(parse("{var_a*(3+var_b+c*2);}"))
    if True:
        print(parse("""
        {
                    let a = 1;
                    if a == 1 {
                        print(a);
                    }
        }
        """))
