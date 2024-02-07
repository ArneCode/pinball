from __future__ import annotations
import copy
from types import UnionType
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from abc import ABC, abstractmethod

from .lexer import CodeSlice, TokenStream, lex, TokenType


NodeT = TypeVar("NodeT")


class Grammar(ABC):
    @abstractmethod
    def check(self, tokens: TokenStream) -> bool:
        pass

    @abstractmethod
    def is_single_token(self) -> bool:
        pass


class Matcher(Grammar, Generic[NodeT]):
    @abstractmethod
    def match(self, tokens: TokenStream, dict: Dict[str, NodeT]) -> Dict[str, NodeT]:
        pass

    def __or__(self, other: Matcher) -> OneOfMatcher[NodeT]:
        return OneOfMatcher([self, other])


class Parser(Grammar, Generic[NodeT]):
    @abstractmethod
    def parse(self, tokens: TokenStream) -> NodeT:
        pass

    def __or__(self, other: Parser) -> OneOfParser[NodeT]:
        return OneOfParser([self, other])

class ParserError(Exception):
    slice: Optional[CodeSlice]
    
    def __init__(self, message: str, slice: Optional[CodeSlice]= None):
        if slice is None:
            super().__init__(f"Parser error: {message}")
        else:
            super().__init__(f"Parser error at {slice.start}: {message}, \n {slice.highlight()}")
        self.slice = slice

class Capture(Parser, Generic[NodeT]):
    item: Optional[Matcher]
    func: Optional[Callable[[Dict[str, NodeT]], NodeT]]

    def __init__(self, item: Optional[Matcher] = None, func: Optional[Callable[[Dict[str, NodeT]], NodeT]] = None):
        self.item = item
        self.func = func

    def set(self, item: Matcher):
        self.item = item

    def check(self, tokens: TokenStream) -> bool:
        assert self.item is not None
        return self.item.check(tokens)

    def parse(self, tokens: TokenStream) -> NodeT:
        assert self.item is not None
        matched_dict = self.item.match(tokens, {})
        assert self.func is not None
        result = self.func(matched_dict)
        return result

    def is_single_token(self) -> bool:
        assert self.item is not None
        return self.item.is_single_token()

    def __str__(self) -> str:
        return f"Capture({self.item})"


class OneOfParser(Parser, Generic[NodeT]):
    choices: List[Parser]

    def __init__(self, choices: List[Parser] = []):
        self.choices = choices

    def set(self, choices: List[Parser]):
        self.choices = choices

    def check(self, tokens: TokenStream) -> bool:
        if tokens.is_eof():
            return False
        for choice in self.choices:
            if choice.check(tokens):
                return True
        return False

    def parse(self, tokens: TokenStream) -> NodeT:
        for choice in self.choices:
            if choice.check(tokens):
                return choice.parse(tokens)
        next_token = tokens.peek()
        if tokens.is_eof():
            raise ParserError("unexpected end of file")
        assert next_token is not None
        raise ParserError(f"unexpected token {next_token.value}", next_token.slice)

    def is_single_token(self) -> bool:
        for choice in self.choices:
            if not choice.is_single_token():
                return False
        return True


class OneOfMatcher(Matcher, Generic[NodeT]):
    choices: List[Matcher]

    def __init__(self, choices: List[Matcher] = []):
        self.choices = choices

    def set(self, choices: List[Matcher]):
        self.choices = choices

    def check(self, tokens: TokenStream) -> bool:
        if tokens.is_eof():
            return False
        for choice in self.choices:
            if choice.check(tokens):
                return True
        return False

    def match(self, tokens: TokenStream, dict: Dict) -> Dict:
        assert isinstance(dict, Dict)

        for choice in self.choices:
            if choice.check(tokens):
                return choice.match(tokens, dict)
        next_token = tokens.peek()
        if tokens.is_eof():
            raise ParserError("unexpected end of file")
        assert next_token is not None
        raise ParserError(f"unexpected token {next_token.value}", next_token.slice)

    def is_single_token(self) -> bool:
        for choice in self.choices:
            if not choice.is_single_token():
                return False
        return True


class Sequence(Matcher):
    items: List[Matcher]

    def __init__(self, items: List[Matcher] = []):
        self.items = items

    def set(self, items: List[Matcher]):
        self.items = items

    def check(self, tokens: TokenStream) -> bool:
        # checking in later items in advance is only possible for fixed sized grammars, because
        # otherwise it is unknown how many tokens will be consumed by the first items

        tokens_copy = copy.copy(tokens)
        i = 0
        for item in self.items:
            if not item.check(tokens_copy):
                return False
            if not item.is_single_token():
                break
            tokens_copy.next()
            i += 1
        return True

    def match(self, tokens: TokenStream, dict: Dict) -> Dict:
        assert isinstance(dict, Dict)
        for item in self.items:
            if not item.check(tokens):
                next = tokens.peek()
                if next is None:
                    raise ParserError("unexpected end of file")
                raise ParserError(f"unexpected token {next.value}", next.slice)
            dict = item.match(tokens, dict)
            assert isinstance(dict, Dict)

        return dict

    def is_single_token(self) -> bool:
        return False


class Maybe(Matcher):
    item: Matcher

    def __init__(self, item) -> None:
        self.item = item

    def __str__(self):
        return f"Maybe({self.item})"

    def check(self, tokens: TokenStream) -> bool:
        return True

    def match(self, tokens: TokenStream, dict: Dict) -> dict:

        if self.item.check(tokens):
            return self.item.match(tokens, dict)
        return dict

    def is_single_token(self) -> bool:
        return False


class Multiple(Matcher):
    item: Matcher
    pattern: str

    def __init__(self, item, pattern: str = "{#id}") -> None:
        self.item = item
        self.pattern = pattern

    def __str__(self):
        return f"OneOrMore({self.item})"

    def check(self, tokens: TokenStream) -> bool:
        return True

    def match(self, tokens: TokenStream, dict: Dict) -> dict:
        i = 0
        while self.item.check(tokens):
            new_dict = self.item.match(tokens, {})
            for key in new_dict:
                if self.pattern in key:
                    new_key = key.replace(self.pattern, str(i))
                    dict[new_key] = new_dict[key]
            i += 1
        return dict

    def is_single_token(self) -> bool:
        return False


class Labeled(Matcher):
    label: str
    item: Parser

    def __init__(self, item: Parser, label: str) -> None:
        self.label = label
        self.item = item

    def __str__(self):
        return f"Labeled({self.label}, {self.item})"

    def check(self, tokens: TokenStream) -> bool:
        return self.item.check(tokens)

    def match(self, tokens: TokenStream, dict: Dict) -> dict:
        node = self.item.parse(tokens)
        dict[self.label] = node
        return dict

    def is_single_token(self) -> bool:
        return self.item.is_single_token()


class AnyWord(Parser, Generic[NodeT]):
    nodeConstructor: Callable[[str], NodeT]

    def __init__(self, nodeConstructor: Callable[[str], NodeT]):
        self.nodeConstructor = nodeConstructor

    def check(self, tokens: TokenStream) -> bool:
        next = tokens.peek()
        if next is None:
            return False
        return next.type == TokenType.WORD
        # return (not tokens.is_eof()) and tokens.peek().type == TokenType.WORD

    def parse(self, tokens: TokenStream) -> NodeT:
        assert self.nodeConstructor is not None
        next = tokens.next()
        assert next is not None
        return self.nodeConstructor(next.value)

    def is_single_token(self) -> bool:
        return True


class AnyNumber(Parser, Generic[NodeT]):
    nodeConstructor: Callable[[float], NodeT]

    def __init__(self, nodeConstructor: Callable[[float], NodeT]):
        self.nodeConstructor = nodeConstructor

    def check(self, tokens: TokenStream) -> bool:
        next = tokens.peek()
        if next is None:
            return False
        return next.type == TokenType.NUMBER

    def parse(self, tokens: TokenStream) -> NodeT:
        assert self.nodeConstructor is not None
        next = tokens.next()
        assert next is not None
        return self.nodeConstructor(float(next.value))

    def is_single_token(self) -> bool:
        return True


class AnyString(Parser, Generic[NodeT]):
    nodeConstructor: Callable[[str], NodeT]

    def __init__(self, nodeConstructor: Callable[[str], NodeT]):
        self.nodeConstructor = nodeConstructor

    def check(self, tokens: TokenStream) -> bool:
        next = tokens.peek()
        if next is None:
            return False
        return next.type == TokenType.STRING

    def parse(self, tokens: TokenStream) -> NodeT:
        assert self.nodeConstructor is not None
        next = tokens.next()
        assert next is not None
        return self.nodeConstructor(next.value)

    def is_single_token(self) -> bool:
        return True


class SymbolParser(Parser, Generic[NodeT]):
    symbol: str
    nodeConstructor: Callable[[str], NodeT]

    def __init__(self, symbol: str, nodeConstructor: Callable[[str], NodeT]):
        self.symbol = symbol
        self.nodeConstructor = nodeConstructor

    def __str__(self) -> str:
        return self.symbol

    def check(self, tokens: TokenStream) -> bool:
        next = tokens.peek()
        if next is None:
            return False
        return next.value == self.symbol

    def parse(self, tokens: TokenStream) -> NodeT:
        next = tokens.next()
        
        assert next is not None
        if next.value != self.symbol:
            raise ParserError(f"expected symbol {self.symbol}, got {next.value}", next.slice)
        return self.nodeConstructor(next.value)

    def is_single_token(self) -> bool:
        return True


class Symbol(Matcher):
    symbol: str

    def __init__(self, symbol: str):
        self.symbol = symbol

    def __str__(self) -> str:
        return self.symbol

    def check(self, tokens: TokenStream) -> bool:
        next = tokens.peek()
        if next is None:
            return False
        return next.value == self.symbol

    def match(self, tokens: TokenStream, dict: Dict) -> Dict:
        assert isinstance(dict, Dict)

        next = tokens.next()
        assert next is not None
        if next.value != self.symbol:
            raise ParserError(f"expected symbol {self.symbol}, got {next.value}", next.slice)
        return dict

    def is_single_token(self) -> bool:
        return True


class WordParser(Parser, Generic[NodeT]):
    word: str
    nodeConstructor: Optional[Callable[[str], NodeT]]

    def __init__(self, word: str, nodeConstructor: Optional[Callable[[str], NodeT]] = None):
        self.word = word
        self.nodeConstructor = nodeConstructor

    def __str__(self) -> str:
        return self.word

    def check(self, tokens: TokenStream) -> bool:
        next = tokens.peek()
        if next is None:
            return False
        return next.value == self.word

    def parse(self, tokens: TokenStream) -> NodeT:
        next = tokens.next()
        assert next is not None
        if next.value != self.word:
            raise ParserError(f"expected word {self.word}, got {next.value}", next.slice)
        assert self.nodeConstructor is not None
        return self.nodeConstructor(next.value)

    def is_single_token(self) -> bool:
        return True


class Word(Matcher):
    word: str

    def __init__(self, word: str):
        self.word = word

    def __str__(self) -> str:
        return self.word

    def check(self, tokens: TokenStream) -> bool:
        next = tokens.peek()
        if next is None:
            return False
        return next.value == self.word

    def match(self, tokens: TokenStream, dict: Dict) -> Dict:
        assert isinstance(dict, Dict)

        next = tokens.next()
        assert next is not None
        if next.value != self.word:
            raise ParserError(f"expected word {self.word}, got {next.value}", next.slice)
        return dict

    def is_single_token(self) -> bool:
        return True



if __name__ == "__main__":
    """
    plusminus -> dotdiv ( "+" plusminus | "-" plusminus )?
    dotdiv -> primary ( "*" dotdiv | "/" dotdiv )?
    primary -> Word | Number

    """
    class Node(ABC):
        pass

    class PlusNode(Node):
        left: Node
        right: Node

        def __init__(self, left: Node, right: Node):
            self.left = left
            self.right = right

        def __str__(self) -> str:
            return f"({self.right} + {self.left})"

    class MinusNode(Node):
        left: Node
        right: Node

        def __init__(self, left: Node, right: Node):
            self.left = left
            self.right = right

        def __str__(self) -> str:
            return f"({self.left} - {self.right})"

    class TimesNode(Node):
        left: Node
        right: Node

        def __init__(self, left: Node, right: Node):
            self.left = left
            self.right = right

        def __str__(self) -> str:
            return f"({self.left} * {self.right})"

    class DivNode(Node):
        left: Node
        right: Node

        def __init__(self, left: Node, right: Node):
            self.left = left
            self.right = right

        def __str__(self) -> str:
            return f"({self.left} / {self.right})"

    class NumberNode(Node):
        value: float

        def __init__(self, value: float):
            self.value = value

        def __str__(self) -> str:
            return str(self.value)

    class WordNode(Node):
        word: str

        def __init__(self, word: str):
            self.word = word

        def __str__(self) -> str:
            return self.word

    class SymbolNode(Node):
        symbol: str

        def __init__(self, symbol: str):
            self.symbol = symbol

        def __str__(self) -> str:
            return self.symbol

    def parse_op(symbol: str, left: Node, right: Node):
        if symbol == "+":
            return PlusNode(left, right)
        if symbol == "-":
            return MinusNode(left, right)
        if symbol == "*":
            return TimesNode(left, right)
        if symbol == "/":
            return DivNode(left, right)
        raise Exception("unknown symbol")

    def op_capture(x: Dict[str, Node]) -> Node:
        if "right" in x:
            symbol = x["symbol"]
            assert isinstance(symbol, SymbolNode)
            return parse_op(symbol.symbol, x["left"], x["right"])
        else:
            return x["left"]
    plusminus = Capture(func=op_capture)
    paren: Capture[Node] = Capture(Sequence([
        Symbol("("),
        Labeled(plusminus, "x"),
        Symbol(")")
    ]), func=lambda x: x["x"])
    anyWord = AnyWord(WordNode)
    anyNumber = AnyNumber(NumberNode)

    primary = anyWord | anyNumber | paren
    # primary: Capture[Node] = Capture(AnyWord(WordNode) | AnyNumber(
    #    NumberNode) | Labeled(paren, "x"), func=lambda x: x["x"])

    mult = SymbolParser("*", SymbolNode)
    div = SymbolParser("/", SymbolNode)

    dotdiv = Capture(func=op_capture)
    dotdiv.set(Sequence([
        Labeled(primary, "left"),
        Maybe(
            Sequence([
                Labeled(mult | div, "symbol"),
                Labeled(dotdiv, "right")
            ])
        )
    ]))

    plus = SymbolParser("+", SymbolNode)
    minus = SymbolParser("-", SymbolNode)

    plusminus.set(Sequence([
        Labeled(dotdiv, "left"),
        Maybe(Sequence([
            Labeled(plus | minus, "symbol"),
            Labeled(plusminus, "right")
        ])
        )
    ]))

    tokens = lex("var_a*(3+var_b)", symbol_chars="+-*/()")
    print(f"tokens: {tokens}")
    print(plusminus.parse(TokenStream(tokens)))
