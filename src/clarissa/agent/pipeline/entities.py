"""Entity Extraction Stage Implementation.

Extracts structured entities (wells, rates, dates, etc.) from natural language,
guided by the recognized intent.

Usage:
    from clarissa.agent.pipeline.entities import EntityExtractor
    
    extractor = EntityExtractor()
    result = extractor.extract(
        "Set well PROD-01 rate to 500 bbl/day",
        intent="SET_RATE"
    )
    
    # result.data["entities"] = {
    #     "well_name": "PROD-01",
    #     "rate_value": 500.0,
    #     "rate_unit": "BBL/DAY"
    # }
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from clarissa.agent.pipeline.protocols import EntityExtractor as EntityExtractorProtocol
from clarissa.agent.pipeline.protocols import StageResult


# Load taxonomy for entity definitions
TAXONOMY_PATH = Path(__file__).parent.parent / "intents" / "taxonomy.json"


def load_taxonomy() -> dict:
    """Load intent taxonomy from JSON file."""
    with open(TAXONOMY_PATH) as f:
        return json.load(f)


# =============================================================================
# Unit Conversion Utilities
# =============================================================================

@dataclass
class RateValue:
    """Represents a rate with value and unit."""
    value: float
    unit: str
    
    # Standard unit conversions to STB/DAY for oil, BBL/DAY for water
    RATE_CONVERSIONS = {
        "STB/DAY": 1.0,
        "STB/D": 1.0,
        "BBL/DAY": 1.0,
        "BBL/D": 1.0,
        "MSCF/DAY": 1.0,  # Keep gas in MSCF
        "MSCF/D": 1.0,
        "MMSCF/DAY": 1000.0,  # Convert to MSCF
        "MMSCF/D": 1000.0,
        "M3/DAY": 6.2898,  # m³ to bbl
        "M3/D": 6.2898,
    }
    
    def to_standard(self) -> "RateValue":
        """Convert to standard unit."""
        unit_upper = self.unit.upper().replace(" ", "").replace("BARREL", "BBL")
        unit_upper = unit_upper.replace("PERDAY", "/DAY").replace("/DAY", "/DAY")
        
        factor = self.RATE_CONVERSIONS.get(unit_upper, 1.0)
        
        # Determine standard unit based on original
        if "SCF" in unit_upper:
            std_unit = "MSCF/DAY"
        else:
            std_unit = "STB/DAY"
        
        return RateValue(value=self.value * factor, unit=std_unit)


@dataclass
class PressureValue:
    """Represents a pressure with value and unit."""
    value: float
    unit: str
    
    # Standard conversions to PSIA
    PRESSURE_CONVERSIONS = {
        "PSI": 1.0,
        "PSIA": 1.0,
        "PSIG": 1.0,  # Would need reference pressure for exact conversion
        "BAR": 14.5038,
        "BARA": 14.5038,
        "KPA": 0.145038,
        "MPA": 145.038,
        "ATM": 14.696,
    }
    
    def to_standard(self) -> "PressureValue":
        """Convert to PSIA."""
        unit_upper = self.unit.upper()
        factor = self.PRESSURE_CONVERSIONS.get(unit_upper, 1.0)
        return PressureValue(value=self.value * factor, unit="PSIA")


# =============================================================================
# Entity Patterns
# =============================================================================

# Well name patterns - alphanumeric with hyphens/underscores
WELL_NAME_PATTERN = re.compile(
    r'\b([A-Z][A-Z0-9]*[-_]?[A-Z0-9]+|[A-Z]{1,4}[-_]?\d+)\b',
    re.IGNORECASE
)

# Group name patterns - similar to well names but also supports FIELD, G1, etc.
GROUP_NAME_PATTERN = re.compile(
    r'\b(?:group\s+)?([A-Z][A-Z0-9]*[-_]?[A-Z0-9]*|FIELD[-_]?[A-Z0-9]*)\b',
    re.IGNORECASE
)

# Rate patterns
RATE_PATTERN = re.compile(
    r'(\d+(?:[.,]\d+)?)\s*'  # Number (with optional decimal)
    r'(stb|bbl|barrels?|mscf|mmscf|m3|m³)\s*'  # Volume unit
    r'(?:per\s*|/)?\s*'  # Separator
    r'(day|d)\b',  # Time unit
    re.IGNORECASE
)

# Pressure patterns
PRESSURE_PATTERN = re.compile(
    r'(\d+(?:[.,]\d+)?)\s*'  # Number
    r'(psi|psia|psig|bar|bara|kpa|mpa|atm)\b',  # Pressure unit
    re.IGNORECASE
)

# Date patterns
DATE_ISO_PATTERN = re.compile(r'\b(\d{4})-(\d{2})-(\d{2})\b')
DATE_MONTH_YEAR_PATTERN = re.compile(
    r'\b(january|february|march|april|may|june|july|august|september|october|november|december)'
    r'\s+(\d{4})\b',
    re.IGNORECASE
)
DATE_MONTH_DAY_PATTERN = re.compile(
    r'\b(january|february|march|april|may|june|july|august|september|october|november|december)'
    r'\s+(\d{1,2})(?:st|nd|rd|th)?\b',
    re.IGNORECASE
)

# Duration patterns
DURATION_PATTERN = re.compile(
    r'(\d+)\s*(day|week|month|year)s?\b',
    re.IGNORECASE
)

# Fluid/Phase patterns
FLUID_PATTERN = re.compile(
    r'\b(oil|water|gas|liquid)\b',
    re.IGNORECASE
)

# Well type patterns
WELL_TYPE_PATTERN = re.compile(
    r'\b(producer|injector|observation|prod|inj)\b',
    re.IGNORECASE
)

# Grid location patterns
GRID_LOCATION_PATTERN = re.compile(
    r'\b(?:i|I)\s*[=:]?\s*(\d+)\s*[,]?\s*(?:j|J)\s*[=:]?\s*(\d+)\b'
)


# Month name to number mapping
MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12
}


# =============================================================================
# Entity Extractor Implementation
# =============================================================================

@dataclass
class ExtractedEntity:
    """Represents an extracted entity with metadata."""
    name: str
    value: Any
    raw_text: str
    start: int
    end: int
    confidence: float = 1.0


class RuleBasedEntityExtractor:
    """Rule-based entity extraction using regex patterns.
    
    Extracts entities based on the intent context, ensuring required
    entities are present and validating against taxonomy definitions.
    """
    
    def __init__(self, confidence_threshold: float = 0.7):
        """Initialize extractor.
        
        Args:
            confidence_threshold: Minimum confidence for success.
        """
        self.taxonomy = load_taxonomy()
        self.confidence_threshold = confidence_threshold
        
        # Map intents to required/optional entities
        self._build_intent_entity_map()
    
    def _build_intent_entity_map(self) -> None:
        """Build mapping of intents to their required/optional entities."""
        self.intent_entities = {}
        
        for cat_data in self.taxonomy["categories"].values():
            for intent_name, intent_data in cat_data["intents"].items():
                self.intent_entities[intent_name] = {
                    "required": intent_data.get("required_entities", []),
                    "optional": intent_data.get("optional_entities", []),
                }
    
    def _extract_well_names(self, text: str) -> list[ExtractedEntity]:
        """Extract well names from text."""
        entities = []
        
        # Common non-well words to exclude
        excluded = {"set", "get", "run", "the", "and", "for", "all", "day", "oil", "open", "shut", "show", "add", "new", "close", "stop", "start", 
                   "gas", "bhp", "thp", "psi", "bar", "stb", "bbl", "jan", "feb",
                   "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"}
        
        for match in WELL_NAME_PATTERN.finditer(text):
            name = match.group(1).upper()
            if name.lower() not in excluded and len(name) >= 2:
                entities.append(ExtractedEntity(
                    name="well_name",
                    value=name,
                    raw_text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9 if "-" in name or "_" in name else 0.75
                ))
        
        return entities
    
    def _extract_group_names(self, text: str) -> list[ExtractedEntity]:
        """Extract group names from text."""
        entities = []
        
        # Look for explicit "group X" patterns
        group_explicit = re.finditer(r'\bgroup\s+([A-Z][A-Z0-9_-]*)\b', text, re.IGNORECASE)
        for match in group_explicit:
            entities.append(ExtractedEntity(
                name="group_name",
                value=match.group(1).upper(),
                confidence=0.95,
                start=match.start(1),
                end=match.end(1),
                raw_text=match.group(0)
            ))
        
        # Look for FIELD_X, G1, etc. patterns when not already captured
        for match in GROUP_NAME_PATTERN.finditer(text):
            name = match.group(1).upper()
            # Filter out well-like names and common words
            if name.startswith(("FIELD", "PLATFORM", "REGION")) or (name.startswith("G") and len(name) <= 3):
                if name not in {"GAS", "GET", "GO", "GOC", "GOR"}:
                    if not any(e.value == name for e in entities):
                        entities.append(ExtractedEntity(
                            name="group_name",
                            value=name,
                            confidence=0.8,
                            start=match.start(1),
                            end=match.end(1),
                            raw_text=match.group(0)
                        ))
        
        return entities


    def _extract_rates(self, text: str) -> list[ExtractedEntity]:
        """Extract rate values from text."""
        entities = []
        
        for match in RATE_PATTERN.finditer(text):
            value_str = match.group(1).replace(",", ".")
            value = float(value_str)
            volume_unit = match.group(2).upper()
            time_unit = match.group(3).upper()
            
            # Normalize unit
            unit = f"{volume_unit}/{time_unit}"
            unit = unit.replace("BARREL", "BBL").replace("D", "DAY")
            
            rate = RateValue(value=value, unit=unit)
            
            entities.append(ExtractedEntity(
                name="rate_value",
                value=rate.value,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))
            entities.append(ExtractedEntity(
                name="rate_unit",
                value=rate.unit,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))
        
        return entities
    
    def _extract_pressures(self, text: str) -> list[ExtractedEntity]:
        """Extract pressure values from text."""
        entities = []
        
        for match in PRESSURE_PATTERN.finditer(text):
            value_str = match.group(1).replace(",", ".")
            value = float(value_str)
            unit = match.group(2).upper()
            
            pressure = PressureValue(value=value, unit=unit)
            
            entities.append(ExtractedEntity(
                name="pressure_value",
                value=pressure.value,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))
            entities.append(ExtractedEntity(
                name="pressure_unit",
                value=pressure.unit,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))
            
            # Try to determine pressure type from context
            text_lower = text.lower()
            if "bhp" in text_lower or "bottomhole" in text_lower:
                entities.append(ExtractedEntity(
                    name="pressure_type",
                    value="BHP",
                    raw_text="bhp",
                    start=0,
                    end=0,
                    confidence=0.9
                ))
            elif "thp" in text_lower or "tubing" in text_lower:
                entities.append(ExtractedEntity(
                    name="pressure_type",
                    value="THP",
                    raw_text="thp",
                    start=0,
                    end=0,
                    confidence=0.9
                ))
        
        return entities
    
    def _extract_dates(self, text: str) -> list[ExtractedEntity]:
        """Extract date values from text."""
        entities = []
        current_year = datetime.now().year
        
        # ISO format: 2025-01-15
        for match in DATE_ISO_PATTERN.finditer(text):
            date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            entities.append(ExtractedEntity(
                name="target_date",
                value=date_str,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.98
            ))
        
        # Month Year: January 2025
        for match in DATE_MONTH_YEAR_PATTERN.finditer(text):
            month = MONTH_MAP[match.group(1).lower()]
            year = int(match.group(2))
            date_str = f"{year}-{month:02d}-01"
            entities.append(ExtractedEntity(
                name="target_date",
                value=date_str,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.90
            ))
        
        # Month Day: January 15 (assume current/next year)
        for match in DATE_MONTH_DAY_PATTERN.finditer(text):
            month = MONTH_MAP[match.group(1).lower()]
            day = int(match.group(2))
            # Assume current year, or next year if month has passed
            year = current_year
            date_str = f"{year}-{month:02d}-{day:02d}"
            entities.append(ExtractedEntity(
                name="target_date",
                value=date_str,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.80
            ))
        
        return entities
    
    def _extract_durations(self, text: str) -> list[ExtractedEntity]:
        """Extract duration/timestep values."""
        entities = []
        
        for match in DURATION_PATTERN.finditer(text):
            value = int(match.group(1))
            unit = match.group(2).upper()
            
            entities.append(ExtractedEntity(
                name="timestep_size",
                value=value,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.90
            ))
            entities.append(ExtractedEntity(
                name="timestep_unit",
                value=unit,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.90
            ))
        
        return entities
    
    def _extract_fluids(self, text: str) -> list[ExtractedEntity]:
        """Extract fluid/phase references."""
        entities = []
        
        for match in FLUID_PATTERN.finditer(text):
            fluid = match.group(1).upper()
            entities.append(ExtractedEntity(
                name="phase",
                value=fluid,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))
        
        return entities
    
    def _extract_well_types(self, text: str) -> list[ExtractedEntity]:
        """Extract well type references."""
        entities = []
        
        for match in WELL_TYPE_PATTERN.finditer(text):
            wtype = match.group(1).upper()
            # Normalize abbreviations
            if wtype in ("PROD",):
                wtype = "PRODUCER"
            elif wtype in ("INJ",):
                wtype = "INJECTOR"
            
            entities.append(ExtractedEntity(
                name="well_type",
                value=wtype,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.90
            ))
        
        return entities
    
    def _extract_grid_locations(self, text: str) -> list[ExtractedEntity]:
        """Extract grid I,J locations."""
        entities = []
        
        for match in GRID_LOCATION_PATTERN.finditer(text):
            i_val = int(match.group(1))
            j_val = int(match.group(2))
            
            entities.append(ExtractedEntity(
                name="location_i",
                value=i_val,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.85
            ))
            entities.append(ExtractedEntity(
                name="location_j",
                value=j_val,
                raw_text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=0.85
            ))
        
        return entities
    
    def extract(self, text: str, intent: str) -> StageResult:
        """Extract entities from text given an intent.
        
        Args:
            text: Natural language input.
            intent: Recognized intent identifier.
        
        Returns:
            StageResult with extracted entities.
        """
        if not text.strip():
            return StageResult.failure(["Empty input text"])
        
        if intent not in self.intent_entities:
            return StageResult.failure([f"Unknown intent: {intent}"])
        
        # Extract all possible entities
        all_entities: list[ExtractedEntity] = []
        all_entities.extend(self._extract_well_names(text))
        all_entities.extend(self._extract_group_names(text))
        all_entities.extend(self._extract_rates(text))
        all_entities.extend(self._extract_pressures(text))
        all_entities.extend(self._extract_dates(text))
        all_entities.extend(self._extract_durations(text))
        all_entities.extend(self._extract_fluids(text))
        all_entities.extend(self._extract_well_types(text))
        all_entities.extend(self._extract_grid_locations(text))
        
        # Build entity dict (keep highest confidence for duplicates)
        entities: dict[str, Any] = {}
        entity_meta: dict[str, ExtractedEntity] = {}
        
        for entity in all_entities:
            if entity.name not in entities or entity.confidence > entity_meta[entity.name].confidence:
                entities[entity.name] = entity.value
                entity_meta[entity.name] = entity
        
        # Check required entities
        required = self.intent_entities[intent]["required"]
        missing = [r for r in required if r not in entities]
        
        # Check optional entities
        optional = self.intent_entities[intent]["optional"]
        found_optional = [o for o in optional if o in entities]
        
        # Calculate overall confidence
        if not all_entities:
            confidence = 0.3
        else:
            confidences = [e.confidence for e in entity_meta.values()]
            confidence = sum(confidences) / len(confidences)
            
            # Penalize missing required entities
            if missing:
                confidence *= (1 - 0.2 * len(missing))
        
        # Build result
        result_data = {
            "entities": entities,
            "missing": missing,
            "ambiguous": [],  # TODO: detect ambiguous entities
        }
        
        if missing:
            return StageResult(
                success=False,
                confidence=confidence,
                data=result_data,
                errors=[f"Missing required entities: {', '.join(missing)}"],
                metadata={
                    "extractor": "rule_based",
                    "entity_count": len(entities),
                    "required": required,
                    "optional": optional,
                }
            )
        
        if confidence < self.confidence_threshold:
            return StageResult.low_confidence(
                data=result_data,
                confidence=confidence,
                metadata={"extractor": "rule_based"}
            )
        
        return StageResult(
            success=True,
            confidence=confidence,
            data=result_data,
            metadata={
                "extractor": "rule_based",
                "entity_count": len(entities),
            }
        )


# Alias for protocol compliance
EntityExtractor = RuleBasedEntityExtractor


__all__ = [
    "EntityExtractor",
    "RuleBasedEntityExtractor",
    "ExtractedEntity",
    "RateValue",
    "PressureValue",
]