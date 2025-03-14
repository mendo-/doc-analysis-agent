from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class Document:
    """Represents a document to be analyzed."""

    content: str
    metadata: Dict[str, Any]


@dataclass
class DocumentSummary:
    """Represents a summary of a document."""

    content: str
    key_points: List[str] = field(default_factory=list)
    confidence_score: float = 1.0


@dataclass
class AnalysisResult:
    """Represents the result of document analysis."""

    document_type: str
    key_entities: List[str]
    monetary_values: List[float]
    dates: List[str]
    key_info: Dict[str, Any]
    related_docs: List[str] = field(default_factory=list)
    changes_detected: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 1.0


@dataclass
class AnalysisConfig:
    """Configuration for document analysis."""

    detail_level: str = "standard"  # One of: brief, standard, detailed
    extract_entities: bool = True
    extract_values: bool = True
    extract_dates: bool = True
    custom_extractors: List[str] = field(default_factory=list)
    temperature: float = 0.7
