"""ECLIPSE Deck Parsing Module.

Provides tokenization and AST representation for ECLIPSE reservoir
simulation decks. Enables CLARISSA to parse, manipulate, and generate
deck syntax.

Modules:
    tokenizer: Lexical analysis (text → tokens)
    nodes: AST node definitions (tokens → tree)
"""

from clarissa.parsers.eclipse.tokenizer import (
    TokenType,
    Token,
    Tokenizer,
    TokenStream,
)
from clarissa.parsers.eclipse.nodes import (
    Deck,
    Section,
    Keyword,
    Record,
    Comment,
)

__all__ = [
    "TokenType",
    "Token", 
    "Tokenizer",
    "TokenStream",
    "Deck",
    "Section",
    "Keyword",
    "Record",
    "Comment",
]
