"""Core data models for Kast dubbing cast extractor."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class DialogueLine:
    """Represents a single parsed line of dialogue in a dubbing script."""

    speaker: str
    text: str
    timecode: Optional[str] = None
    page: int = 1
    paragraph_index: int = 0


@dataclass
class CharacterStats:
    """Aggregated statistics for a single character in the script."""

    name: str
    first_seen_order: int
    line_count: int = 0
    pages: Set[int] = field(default_factory=set)
    notes: str = ""

    def add_line(self, page: int) -> None:
        """Record a dialogue line spoken on the given page."""
        self.line_count += 1
        self.pages.add(page)

    @property
    def formatted_pages(self) -> str:
        """Return comma-separated sorted list of page numbers."""
        return ", ".join(str(p) for p in sorted(self.pages))


@dataclass
class CastExtractionResult:
    """Overall cast extraction result containing all characters and metadata."""

    characters: List[CharacterStats]
    metadata: Dict[str, str] = field(default_factory=dict)
    total_lines: int = 0
    total_pages: int = 0
