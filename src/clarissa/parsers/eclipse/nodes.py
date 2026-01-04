"""ECLIPSE Deck Abstract Syntax Tree.

Defines the AST structure for representing parsed ECLIPSE decks.
Enables structured manipulation and code generation.

Usage:
    from clarissa.parsers.eclipse.ast import Deck, Section, Keyword, Record
    
    # Build AST programmatically
    deck = Deck()
    deck.add_section(Section("RUNSPEC", [
        Keyword("DIMENS", [Record([100, 100, 20])]),
        Keyword("OIL"),
        Keyword("WATER"),
    ]))
    
    # Generate deck text
    print(deck.to_string())
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Iterator, Union


class NodeType(Enum):
    """Types of AST nodes."""
    DECK = "deck"
    SECTION = "section"
    KEYWORD = "keyword"
    RECORD = "record"
    VALUE = "value"
    COMMENT = "comment"


# Value types that can appear in records
Value = Union[int, float, str, date, None]  # None = default (1*)


@dataclass
class Comment:
    """A comment in the deck."""
    text: str
    line: int = 0
    
    def to_string(self) -> str:
        return f"-- {self.text}"


@dataclass
class Record:
    """A data record within a keyword.
    
    Represents a single line of values terminated by '/'.
    
    Attributes:
        values: List of values in the record.
        comment: Optional inline comment.
    """
    values: list[Value] = field(default_factory=list)
    comment: str | None = None
    
    def __len__(self) -> int:
        return len(self.values)
    
    def __getitem__(self, idx: int) -> Value:
        return self.values[idx]
    
    def append(self, value: Value) -> None:
        """Add a value to the record."""
        self.values.append(value)
    
    def to_string(self) -> str:
        """Convert record to ECLIPSE syntax."""
        parts = []
        for v in self.values:
            if v is None:
                parts.append("1*")
            elif isinstance(v, str):
                if not v.startswith("'"):
                    parts.append(f"'{v}'")
                else:
                    parts.append(v)
            elif isinstance(v, float):
                # Use scientific notation for very small/large numbers
                if abs(v) < 0.001 or abs(v) > 100000:
                    parts.append(f"{v:.4E}")
                else:
                    parts.append(str(v))
            elif isinstance(v, date):
                parts.append(v.strftime("%d %b %Y").upper())
            else:
                parts.append(str(v))
        
        result = " ".join(parts) + " /"
        if self.comment:
            result += f"  -- {self.comment}"
        return result


@dataclass
class Keyword:
    """An ECLIPSE keyword with its data.
    
    Keywords can have:
    - No data (flags like OIL, WATER)
    - Single record (DIMENS, ROCK)
    - Multiple records (WELSPECS, PVTO)
    - Grid data (PORO, PERMX)
    
    Attributes:
        name: The keyword name (uppercase).
        records: List of data records.
        is_flag: True if keyword has no data.
        grid_data: For per-cell keywords, flattened cell values.
        comments: Comments associated with this keyword.
    """
    name: str
    records: list[Record] = field(default_factory=list)
    is_flag: bool = False
    grid_data: list[Value] | None = None
    comments: list[Comment] = field(default_factory=list)
    
    def __post_init__(self):
        self.name = self.name.upper()
    
    def add_record(self, *values: Value, comment: str | None = None) -> Record:
        """Add a new record with the given values.
        
        Args:
            *values: Values for the record.
            comment: Optional inline comment.
        
        Returns:
            The created Record.
        """
        record = Record(list(values), comment)
        self.records.append(record)
        return record
    
    def to_string(self) -> str:
        """Convert keyword to ECLIPSE syntax."""
        lines = []
        
        # Add preceding comments
        for comment in self.comments:
            lines.append(comment.to_string())
        
        # Keyword name
        lines.append(self.name)
        
        if self.is_flag:
            # Flag keyword - just the name
            pass
        elif self.grid_data is not None:
            # Grid data keyword
            lines.append(self._format_grid_data())
        elif self.records:
            # Standard records
            for record in self.records:
                lines.append(record.to_string())
            # Add empty terminator if multiple records
            if len(self.records) > 1 or self.name in _MULTI_RECORD_KEYWORDS:
                lines.append("/")
        
        return "\n".join(lines)
    
    def _format_grid_data(self) -> str:
        """Format grid data with repeat notation."""
        if not self.grid_data:
            return "/"
        
        # Use repeat notation for consecutive identical values
        parts = []
        i = 0
        while i < len(self.grid_data):
            value = self.grid_data[i]
            count = 1
            while i + count < len(self.grid_data) and self.grid_data[i + count] == value:
                count += 1
            
            if count > 1:
                parts.append(f"{count}*{value}")
            else:
                parts.append(str(value))
            i += count
        
        return " ".join(parts) + " /"


# Keywords that always have multiple records terminated by empty /
_MULTI_RECORD_KEYWORDS = {
    "WELSPECS", "COMPDAT", "WCONPROD", "WCONINJE", "WCONHIST", "WCONINJH",
    "WELOPEN", "WELTARG", "DATES", "PVTO", "PVTG", "SWOF", "SGOF",
    "EQUIL", "RSVD", "RVVD", "PBVD",
}


@dataclass
class Section:
    """A major section of the deck (RUNSPEC, GRID, etc.).
    
    Attributes:
        name: Section name (RUNSPEC, GRID, PROPS, etc.).
        keywords: Keywords in this section.
        comments: Section-level comments.
    """
    name: str
    keywords: list[Keyword] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    
    def __post_init__(self):
        self.name = self.name.upper()
    
    def __iter__(self) -> Iterator[Keyword]:
        return iter(self.keywords)
    
    def add_keyword(self, keyword: Keyword | str) -> Keyword:
        """Add a keyword to the section.
        
        Args:
            keyword: Keyword object or name string.
        
        Returns:
            The added Keyword.
        """
        if isinstance(keyword, str):
            keyword = Keyword(keyword, is_flag=True)
        self.keywords.append(keyword)
        return keyword
    
    def get_keyword(self, name: str) -> Keyword | None:
        """Find a keyword by name.
        
        Args:
            name: Keyword name to find.
        
        Returns:
            The Keyword or None if not found.
        """
        name = name.upper()
        for kw in self.keywords:
            if kw.name == name:
                return kw
        return None
    
    def to_string(self) -> str:
        """Convert section to ECLIPSE syntax."""
        lines = []
        
        # Section comments
        for comment in self.comments:
            lines.append(comment.to_string())
        
        # Section header
        lines.append(self.name)
        lines.append("")  # Blank line after section name
        
        # Keywords
        for keyword in self.keywords:
            lines.append(keyword.to_string())
            lines.append("")  # Blank line between keywords
        
        return "\n".join(lines)


@dataclass
class Deck:
    """Complete ECLIPSE simulation deck.
    
    The top-level AST node containing all sections.
    
    Attributes:
        sections: Ordered list of sections.
        title: Deck title (from TITLE keyword).
        comments: File-level comments.
    """
    sections: list[Section] = field(default_factory=list)
    title: str = ""
    comments: list[Comment] = field(default_factory=list)
    
    # Standard section order
    SECTION_ORDER = [
        "RUNSPEC", "GRID", "EDIT", "PROPS", 
        "REGIONS", "SOLUTION", "SUMMARY", "SCHEDULE"
    ]
    
    def __iter__(self) -> Iterator[Section]:
        return iter(self.sections)
    
    def add_section(self, section: Section | str) -> Section:
        """Add a section to the deck.
        
        Args:
            section: Section object or name string.
        
        Returns:
            The added Section.
        """
        if isinstance(section, str):
            section = Section(section)
        self.sections.append(section)
        return section
    
    def get_section(self, name: str) -> Section | None:
        """Find a section by name.
        
        Args:
            name: Section name to find.
        
        Returns:
            The Section or None if not found.
        """
        name = name.upper()
        for section in self.sections:
            if section.name == name:
                return section
        return None
    
    def get_keyword(self, name: str) -> Keyword | None:
        """Find a keyword anywhere in the deck.
        
        Args:
            name: Keyword name to find.
        
        Returns:
            The first matching Keyword or None.
        """
        for section in self.sections:
            kw = section.get_keyword(name)
            if kw:
                return kw
        return None
    
    def to_string(self) -> str:
        """Convert entire deck to ECLIPSE syntax.
        
        Returns:
            Complete deck as string.
        """
        lines = []
        
        # File-level comments
        for comment in self.comments:
            lines.append(comment.to_string())
        if self.comments:
            lines.append("")
        
        # Sections in order
        for section in self.sections:
            lines.append(section.to_string())
        
        # End marker
        lines.append("END")
        lines.append("")
        
        return "\n".join(lines)
    
    def validate(self) -> list[str]:
        """Validate deck structure.
        
        Returns:
            List of validation error messages.
        """
        errors = []
        
        # Check required sections
        required = {"RUNSPEC", "GRID", "PROPS", "SOLUTION", "SCHEDULE"}
        present = {s.name for s in self.sections}
        missing = required - present
        if missing:
            errors.append(f"Missing required sections: {', '.join(sorted(missing))}")
        
        # Check section order
        section_names = [s.name for s in self.sections]
        expected_order = [s for s in self.SECTION_ORDER if s in section_names]
        if section_names != expected_order:
            errors.append(f"Sections out of order. Expected: {expected_order}")
        
        # Check RUNSPEC requirements
        runspec = self.get_section("RUNSPEC")
        if runspec:
            if not runspec.get_keyword("DIMENS"):
                errors.append("RUNSPEC missing DIMENS keyword")
            
            # Check for at least one phase
            phases = {"OIL", "WATER", "GAS"}
            has_phase = any(runspec.get_keyword(p) for p in phases)
            if not has_phase:
                errors.append("RUNSPEC must specify at least one phase (OIL/WATER/GAS)")
        
        return errors


# Convenience constructors
def make_dimens(nx: int, ny: int, nz: int) -> Keyword:
    """Create a DIMENS keyword."""
    kw = Keyword("DIMENS")
    kw.add_record(nx, ny, nz)
    return kw


def make_welspecs(
    name: str, 
    group: str, 
    i: int, 
    j: int, 
    ref_depth: float,
    phase: str = "OIL"
) -> Keyword:
    """Create a WELSPECS keyword for a single well."""
    kw = Keyword("WELSPECS")
    kw.add_record(name, group, i, j, ref_depth, phase)
    return kw


def make_wconprod(
    name: str,
    status: str = "OPEN",
    control: str = "ORAT",
    orat: float | None = None,
    wrat: float | None = None,
    grat: float | None = None,
    lrat: float | None = None,
    resv: float | None = None,
    bhp: float | None = None
) -> Keyword:
    """Create a WCONPROD keyword for a single well."""
    kw = Keyword("WCONPROD")
    kw.add_record(name, status, control, orat, wrat, grat, lrat, resv, bhp)
    return kw


__all__ = [
    "NodeType",
    "Value",
    "Comment",
    "Record",
    "Keyword",
    "Section",
    "Deck",
    "make_dimens",
    "make_welspecs",
    "make_wconprod",
]