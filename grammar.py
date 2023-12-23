from __future__ import annotations
from types import UnionType
from typing import Any, List
from abc import ABC, abstractmethod

from lexer import TokenStream, lex, TokenType


class Grammar(ABC):
    @abstractmethod
    def check(self, tokens: TokenStream) -> bool:
        pass

    @abstractmethod
    def parse(self, tokens: TokenStream) -> str:
        pass

    def __or__(self, __value: Any) -> Grammar:
        return OneOf([self, __value])


class OneOf(Grammar):
    choices: List[Grammar]
    name: str

    def __init__(self, choices: List[Grammar] = [], name: str = ""):
        self.choices = choices
        self.name = name

    def __str__(self) -> str:
        # return own name and names of all choices
        return f"{self.name}({'|'.join([choice.name for choice in self.choices])})"

    def set(self, choices: List[Grammar]):
        self.choices = choices

    def check(self, tokens: TokenStream) -> bool:
        if tokens.is_eof():
            return False
        print(f"checking oneof {self.name}: {tokens.peek()}")
        for choice in self.choices:
            if choice.check(tokens):
                print("return true")
                return True
        return False

    def parse(self, tokens: TokenStream) -> str:
        print(f"oneof parse {self.name}")
        i = 0
        for choice in self.choices:
            print(f"choice {i}: {choice}")
            if choice.check(tokens):
                print("accepted")
                return choice.parse(tokens)
            print("rejected")
            i += 1
        raise Exception("Parser error")


class Sequence(Grammar):
    items: List[Grammar]
    name: str

    def __init__(self, items: List[Grammar] = [], name: str = ""):
        self.items = items
        self.name = name

    def __str__(self) -> str:
        # return own name and names of all items
        return f"{self.name}({' '.join([item.name for item in self.items])})"

    def set(self, items: List[Grammar]):
        self.items = items

    def check(self, tokens: TokenStream) -> bool:
        print(f"sequence check: {self.name}")
        return self.items[0].check(tokens)

    def parse(self, tokens: TokenStream) -> str:
        result = ""
        for item in self.items:
            if not item.check(tokens):
                raise Exception(
                    f"Parse error, expected {item}, got {tokens.peek()}")
            result += item.parse(tokens)
        return f"({result})"


class Maybe(Grammar):
    name = "maybe"
    item: Grammar

    def __init__(self, item) -> None:
        self.item = item

    def __str__(self):
        return f"Maybe({self.item})"

    def check(self, tokens: TokenStream) -> bool:
        return True

    def parse(self, tokens: TokenStream) -> str:
        if self.item.check(tokens):
            return self.item.parse(tokens)
        return ""


class AnyWord(Grammar):
    name = "anyword"

    def check(self, tokens: TokenStream) -> bool:
        return (not tokens.is_eof()) and tokens.peek().type == TokenType.WORD

    def parse(self, tokens: TokenStream) -> str:
        return tokens.next().value


class AnyNumber(Grammar):
    name = "anynumber"

    def check(self, tokens: TokenStream) -> bool:
        return (not tokens.is_eof()) and tokens.peek().type == TokenType.NUMBER

    def parse(self, tokens: TokenStream) -> str:
        return tokens.next().value


class Word(Grammar):
    word: str

    def __init__(self, word: str):
        self.word = word


class Symbol(Grammar):
    symbol: str

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.name = symbol

    def __str__(self) -> str:
        return self.symbol

    def check(self, tokens: TokenStream) -> bool:
        if tokens.is_eof():
            return False
        return tokens.peek().value == self.symbol

    def parse(self, tokens: TokenStream) -> str:
        print(f"consuming symbol, {self.symbol}")
        result = tokens.next().value
        if result != self.symbol:
            raise Exception("expected symbol")
        return result


if __name__ == "__main__":
    """
    plusminus -> dotdiv ( "+" plusminus | "-" plusminus )?
    dotdiv -> primary ( "*" dotdiv | "/" dotdiv )?
    primary -> Word | Number

    """
    plusminus = Sequence(name="expr")
    primary = AnyWord() | AnyNumber() | Sequence([
        Symbol("("),
        plusminus,
        Symbol(")")
    ])

    dotdiv = Sequence(name="term")
    dotdiv.set([
        primary,
        Maybe(
            Sequence([Symbol("*"), dotdiv]) |
            Sequence([Symbol("/"), dotdiv])
        )
    ])

    plusminus.set([
        dotdiv,
        Maybe(OneOf([
            Sequence([Symbol("+"), plusminus]),
            Sequence([Symbol("-"), plusminus])
        ]))
    ])

    tokens = lex("var_a*(3+var_b)", symbols="+-*/()")
    print(f"tokens: {tokens}")
    print(plusminus.parse(TokenStream(tokens)))
