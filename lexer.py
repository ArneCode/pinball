from enum import Enum, auto
from typing import List, Optional

# there are different types of tokens
class TokenType(Enum):
    WORD = auto()
    NUMBER = auto()
    SYMBOL = auto()
class CodePos:
    line: int
    column: int

    def __init__(self, line: int, column: int):
        self.line = line
        self.column = column

    def __repr__(self):
        return f"CodePos({self.line}, {self.column})"
    
    def __str__(self):
        return f"line: {self.line}, column: {self.column}"
class CodeSlice:
    start: CodePos
    end: CodePos

    def __init__(self, start: CodePos, end: CodePos):
        self.start = start
        self.end = end

    def __repr__(self):
        return f"CodeSlice({self.start}, {self.end})"
    
    def __str__(self):
        return f"start: {self.start}, end: {self.end}"
class Token:
    type: TokenType
    value: str
    slice: CodeSlice

    def __init__(self, type: TokenType, value: str, slice: CodeSlice):
        self.type = type
        self.value = value
        self.slice = slice

    def __repr__(self):
        return f'Token({self.type}, "{self.value}")'
    
    def __str__(self):
        return self.value

class CharStream:
    string: str
    index: int

    line: int
    column: int

    def __init__(self, string: str):
        self.string = string
        self.index = 0
        self.line = 1
        self.column = 1

    def peek(self) -> Optional[str]:
        if self.index >= len(self.string):
            return None
        return self.string[self.index]

    def next(self) -> Optional[str]:
        if self.index >= len(self.string):
            return None
        char = self.string[self.index]
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.index += 1
        return char
    def get_pos(self) -> CodePos:
        return CodePos(self.line, self.column)
    def is_eof(self) -> bool:
        return self.index >= len(self.string)
class TokenStream:
    tokens: List[Token]
    index: int

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.index = 0

    def peek(self) -> Optional[Token]:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def next(self) -> Optional[Token]:
        if self.index >= len(self.tokens):
            return None
        token = self.tokens[self.index]
        self.index += 1
        return token
    def is_eof(self) -> bool:
        return self.index >= len(self.tokens)
# lexer error
class LexerError(Exception):
    def __init__(self, message: str, pos: CodePos):
        super().__init__(f"Lexer error at {pos}: {message}")
        self.pos = pos
def is_whitespace(char: str) -> bool:
    return char in [" ", "\t", "\n"]
class __Lexer:
    stream: CharStream
    alphabet: str
    num_sep: str
    symbol_chars: str
    multi_symbols: List[str]

    tokens: List[Token]

    def __init__(self, text: str, alphabet: str, num_sep: str, symbol_chars: str, multi_symbols: List[str]):
        self.stream = CharStream(text)
        self.alphabet = alphabet
        self.num_sep = num_sep
        self.symbol_chars = symbol_chars
        self.multi_symbols = multi_symbols
        self.tokens = []
    
    def lex_word(self):
        word = ""
        start_pos = self.stream.get_pos()
        while True:
            char = self.stream.peek()
            if char is None or (char not in self.alphabet and not char.isdigit()) or is_whitespace(char):
                break
            word += char
            self.stream.next()
        end_pos = self.stream.get_pos()
        self.tokens.append(Token(TokenType.WORD, word, CodeSlice(start_pos, end_pos)))
    def lex_number(self):
        number = ""
        start_pos = self.stream.get_pos()
        while True:
            char = self.stream.peek()
            if char is None or is_whitespace(char) or char in self.symbol_chars:
                break
            if char != self.num_sep and not char.isdigit():
                raise LexerError(f"Invalid number character '{char}', maybe add a space", self.stream.get_pos())
            number += char
            self.stream.next()
        end_pos = self.stream.get_pos()
        self.tokens.append(Token(TokenType.NUMBER, number, CodeSlice(start_pos, end_pos)))
    def lex_whitespace(self):
        while True:
            char = self.stream.peek()
            if char is None or not is_whitespace(char):
                break
            self.stream.next()
    def lex_symbol(self):
        start_pos = self.stream.get_pos()
        symbol = self.stream.next()
        assert symbol is not None
        while True:
            next_char = self.stream.peek()
            if next_char is None or next_char not in self.symbol_chars:
                break
            assert next_char is not None
            new_symbol = symbol + next_char
            if new_symbol not in self.multi_symbols:
                break
            symbol += next_char
            self.stream.next()
        end_pos = self.stream.get_pos()
        self.tokens.append(Token(TokenType.SYMBOL, symbol, CodeSlice(start_pos, end_pos)))
    def lex(self) -> List[Token]:
        while not self.stream.is_eof():
            char = self.stream.peek()
            assert char is not None
            if char in self.alphabet:
                self.lex_word()
            elif char.isdigit():
                self.lex_number()
            elif char in self.symbol_chars:
                self.lex_symbol()
            elif is_whitespace(char):
                self.lex_whitespace()
            else:
                raise LexerError(f"Unknown character '{char}'", self.stream.get_pos())
        return self.tokens
def lex(string: str, symbol_chars: str, multi_symbols: List[str] = [], num_sep: str = "." , alphabet: str = "abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ") -> List[Token]:
    lexer = __Lexer(string, alphabet, num_sep, symbol_chars, multi_symbols)
    return lexer.lex()

if __name__ == "__main__":
    print(lex("hello wOrld_2_a + 3 - 4 a", symbol_chars="+-*/"))