from enum import Enum, auto
from typing import List, Optional

# there are different types of tokens
class TokenType(Enum):
    """
    The type of a token

    Possible values:
        WORD: a word
        NUMBER: a number
        SYMBOL: a symbol
        STRING: a string
    """
    WORD = auto()
    NUMBER = auto()
    SYMBOL = auto()
    STRING = auto()
class bcolors:
    """
    Colors for the terminal, values copied from https://stackoverflow.com/a/287944/11143265
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CodePos:
    """
    The position of a character in a text

    Attributes:
        line (int): the line number (1-indexed)
        column (int): the column number (1-indexed)
        text (str): the text
    """
    line: int
    column: int
    text: str

    def __init__(self, line: int, column: int, text: str):
        """
        Create a new CodePos

        Args:
            line (int): the line number (1-indexed)
            column (int): the column number (1-indexed)
            text (str): the text
        """
        self.line = line
        self.column = column
        self.text = text

    def highlight(self) -> str:
        """
        Highlight the character at this position in the text

        Returns:
            str: the text with the character at this position highlighted
        """
        lines = self.text.split("\n")
        line = lines[self.line - 1]
        before = line[:self.column - 1]
        after = line[self.column - 1:]
        return before + bcolors.FAIL + line[self.column] + bcolors.ENDC + after
    def __repr__(self):
        return f"CodePos({self.line}, {self.column})"
    
    def __str__(self):
        return f"line: {self.line}, column: {self.column}"
class CodeSlice:
    """
    A slice of code

    Attributes:
        start (CodePos): the start position
        end (CodePos): the end position
    """
    start: CodePos
    end: CodePos

    def __init__(self, start: CodePos, end: CodePos):
        """
        Create a new CodeSlice

        Args:
            start (CodePos): the start position
            end (CodePos): the end position
        """
        self.start = start
        self.end = end

    def highlight(self) -> str:
        """
        Highlight the code in the slice
        
        Returns:
            str: the code with the slice highlighted
        """
        lines = self.start.text.split("\n")
        start_line = lines[self.start.line - 1]
        # lines, without start and end line

        if self.start.line == self.end.line:
            before = start_line[:self.start.column - 1]
            middle = start_line[self.start.column - 1:self.end.column - 1]
            after = start_line[self.end.column - 1:]
            return before + bcolors.FAIL + middle + bcolors.ENDC + after
        
        middle_lines = lines[self.start.line + 1:self.end.line]
        end_line = lines[self.end.line - 1]
        before_start = start_line[:self.start.column - 1]
        after_start = start_line[self.start.column - 1:]
        before_end = end_line[:self.end.column - 1]
        after_end = end_line[self.end.column:]
       # print(f"before_start: {before_start}, after_start: {after_start}, before_end: {before_end}, after_end: {after_end}")
        
        result = ""
        result += before_start + bcolors.FAIL + after_start + "\n"
        for line in middle_lines:
            result += line + "\n"
        result += before_end + bcolors.ENDC + after_end
        return result

    def __repr__(self):
        return f"CodeSlice({self.start}, {self.end})"
    
    def __str__(self):
        return f"start: {self.start}, end: {self.end}"
class Token:
    """
    A token

    Attributes:
        type (TokenType): the type of the token
        value (str): the value of the token
        slice (CodeSlice): the slice of code the token is in
    """
    type: TokenType
    value: str
    slice: CodeSlice

    def __init__(self, type: TokenType, value: str, slice: CodeSlice):
        """
        Create a new Token

        Args:
            type (TokenType): the type of the token
            value (str): the value of the token
            slice (CodeSlice): the slice of code the token is in
        """
        self.type = type
        self.value = value
        self.slice = slice

    def __repr__(self):
        return f'Token({self.type}, "{self.value}")'
    
    def __str__(self):
        return self.value

class CharStream:
    """
    Represents a character stream for lexical analysis.

    Attributes:
        string (str): The input string.
        index (int): The current index in the string.
        line (int): The current line number.
        column (int): The current column number.
    """

    string: str
    index: int

    line: int
    column: int

    def __init__(self, string: str):
        """
        Initializes a new instance of the CharStream class.

        Args:
            string (str): The input string.
        """
        self.string = string
        self.index = 0
        self.line = 1
        self.column = 1

    def peek(self) -> Optional[str]:
        """
        Returns the next character in the stream without advancing the index.

        Returns:
            Optional[str]: The next character in the stream, or None if the end of the stream is reached.
        """
        if self.index >= len(self.string):
            return None
        return self.string[self.index]

    def next(self) -> Optional[str]:
        """
        Returns the next character in the stream and advances the index.

        Returns:
            Optional[str]: The next character in the stream, or None if the end of the stream is reached.
        """
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
        """
        Returns the current position in the code.

        Returns:
            CodePos: The current position in the code.
        """
        return CodePos(self.line, self.column, self.string)

    def is_eof(self) -> bool:
        """
        Checks if the end of the stream is reached.

        Returns:
            bool: True if the end of the stream is reached, False otherwise.
        """
        return self.index >= len(self.string)
class TokenStream:
    """
    Represents a stream of tokens.

    Attributes:
        tokens (List[Token]): The list of tokens in the stream.
        index (int): The current index in the stream.
    """

    tokens: List[Token]
    index: int

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.index = 0

    def peek(self) -> Optional[Token]:
        """
        Returns the next token in the stream without consuming it.

        Returns:
            Optional[Token]: The next token in the stream, or None if the end of the stream is reached.
        """
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def next(self) -> Optional[Token]:
        """
        Returns the next token in the stream and advances the index.

        Returns:
            Optional[Token]: The next token in the stream, or None if the end of the stream is reached.
        """
        if self.index >= len(self.tokens):
            return None
        token = self.tokens[self.index]
        self.index += 1
        return token

    def is_eof(self) -> bool:
        """
        Checks if the end of the stream has been reached.

        Returns:
            bool: True if the end of the stream has been reached, False otherwise.
        """
        return self.index >= len(self.tokens)
# lexer error
class LexerError(Exception):
    """
    Represents an error that occurred during lexical analysis.

    Attributes:
        pos (CodePos): The position in the code where the error occurred.
    """
    pos: CodePos

    def __init__(self, message: str, pos: CodePos):
        """
        Initializes a new instance of the LexerError class.

        Args:
            message (str): The error message.
            pos (CodePos): The position in the code where the error occurred.
        """
        super().__init__(f"Lexer error at {pos}: {message} + \n {pos.highlight()}")
        self.pos = pos
def is_whitespace(char: str) -> bool:
    """
    Checks if a character is whitespace.

    Args:
        char (str): The character to check.

    Returns:
        bool: True if the character is whitespace, False otherwise.
    """
    return char in [" ", "\t", "\n"]
# __, so it's private
class __Lexer:
    """
    A lexer class that tokenizes a given text based on specified rules.

    Attributes:
    - stream: CharStream - The character stream to be tokenized.
    - alphabet: str - The allowed characters for word tokens.
    - num_sep: str - The separator character for numbers.
    - symbol_chars: str - The allowed characters for symbol tokens.
    - multi_symbols: List[str] - The list of multi-character symbols.
    - str_chars: str - The allowed characters for string tokens.
    - tokens: List[Token] - The list of tokens generated by the lexer.

    Methods:
    - __init__(self, text: str, alphabet: str, num_sep: str, symbol_chars: str, multi_symbols: List[str], str_chars: str):
        Initializes the lexer with the given text and tokenization rules.
    - lex_word(self):
        Tokenizes a word from the character stream.
    - lex_number(self):
        Tokenizes a number from the character stream.
    - lex_whitespace(self):
        Skips whitespace characters from the character stream.
    - lex_symbol(self):
        Tokenizes a symbol from the character stream.
    - lex_string(self):
        Tokenizes a string from the character stream.
    - lex(self) -> List[Token]:
        Tokenizes the entire character stream and returns the list of tokens.
    """
    stream: CharStream
    alphabet: str
    num_sep: str
    symbol_chars: str
    multi_symbols: List[str]
    str_chars: str

    tokens: List[Token]

    def __init__(self, text: str, alphabet: str, num_sep: str, symbol_chars: str, multi_symbols: List[str], str_chars: str):
        """
        Initializes a new instance of the __Lexer class.

        Args:
            text (str): The text to be tokenized.
            alphabet (str): The allowed characters for word tokens.
            num_sep (str): The separator character for numbers.
            symbol_chars (str): The allowed characters for symbol tokens.
            multi_symbols (List[str]): The list of multi-character symbols.
            str_chars (str): The allowed characters for string tokens.
        """
        self.stream = CharStream(text)
        self.alphabet = alphabet
        self.num_sep = num_sep
        self.symbol_chars = symbol_chars
        self.multi_symbols = multi_symbols
        self.str_chars = str_chars
        self.tokens = []
    
    def lex_word(self):
        """
        Tokenizes a word from the character stream.
        """
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
        """
        Tokenizes a number from the character stream.
        """
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
        """
        Skips whitespace characters from the character stream.
        """
        while True:
            char = self.stream.peek()
            if char is None or not is_whitespace(char):
                break
            self.stream.next()
    
    def lex_symbol(self):
        """
        Tokenizes a symbol from the character stream.
        """
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
    def lex_string(self):
        """
        Tokenizes a string from the character stream.
        """
        # string can be escaped with \" or \' and enclosed in "" or ''
        string = ""
        start_pos = self.stream.get_pos()
        quote = self.stream.next()
        assert quote is not None
        while True:
            char = self.stream.next()
            if char is None:
                raise LexerError("Unexpected EOF", self.stream.get_pos())
            if char == quote:
                break
            if char == "\\":
                next_char = self.stream.next()
                if next_char is None:
                    raise LexerError("Unexpected EOF", self.stream.get_pos())
                if next_char == quote:
                    char = quote
                else:
                    char = "\\" + next_char
            string += char
        end_pos = self.stream.get_pos()
        self.tokens.append(Token(TokenType.STRING, string, CodeSlice(start_pos, end_pos)))

    def lex(self) -> List[Token]:
        """
        Tokenizes the entire character stream and returns the list of tokens.

        Returns:
            List[Token]: The list of tokens generated by the lexer.
        """
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
            elif char in self.str_chars:
                self.lex_string()
            else:
                raise LexerError(f"Unknown character '{char}'", self.stream.get_pos())
        return self.tokens
def lex(string: str, symbol_chars: str, multi_symbols: List[str] = [], num_sep: str = "." , alphabet: str = "abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ", str_chars = "\"'") -> List[Token]:
    """
    Tokenizes a given string based on parameters.

    Args:
        string (str): The string to be tokenized.
        symbol_chars (str): The allowed characters for symbol tokens.
        multi_symbols (List[str]): The list of multi-character symbols.
        num_sep (str): The separator character for numbers.
        alphabet (str): The allowed characters for word tokens.
        str_chars (str): The allowed characters for string tokens.
    
    Returns:
        List[Token]: The list of tokens generated by the lexer.
    """
    lexer = __Lexer(string, alphabet, num_sep, symbol_chars, multi_symbols, str_chars)
    return lexer.lex()

if __name__ == "__main__":
    print(lex("hello wOrld_2_a + 3 - 4 a", symbol_chars="+-*/"))