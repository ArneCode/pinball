from __future__ import annotations
import copy
from types import UnionType
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from abc import ABC, abstractmethod

from lexer import TokenStream, lex, TokenType


NodeT = TypeVar("NodeT")

class Grammar(ABC):
    @abstractmethod
    def check(self, tokens: TokenStream) -> bool:
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

class SingleTokenGrammar(Grammar):
    pass

class Capture(Parser, Generic[NodeT]):
    item: Optional[Matcher]
    func: Optional[Callable[[Dict[str, NodeT]], NodeT]]

    def __init__(self, item: Optional[Matcher] = None, func: Optional[Callable[[Dict[str, NodeT]], NodeT]] = None):
        self.item = item
        self.func = func

    def set(self, item: Matcher):
        self.item = item


    def check(self, tokens: TokenStream) -> bool:
        if self.item is None:
            raise Exception(
                f"Capture must have an item")
        return self.item.check(tokens)

    def parse(self, tokens: TokenStream) -> NodeT:
        assert self.item is not None
        matched_dict = self.item.match(tokens, {})
        assert self.func is not None
        result = self.func(matched_dict)
        return result


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
        raise Exception("parse error")
    
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
        raise Exception("match error")

class Sequence(Matcher):
    items: List[Matcher]

    def __init__(self, items: List[Matcher] = []):
        self.items = items

    def set(self, items: List[Matcher]):
        self.items = items

    def check(self, tokens: TokenStream) -> bool:
        # checking in later items in advance is not possible, because 
        # it is unknown how many tokens will be consumed by the first items
        return self.items[0].check(tokens)

    def match(self, tokens: TokenStream, dict: Dict) -> Dict:
        assert isinstance(dict, Dict)

        for item in self.items:

            if not item.check(tokens):
                raise Exception(
                    f"match error, expected {item}, got {tokens.peek()}")
            dict = item.match(tokens, dict)
            assert isinstance(dict, Dict)

        return dict


class Maybe(Matcher):
    item: Matcher

    def __init__(self, item) -> None:
        self.item = item

    def __str__(self):
        return f"Maybe({self.item})"

    def check(self, tokens: TokenStream) -> bool:
        return True

    def match(self, tokens: TokenStream, dict: Dict) -> dict:
        assert isinstance(dict, Dict)

        if self.item.check(tokens):
            return self.item.match(tokens, dict)
        return dict

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
        assert isinstance(dict, Dict)
        i = 0
        while self.item.check(tokens): 
            new_dict = self.item.match(tokens, {})
            for key in new_dict:
                if self.pattern in key:
                    new_key = key.replace(self.pattern, str(i))
                    #new_dict[new_key] = new_dict[key]
                    #del new_dict[key]
                    dict[new_key] = new_dict[key]
            #dict.update(new_dict)
            assert isinstance(dict, Dict)
            i += 1
        return dict

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
        assert isinstance(dict, Dict)
        node = self.item.parse(tokens)
        print(f"dict: {dict}, conte, label: {self.label}, node: {node}")
        dict[self.label] = node
        return dict


class AnyWord(Parser, SingleTokenGrammar, Generic[NodeT]):
    nodeConstructor: Callable[[str], NodeT]

    def __init__(self, nodeConstructor: Callable[[str], NodeT]):
        self.nodeConstructor = nodeConstructor

    def check(self, tokens: TokenStream) -> bool:
        next = tokens.peek()
        if next is None:
            return False
        return next.type == TokenType.WORD
        #return (not tokens.is_eof()) and tokens.peek().type == TokenType.WORD

    def parse(self, tokens: TokenStream) -> NodeT:
        assert self.nodeConstructor is not None
        next = tokens.next()
        assert next is not None
        return self.nodeConstructor(next.value)


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
            raise Exception("expected symbol")
        return self.nodeConstructor(next.value)

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

        print(f"consuming symbol, {self.symbol}")
        next = tokens.next()
        assert next is not None
        if next.value != self.symbol:
            raise Exception("expected symbol")
        return dict

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
            raise Exception("expected word")
        assert self.nodeConstructor is not None
        return self.nodeConstructor(next.value)
    
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

        print(f"consuming word, {self.word}")
        next = tokens.next()
        assert next is not None
        if next.value != self.word:
            raise Exception("expected word")
        return dict
    
class MultiWord(Matcher):
    words: List[Word]

    def __init__(self, words: List[Word]):
        self.words = words

    def __str__(self) -> str:
        return " ".join(map(str, self.words))
    
    def check(self, tokens: TokenStream) -> bool:
        tokens_copy = copy.copy(tokens)
        for word in self.words:
            if not word.check(tokens):
                return False
            tokens_copy.next()
        return True
    
    def match(self, tokens: TokenStream, dict: Dict) -> Dict:
        assert isinstance(dict, Dict)

        for word in self.words:
            dict = word.match(tokens, dict)
        return dict

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
    #primary: Capture[Node] = Capture(AnyWord(WordNode) | AnyNumber(
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
