"""
Defines Classes which can be used to define an abstract grammar and parse a string into a syntax tree
"""
from __future__ import annotations
import copy
from types import UnionType
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from abc import ABC, abstractmethod

from .lexer import CodeSlice, TokenStream, lex, TokenType


NodeT = TypeVar("NodeT")


class Grammar(ABC):
    """
    Interface for a grammar
    
    A grammar is a set of rules for parsing a string into a syntax tree
    """
    @abstractmethod
    def check(self, tokens: TokenStream) -> bool:
        """
        Check if the grammar can parse the next tokens

        Args:
            tokens (TokenStream): the tokens to check

        Returns:
            bool: True if the grammar can parse the next tokens
        """
        pass

    @abstractmethod
    def is_single_token(self) -> bool:
        """
        Check if the grammar only consumes a single token. This is used in sequence grammars to check if the grammar can be checked in advance
        (see Sequence.check)

        Returns:
            bool: True if the grammar only consumes a single token
        """
        pass


class Matcher(Grammar, Generic[NodeT]):
    """
    A Matcher represents the static scaffolding of a grammar rule. It contains Labeled variable Sections, called Parsers.
    When matching it stores the values at the labeled sections in a dictionary.
    """
    @abstractmethod
    def match(self, tokens: TokenStream, dict: Dict[str, NodeT]) -> Dict[str, NodeT]:
        """
        Match the grammar and store the values at the labeled sections in the dictionary

        Args:
            tokens (TokenStream): the tokens to match
            dict (Dict[str, NodeT]): the dictionary to store the values at the labeled sections

        Returns:
            Dict[str, NodeT]: the dictionary with the values at the labeled sections
        """
        pass

    def __or__(self, other: Matcher) -> OneOfMatcher[NodeT]:
        return OneOfMatcher([self, other])


class Parser(Grammar, Generic[NodeT]):
    """
    A Parser Represents a dynamic grammar rule. It can parse a string into a syntax tree.
    Can be wrapped in a Labeled-class Object to use as a Matcher.
    """
    @abstractmethod
    def parse(self, tokens: TokenStream) -> NodeT:
        """
        Parse the grammar and return the syntax tree

        Args:
            tokens (TokenStream): the tokens to parse

        Returns:
            NodeT: the parsed syntax tree
        """
        pass

    def __or__(self, other: Parser) -> OneOfParser[NodeT]:
        """
        Overload the | operator to combine two parsers into a OneOfParser
        """
        return OneOfParser([self, other])

class ParserError(Exception):
    """
    Exception raised when a parser encounters an error

    Attributes:
        slice (Optional[CodeSlice]): the slice where the error occurred
    """
    slice: Optional[CodeSlice]
    
    def __init__(self, message: str, slice: Optional[CodeSlice]= None):
        """
        Constructor

        Args:
            message (str): the error message
            slice (Optional[CodeSlice], optional): the slice where the error occurred. Defaults to None.
        """
        if slice is None:
            super().__init__(f"Parser error: {message}")
        else:
            super().__init__(f"Parser error at {slice.start}: {message}, \n {slice.highlight()}")
        self.slice = slice

class Capture(Parser, Generic[NodeT]):
    """
    A Parser that Has a Matcher inside and a function to convert the matched dictionary into a syntax tree

    Attributes:
        item (Optional[Matcher]): the matcher
        func (Optional[Callable[[Dict[str, NodeT]], NodeT]]): the function to convert the matched dictionary into a syntax tree

    Args:
        item (Optional[Matcher], optional): the matcher. Defaults to None.
        func (Optional[Callable[[Dict[str, NodeT]], NodeT]], optional): the function to convert the matched dictionary into a syntax tree. Defaults to None.
    """
    item: Optional[Matcher]
    func: Optional[Callable[[Dict[str, NodeT]], NodeT]]

    def __init__(self, item: Optional[Matcher] = None, func: Optional[Callable[[Dict[str, NodeT]], NodeT]] = None):
        """
        Constructor

        Args:
            item (Optional[Matcher], optional): the matcher. Defaults to None.
            func (Optional[Callable[[Dict[str, NodeT]], NodeT]], optional): the function to convert the matched dictionary into a syntax tree. Defaults to None.
        """
        self.item = item
        self.func = func

    def set(self, item: Matcher):
        """
        Set the matcher, useful when the the capture is used inside of its own matcher
        In such a case the matcher is set after the constructor is called

        Args:
            item (Matcher): the matcher
        """
        self.item = item

    def check(self, tokens: TokenStream) -> bool:
        """
        Check if the grammar can parse the next tokens

        Args:
            tokens (TokenStream): the tokens to check

        Returns:
            bool: True if the grammar can parse the next tokens
        """
        assert self.item is not None
        return self.item.check(tokens)

    def parse(self, tokens: TokenStream) -> NodeT:
        """
        Parse the grammar and return the syntax tree

        Args:
            tokens (TokenStream): the tokens to parse

        Returns:
            NodeT: the parsed syntax tree
        """
        assert self.item is not None
        matched_dict = self.item.match(tokens, {})
        assert self.func is not None
        result = self.func(matched_dict)
        return result

    def is_single_token(self) -> bool:
        """
        Check if the grammar only consumes a single token. This is used in sequence grammars to check if the grammar can be checked in advance
        (see Sequence.check)

        Returns:
            bool: True if the grammar only consumes a single token
        """
        assert self.item is not None
        return self.item.is_single_token()

    def __str__(self) -> str:
        return f"Capture({self.item})"


class OneOfParser(Parser, Generic[NodeT]):
    """
    A Parser that represents a choice between multiple parsers. For example statement = return_ | var_def | func_call | assignment (Ballang)
    The | operator can be used to combine two parsers into a OneOfParser
    
    Attributes:
        choices (List[Parser]): the parsers to choose from

    Args:
        choices (List[Parser], optional): the parsers to choose from. Defaults to [].
    """
    choices: List[Parser]

    def __init__(self, choices: List[Parser] = []):
        """
        Constructor

        Args:
            choices (List[Parser], optional): the parsers to choose from. Defaults to [].
        """
        self.choices = choices

    def set(self, choices: List[Parser]):
        """
        Set the parsers, useful when the the capture is used inside of its own matcher
        In such a case the parsers are set after the constructor is called

        Args:
            choices (List[Parser]): the parsers to choose from
        """
        self.choices = choices

    def check(self, tokens: TokenStream) -> bool:
        """
        Check if the grammar can parse the next tokens

        Args:
            tokens (TokenStream): the tokens to check

        Returns:
            bool: True if the grammar can parse the next tokens
        """
        if tokens.is_eof():
            return False
        for choice in self.choices:
            if choice.check(tokens):
                return True
        return False

    def parse(self, tokens: TokenStream) -> NodeT:
        """
        Parse the grammar and return the syntax tree

        Args:
            tokens (TokenStream): the tokens to parse

        Returns:
            NodeT: the parsed syntax tree
        
        Raises:
            ParserError: if the grammar cannot parse the next tokens
        """
        for choice in self.choices:
            if choice.check(tokens):
                return choice.parse(tokens)
        next_token = tokens.peek()
        if tokens.is_eof():
            raise ParserError("unexpected end of file")
        assert next_token is not None
        raise ParserError(f"unexpected token {next_token.value}", next_token.slice)

    def is_single_token(self) -> bool:
        """
        Check if the grammar only consumes a single token. This is used in sequence grammars to check if the grammar can be checked in advance

        Returns:
            bool: True if the grammar only consumes a single token
        """
        for choice in self.choices:
            if not choice.is_single_token():
                return False
        return True


class OneOfMatcher(Matcher, Generic[NodeT]):
    """
    A Matcher that represents a choice between multiple matchers. The | operator can be used to combine two matchers into a OneOfMatcher

    Attributes:
        choices (List[Matcher]): the matchers to choose from
    """
    choices: List[Matcher]

    def __init__(self, choices: List[Matcher] = []):
        """
        Constructor

        Args:
            choices (List[Matcher], optional): the matchers to choose from. Defaults to [].
        """
        self.choices = choices

    def set(self, choices: List[Matcher]):
        """
        Set the matchers, useful when the the capture is used inside of its own matcher

        Args:
            choices (List[Matcher]): the matchers to choose from
        """
        self.choices = choices

    def check(self, tokens: TokenStream) -> bool:
        """
        Check if the grammar can parse the next tokens

        Args:
            tokens (TokenStream): the tokens to check

        Returns:
            bool: True if the grammar can parse the next tokens
        """
        if tokens.is_eof():
            return False
        for choice in self.choices:
            if choice.check(tokens):
                return True
        return False

    def match(self, tokens: TokenStream, dict: Dict) -> Dict:
        """
        Match the grammar and store the values at the labeled sections in the dictionary

        Args:
            tokens (TokenStream): the tokens to match
            dict (Dict[str, NodeT]): the dictionary to store the values at the labeled sections

        Returns:
            Dict[str, NodeT]: the dictionary with the values at the labeled sections

        Raises:
            ParserError: if the grammar cannot parse the next tokens
        """
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
        """
        Check if the grammar only consumes a single token. This is used in sequence grammars to check if the grammar can be checked in advance
        
        Returns:
            bool: True if the grammar only consumes a single token
        """
        for choice in self.choices:
            if not choice.is_single_token():
                return False
        return True


class Sequence(Matcher):
    """
    A Matcher that represents a sequence of matchers. The matchers are checked and matched in order

    Attributes:
        items (List[Matcher]): the matchers to check and match in order

    Args:
        items (List[Matcher], optional): the matchers to check and match in order. Defaults to [].
    """
    items: List[Matcher]

    def __init__(self, items: List[Matcher] = []):
        """
        Constructor

        Args:
            items (List[Matcher], optional): the matchers to check and match in order. Defaults to [].
        """
        self.items = items

    def set(self, items: List[Matcher]):
        """
        Set the matchers, useful when the the capture is used inside of its own matcher

        Args:
            items (List[Matcher]): the matchers to check and match in order
        """
        self.items = items

    def check(self, tokens: TokenStream) -> bool:
        """
        Check if the grammar can parse the next tokens. 
        If the first items are single token matchers, the grammar can be checked further than just the first token

        Args:
            tokens (TokenStream): the tokens to check

        Returns:
            bool: True if the grammar can parse the next tokens
        """
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
        """
        Match the grammar and store the values at the labeled sections in the dictionary

        Args:
            tokens (TokenStream): the tokens to match
            dict (Dict[str, NodeT]): the dictionary to store the values at the labeled sections

        Returns:
            Dict[str, NodeT]: the dictionary with the values at the labeled sections

        Raises:
            ParserError: if the grammar cannot parse the next tokens
        """
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
    """
    A Matcher that represents a Matcher that may or may not be present. If the Matcher is present it is checked and matched

    Attributes:
        item (Matcher): the matcher that may or may not be present
    """
    item: Matcher

    def __init__(self, item) -> None:
        """
        Constructor

        Args:
            item (Matcher): the matcher that may or may not be present
        """
        self.item = item

    def __str__(self):
        return f"Maybe({self.item})"

    def check(self, tokens: TokenStream) -> bool:
        """
        Check if the grammar can parse the next tokens. Is always true, because the grammar may or may not be present
        """
        return True

    def match(self, tokens: TokenStream, dict: Dict) -> dict:
        """
        Match the grammar and store the values at the labeled sections in the dictionary if the grammar is present

        Args:
            tokens (TokenStream): the tokens to match
            dict (Dict[str, NodeT]): the dictionary to store the values at the labeled sections

        Returns:
            Dict[str, NodeT]: the dictionary, maybe with the values at the labeled sections
        """

        if self.item.check(tokens):
            return self.item.match(tokens, dict)
        return dict

    def is_single_token(self) -> bool:
        return False


class Multiple(Matcher):
    """
    Used to represent a grammar that can be repeated multiple times. The grammar is checked and matched as long as it is present.
    For example there may be multiple statements in a block of code

    Attributes:
        item (Matcher): the matcher that may be repeated
    """
    item: Matcher
    pattern: str

    def __init__(self, item, pattern: str = "{#id}") -> None:
        """
        Constructor

        Args:
            item (Matcher): the matcher that may be repeated
        """
        self.item = item
        self.pattern = pattern

    def __str__(self):
        return f"OneOrMore({self.item})"

    def check(self, tokens: TokenStream) -> bool:
        """
        Check if the grammar can parse the next tokens. Is always true, because the grammar may be repeated zero times
        """
        return True

    def match(self, tokens: TokenStream, dict: Dict) -> dict:
        """
        Match the grammar and store the values at the labeled sections in the dictionary if the grammar is present

        Args:
            tokens (TokenStream): the tokens to match
            dict (Dict[str, NodeT]): the dictionary to store the values at the labeled sections

        Returns:
            Dict[str, NodeT]: the dictionary, maybe with the values at the labeled sections
        """
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
    """
    A Wrapper for a parser that stores the result in a dictionary with a label

    Attributes:
        label (str): the label to store the result under
        item (Parser): the parser to wrap
    """
    label: str
    item: Parser

    def __init__(self, item: Parser, label: str) -> None:
        """
        Constructor

        Args:
            item (Parser): the parser to wrap
            label (str): the label to store the result under
        """
        self.label = label
        self.item = item

    def __str__(self):
        return f"Labeled({self.label}, {self.item})"

    def check(self, tokens: TokenStream) -> bool:
        """
        Check if the grammar can parse the next tokens

        Args:
            tokens (TokenStream): the tokens to check   
        
        Returns:
            bool: True if the grammar can parse the next tokens
        """
        return self.item.check(tokens)

    def match(self, tokens: TokenStream, dict: Dict) -> dict:
        """
        Parse the grammar and store the result in the dictionary under the label

        Args:
            tokens (TokenStream): the tokens to parse
            dict (Dict[str, NodeT]): the dictionary to store the result under the label

        Returns:
            Dict[str, NodeT]: the dictionary with the result stored under the label
        """

        node = self.item.parse(tokens)
        dict[self.label] = node
        return dict

    def is_single_token(self) -> bool:
        return self.item.is_single_token()


class AnyWord(Parser, Generic[NodeT]):
    """
    A Parser that represents any word. The word is stored in a syntax tree node, the nodeConstructor is used to create the node

    Attributes:
        nodeConstructor (Callable[[str], NodeT]): the function to create the syntax tree node
    """
    nodeConstructor: Callable[[str], NodeT]

    def __init__(self, nodeConstructor: Callable[[str], NodeT]):
        """
        Initialize the Grammar object.

        Args:
            nodeConstructor (Callable[[str], NodeT]): A callable that constructs a NodeT object given a string.

        Returns:
            None
        """
        self.nodeConstructor = nodeConstructor

    def check(self, tokens: TokenStream) -> bool:
        """
        Check if the grammar can parse the next tokens

        Args:
            tokens (TokenStream): the tokens to check

        Returns:
            bool: True if the grammar can parse the next tokens
        """
        next = tokens.peek()
        if next is None:
            return False
        return next.type == TokenType.WORD
        # return (not tokens.is_eof()) and tokens.peek().type == TokenType.WORD

    def parse(self, tokens: TokenStream) -> NodeT:
        """
        Parse the grammar and return the syntax tree

        Args:
            tokens (TokenStream): the tokens to parse

        Returns:
            NodeT: the result of nodeConstructor
        """
        assert self.nodeConstructor is not None
        next = tokens.next()
        assert next is not None
        return self.nodeConstructor(next.value)

    def is_single_token(self) -> bool:
        return True


class AnyNumber(Parser, Generic[NodeT]):
    """
    Parser for parsing any number token in the input stream.

    Args:
        nodeConstructor (Callable[[float], NodeT]): A callable that constructs a node object from a float value.

    Attributes:
        nodeConstructor (Callable[[float], NodeT]): A callable that constructs a node object from a float value.
    """

    nodeConstructor: Callable[[float], NodeT]

    def __init__(self, nodeConstructor: Callable[[float], NodeT]):
        self.nodeConstructor = nodeConstructor

    def check(self, tokens: TokenStream) -> bool:
        """
        Checks if the next token in the token stream is a number.

        Args:
            tokens (TokenStream): The token stream to check.

        Returns:
            bool: True if the next token is a number, False otherwise.
        """
        next = tokens.peek()
        if next is None:
            return False
        return next.type == TokenType.NUMBER

    def parse(self, tokens: TokenStream) -> NodeT:
        """
        Parses the next number token in the token stream and constructs a node object from it.

        Args:
            tokens (TokenStream): The token stream to parse.

        Returns:
            NodeT: The constructed node object.
        """
        assert self.nodeConstructor is not None
        next = tokens.next()
        assert next is not None
        return self.nodeConstructor(float(next.value))

    def is_single_token(self) -> bool:
        """
        Checks if this parser only consumes a single token.

        Returns:
            bool: True if this parser only consumes a single token, False otherwise.
        """
        return True


class AnyString(Parser, Generic[NodeT]):
    """
    Represents a parser that matches any string token and constructs a node using the provided node constructor.

    Args:
        nodeConstructor (Callable[[str], NodeT]): A callable that constructs a node using a string value.

    Methods:
        check(tokens: TokenStream) -> bool: Checks if the next token in the token stream is a string token.
        parse(tokens: TokenStream) -> NodeT: Parses the next string token and constructs a node using the node constructor.
        is_single_token() -> bool: Returns True indicating that this parser matches a single token.

    Type Parameters:
        NodeT: The type of node that this parser constructs.
    """
    nodeConstructor: Callable[[str], NodeT]

    def __init__(self, nodeConstructor: Callable[[str], NodeT]):
        self.nodeConstructor = nodeConstructor

    def check(self, tokens: TokenStream) -> bool:
        """
        Checks if the next token in the token stream is a string token.

        Args:
            tokens (TokenStream): The token stream to check.

        Returns:
            bool: True if the next token is a string token, False otherwise.
        """
        next = tokens.peek()
        if next is None:
            return False
        return next.type == TokenType.STRING

    def parse(self, tokens: TokenStream) -> NodeT:
        """
        Parses the next string token and constructs a node using the node constructor.

        Args:
            tokens (TokenStream): The token stream to parse.

        Returns:
            NodeT: The constructed node.
        """
        assert self.nodeConstructor is not None
        next = tokens.next()
        assert next is not None
        return self.nodeConstructor(next.value)

    def is_single_token(self) -> bool:
        """
        Returns True indicating that this parser matches a single token.

        Returns:
            bool: True indicating that this parser matches a single token.
        """
        return True


class SymbolParser(Parser, Generic[NodeT]):
    """
    Represents a parser for a specific symbol in the grammar.

    Args:
        symbol (str): The symbol to be parsed.
        nodeConstructor (Callable[[str], NodeT]): A callable that constructs a node of type NodeT.

    Attributes:
        symbol (str): The symbol to be parsed.
        nodeConstructor (Callable[[str], NodeT]): A callable that constructs a node of type NodeT.
    """

    symbol: str
    nodeConstructor: Callable[[str], NodeT]

    def __init__(self, symbol: str, nodeConstructor: Callable[[str], NodeT]):
        self.symbol = symbol
        self.nodeConstructor = nodeConstructor

    def __str__(self) -> str:
        """
        Returns a string representation of the symbol.

        Returns:
            str: The string representation of the symbol.
        """
        return self.symbol

    def check(self, tokens: TokenStream) -> bool:
        """
        Checks if the next token in the token stream matches the symbol.

        Args:
            tokens (TokenStream): The token stream to check.

        Returns:
            bool: True if the next token matches the symbol, False otherwise.
        """
        next = tokens.peek()
        if next is None:
            return False
        return next.value == self.symbol

    def parse(self, tokens: TokenStream) -> NodeT:
        """
        Parses the next token in the token stream and constructs a node.

        Args:
            tokens (TokenStream): The token stream to parse.

        Returns:
            NodeT: The constructed node.

        Raises:
            ParserError: If the next token does not match the symbol.
        """
        next = tokens.next()
        
        assert next is not None
        if next.value != self.symbol:
            raise ParserError(f"expected symbol {self.symbol}, got {next.value}", next.slice)
        return self.nodeConstructor(next.value)

    def is_single_token(self) -> bool:
        """
        Checks if the symbol represents a single token.

        Returns:
            bool: True if the symbol represents a single token, False otherwise.
        """
        return True


class Symbol(Matcher):
    """
    Represents a matcher for a specific symbol in the grammar.

    Args:
        symbol (str): The symbol to be matched.

    """
    symbol: str

    def __init__(self, symbol: str):
        """
        Initializes a Symbol object with the given symbol.

        Args:
            symbol (str): The symbol to be matched.

        """
        self.symbol = symbol

    def __str__(self) -> str:
        """
        Returns the string representation of the Symbol object.

        Returns:
            str: The string representation of the Symbol object.

        """
        return self.symbol

    def check(self, tokens: TokenStream) -> bool:
        """
        Checks if the next token in the TokenStream matches the symbol.

        Args:
            tokens (TokenStream): The TokenStream to check.

        Returns:
            bool: True if the next token matches the symbol, False otherwise.

        """
        next = tokens.peek()
        if next is None:
            return False
        return next.value == self.symbol

    def match(self, tokens: TokenStream, dict: Dict) -> Dict:
        """
        Matches the next token in the TokenStream with the symbol.

        Args:
            tokens (TokenStream): The TokenStream to match against.
            dict (Dict): The dictionary to update with matched values.

        Returns:
            Dict: The updated dictionary.

        Raises:
            ParserError: If the next token does not match the symbol.

        """
        assert isinstance(dict, Dict)

        next = tokens.next()
        assert next is not None
        if next.value != self.symbol:
            raise ParserError(f"expected symbol {self.symbol}, got {next.value}", next.slice)
        return dict

    def is_single_token(self) -> bool:
        """
        Checks if the Symbol is a single token.

        Returns:
            bool: always True, because a symbol is a single token.

        """
        return True


class WordParser(Parser, Generic[NodeT]):
    """
    A parser that matches a specific word in the input token stream.

    Attributes:
        word (str): The word to match.
        nodeConstructor (Optional[Callable[[str], NodeT]]): An optional function to construct a node from the matched word.
    """

    word: str
    nodeConstructor: Optional[Callable[[str], NodeT]]

    def __init__(self, word: str, nodeConstructor: Optional[Callable[[str], NodeT]] = None):
        self.word = word
        self.nodeConstructor = nodeConstructor

    def __str__(self) -> str:
        return self.word

    def check(self, tokens: TokenStream) -> bool:
        """
        Check if the next token in the token stream matches the word.

        Args:
            tokens (TokenStream): The token stream to check.

        Returns:
            bool: True if the next token matches the word, False otherwise.
        """
        next = tokens.peek()
        if next is None:
            return False
        return next.value == self.word

    def parse(self, tokens: TokenStream) -> NodeT:
        """
        Parse the next token in the token stream and return a node constructed from the matched word.

        Args:
            tokens (TokenStream): The token stream to parse.

        Returns:
            NodeT: The constructed node.

        Raises:
            ParserError: If the next token does not match the word.
        """
        next = tokens.next()
        assert next is not None
        if next.value != self.word:
            raise ParserError(f"expected word {self.word}, got {next.value}", next.slice)
        assert self.nodeConstructor is not None
        return self.nodeConstructor(next.value)

    def is_single_token(self) -> bool:
        """
        Check if the parser matches a single token.

        Returns:
            bool: True if the parser matches a single token, False otherwise.
        """
        return True


class Word(Matcher):
    """
    Represents a matcher for a specific word in the grammar.

    Args:
        word (str): The word to be matched.

    """
    word: str

    def __init__(self, word: str):
        self.word = word

    def __str__(self) -> str:
        return self.word

    def check(self, tokens: TokenStream) -> bool:
        """
        Checks if the next token in the token stream matches the word.
        
        Args:
            tokens (TokenStream): The token stream to check.
        
        Returns:
            bool: True if the next token matches the word, False otherwise.
        """
        next = tokens.peek()
        if next is None:
            return False
        return next.value == self.word

    def match(self, tokens: TokenStream, dict: Dict) -> Dict:
        """
        Matches the word with the next token in the token stream.
        
        Args:
            tokens (TokenStream): The token stream to match against.
            dict (Dict): The dictionary to update with the matched word.
        
        Returns:
            Dict: The updated dictionary.
        
        Raises:
            ParserError: If the next token does not match the word.
        """
        assert isinstance(dict, Dict)

        next = tokens.next()
        assert next is not None
        if next.value != self.word:
            raise ParserError(f"expected word {self.word}, got {next.value}", next.slice)
        return dict

    def is_single_token(self) -> bool:
        """
        Checks if the matcher represents a single token.
        
        Returns:
            bool: True if the matcher represents a single token, False otherwise.
        """
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
