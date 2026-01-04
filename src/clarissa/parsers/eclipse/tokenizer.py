"""ECLIPSE Deck Tokenizer.

Lexical analysis for ECLIPSE reservoir simulation decks.
Converts raw deck text into a stream of typed tokens.

Usage:
    from clarissa.parsers.eclipse.tokenizer import Tokenizer
    
    deck_text = '''
    RUNSPEC
    DIMENS
    100 100 20 /
    '''
    
    tokenizer = Tokenizer(deck_text)
    for token in tokenizer:
        print(f"{token.type}: {token.value}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator


class TokenType(Enum):
    """Types of tokens in an ECLIPSE deck."""
    
    # Structure
    KEYWORD = auto()      # RUNSPEC, DIMENS, WELSPECS, etc.
    TERMINATOR = auto()   # /
    
    # Literals
    INTEGER = auto()      # 100, 20
    REAL = auto()         # 3.14, 1.5E-6
    STRING = auto()       # 'PROD1', 'filename.inc'
    DATE = auto()         # 1 JAN 2025
    
    # Special
    REPEAT = auto()       # 100*0.25 (repeat notation)
    DEFAULT = auto()      # 1* (default marker)
    STAR = auto()         # * (standalone)
    
    # Other
    COMMENT = auto()      # -- comment text
    NEWLINE = auto()      # Line break
    WHITESPACE = auto()   # Spaces, tabs
    EOF = auto()          # End of file
    UNKNOWN = auto()      # Unrecognized


@dataclass
class Token:
    """A single token from the deck."""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.column})"


# Token patterns (order matters - more specific patterns first)
TOKEN_PATTERNS = [
    # Comments (must be first to capture before other processing)
    (TokenType.COMMENT, r'--[^\n]*'),
    
    # Terminator
    (TokenType.TERMINATOR, r'/'),
    
    # Repeat notation: N*value or N* (default)
    (TokenType.REPEAT, r'\d+\*[\d.eE+-]+'),
    (TokenType.DEFAULT, r'\d+\*'),
    
    # Standalone star
    (TokenType.STAR, r'\*'),
    
    # Strings (single-quoted)
    (TokenType.STRING, r"'[^']*'"),
    
    # Date pattern: D MON YYYY
    (TokenType.DATE, r'\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{4}'),
    
    # Numbers (real must be before integer to catch decimals)
    (TokenType.REAL, r'[+-]?\d+\.\d*(?:[eE][+-]?\d+)?'),
    (TokenType.REAL, r'[+-]?\d+[eE][+-]?\d+'),
    (TokenType.INTEGER, r'[+-]?\d+'),
    
    # Keywords (letters, may include digits, typically uppercase)
    (TokenType.KEYWORD, r'[A-Za-z][A-Za-z0-9_]*'),
    
    # Whitespace
    (TokenType.NEWLINE, r'\n'),
    (TokenType.WHITESPACE, r'[ \t]+'),
]

# Compile patterns
COMPILED_PATTERNS = [
    (token_type, re.compile(pattern, re.IGNORECASE if token_type == TokenType.DATE else 0))
    for token_type, pattern in TOKEN_PATTERNS
]


class Tokenizer:
    """Lexical analyzer for ECLIPSE decks.
    
    Converts deck text into a stream of tokens. Handles:
    - Keywords (RUNSPEC, DIMENS, etc.)
    - Numbers (integers, reals, scientific notation)
    - Strings (single-quoted)
    - Dates (D MON YYYY format)
    - Repeat notation (100*0.25)
    - Comments (-- to end of line)
    - Terminators (/)
    
    Attributes:
        text: The input deck text.
        pos: Current position in text.
        line: Current line number (1-indexed).
        column: Current column number (1-indexed).
    """
    
    def __init__(self, text: str):
        """Initialize tokenizer with deck text.
        
        Args:
            text: ECLIPSE deck content.
        """
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
    
    def __iter__(self) -> Iterator[Token]:
        """Iterate over tokens in the deck."""
        while self.pos < len(self.text):
            token = self._next_token()
            if token.type != TokenType.WHITESPACE:  # Skip whitespace
                yield token
        
        # Emit EOF
        yield Token(TokenType.EOF, "", self.line, self.column)
    
    def _next_token(self) -> Token:
        """Get the next token from input."""
        if self.pos >= len(self.text):
            return Token(TokenType.EOF, "", self.line, self.column)
        
        # Try each pattern
        for token_type, pattern in COMPILED_PATTERNS:
            match = pattern.match(self.text, self.pos)
            if match:
                value = match.group(0)
                token = Token(token_type, value, self.line, self.column)
                self._advance(value)
                return token
        
        # Unknown character
        char = self.text[self.pos]
        token = Token(TokenType.UNKNOWN, char, self.line, self.column)
        self._advance(char)
        return token
    
    def _advance(self, text: str) -> None:
        """Advance position and update line/column tracking."""
        for char in text:
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
    
    def tokenize(self) -> list[Token]:
        """Tokenize entire input and return list of tokens.
        
        Returns:
            List of all tokens (excluding whitespace).
        """
        return list(self)


class TokenStream:
    """Buffered token stream for parsing.
    
    Provides lookahead and backtracking capabilities.
    
    Usage:
        stream = TokenStream(tokenizer)
        
        if stream.peek().type == TokenType.KEYWORD:
            token = stream.consume()
    """
    
    def __init__(self, tokenizer: Tokenizer):
        """Initialize with tokenizer.
        
        Args:
            tokenizer: Source tokenizer.
        """
        self._tokens = list(tokenizer)
        self._pos = 0
    
    def peek(self, offset: int = 0) -> Token:
        """Look at a token without consuming it.
        
        Args:
            offset: How far ahead to look (0 = current).
        
        Returns:
            Token at the offset position, or EOF if past end.
        """
        idx = self._pos + offset
        if idx >= len(self._tokens):
            return self._tokens[-1]  # Return EOF
        return self._tokens[idx]
    
    def consume(self) -> Token:
        """Consume and return the current token.
        
        Returns:
            The current token.
        """
        token = self.peek()
        if token.type != TokenType.EOF:
            self._pos += 1
        return token
    
    def expect(self, expected_type: TokenType) -> Token:
        """Consume a token of the expected type.
        
        Args:
            expected_type: The required token type.
        
        Returns:
            The consumed token.
        
        Raises:
            SyntaxError: If the token type doesn't match.
        """
        token = self.consume()
        if token.type != expected_type:
            raise SyntaxError(
                f"Expected {expected_type.name}, got {token.type.name} "
                f"at line {token.line}, column {token.column}"
            )
        return token
    
    def skip_comments(self) -> None:
        """Skip over any comment tokens."""
        while self.peek().type == TokenType.COMMENT:
            self.consume()
    
    def skip_newlines(self) -> None:
        """Skip over newline tokens."""
        while self.peek().type == TokenType.NEWLINE:
            self.consume()
    
    @property
    def eof(self) -> bool:
        """Check if at end of input."""
        return self.peek().type == TokenType.EOF


# Known ECLIPSE section keywords
SECTION_KEYWORDS = {
    "RUNSPEC", "GRID", "EDIT", "PROPS", 
    "REGIONS", "SOLUTION", "SUMMARY", "SCHEDULE"
}

# Keywords that take no data (flags)
FLAG_KEYWORDS = {
    "OIL", "WATER", "GAS", "DISGAS", "VAPOIL",
    "METRIC", "FIELD", "LAB", "NOSIM", "END",
    "RUNSUM", "EXCEL", "UNIFOUT", "UNIFIN"
}


def is_section_keyword(keyword: str) -> bool:
    """Check if a keyword starts a major section."""
    return keyword.upper() in SECTION_KEYWORDS


def is_flag_keyword(keyword: str) -> bool:
    """Check if a keyword is a simple flag (no data)."""
    return keyword.upper() in FLAG_KEYWORDS


__all__ = [
    "TokenType",
    "Token",
    "Tokenizer",
    "TokenStream",
    "is_section_keyword",
    "is_flag_keyword",
    "SECTION_KEYWORDS",
    "FLAG_KEYWORDS",
]