"""
Defines the grammar for the Ballang language and provides a function to parse a string of Ballang code into a syntax tree.

The grammar is defined using the `grammar` module, which provides a way to define a context-free grammars.
"""

from abc import ABC
from typing import Dict, List, Optional, TypeVar, cast

from .abstract.grammar import AnyNumber, AnyString, AnyWord, Capture, Labeled, Maybe, Multiple, Sequence, Symbol, SymbolParser, Word
from .abstract.lexer import TokenStream, lex
from .node import CodeFileNode, FuncArgNode, FunctionDefNode, Node, NumberNode, ReturnNode, StringNode, SymbolNode, TwoSideOpNode, UnaryOpNode,  VarNode, VarDefNode, AssignNode, FuncCallNode, CodeBlockNode, IfNode, WordNode, whileNode
from .tostring_visitor import ToStringVisitor
from .capture import *



def get_grammar():
    """
    Get the grammar for the Ballang language

    Returns:
        Grammar: the grammar

    ### The grammar looks like this:
        
    file -> function*

    function -> "def" ANY_WORD "(" func_arg* ")" block

    func_arg -> ANY_WORD

    block -> "{" (if_statement | while_loop | statement)* "}"

    if_statement -> "if" expression block ("else" "if" expression block)* ("else" block)?

    while_loop -> "while" expression block

    statement -> return | var_def | func_call | assignment

    return -> "return" expression?

    var_def -> "let" ANY_WORD ("=" expression)?

    var -> ANY_WORD

    assignment -> expression ("=" expression)?

    func_call -> var "(" expression* ")"

    expression -> logical_op

    logical_op -> comparison ("&&" | "||" logical_op)?

    comparison -> plusminus ("==" | "!=" | "<=" | ">=" | "<" | ">" comparison)?

    plusminus -> dotdiv ("+" | "-" plusminus)?

    dotdiv -> unary_op ("*" | "/" dotdiv)?

    unary_op -> ("!" | "-") primary

    primary -> func_call | var | anyNumber | anyString | "(" expression ")"
    """
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
    """
    Parse a string of Ballang code into a syntax tree

    Args:
        code (str): the code to parse

    Returns:
        Node: the syntax tree
    """
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
