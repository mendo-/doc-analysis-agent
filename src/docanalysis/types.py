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
    reference_id: Optional[str] = None
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
    extract_relationships: bool = True
    custom_extractors: List[str] = field(default_factory=list)
    temperature: float = 0.7

    # Document type specific configurations
    document_types: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "contract": {
                "key_fields": [
                    "parties",
                    "value",
                    "duration",
                    "deliverables",
                    "services",
                ],
                "relationships": ["amendments", "reports", "related_agreements"],
            },
            "amendment": {
                "key_fields": ["reference_id", "changes", "effective_date"],
                "relationships": ["original_contract", "other_amendments"],
            },
            "report": {
                "key_fields": [
                    "metrics",
                    "accomplishments",
                    "challenges",
                    "next_steps",
                ],
                "relationships": ["referenced_contract", "previous_reports"],
            },
        }
    )
