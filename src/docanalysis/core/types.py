"""Core type definitions for document analysis."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Document:
    """Represents a document with its content and metadata."""

    content: str
    metadata: Dict[str, Any]
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def model_dump(self) -> Dict[str, Any]:
        """Convert the document to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the document
        """
        result = {
            "content": self.content,
            "metadata": self.metadata,
        }
        if self.id:
            result["id"] = self.id
        if self.created_at:
            result["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            result["updated_at"] = self.updated_at.isoformat()
        return result


@dataclass
class DocumentSummary:
    """Summary of a document's content."""

    content: str
    key_points: List[str]
    detail_level: str  # "brief", "standard", or "detailed"
    word_count: int
    source_doc_id: Optional[str] = None

    def model_dump(self) -> Dict[str, Any]:
        """Convert the summary to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the summary
        """
        return {
            "content": self.content,
            "key_points": self.key_points,
            "detail_level": self.detail_level,
            "word_count": self.word_count,
            "source_doc_id": self.source_doc_id,
        }


@dataclass
class Entity:
    """Named entity found in a document."""

    name: str
    type: str  # e.g., "person", "organization", "location"
    context: Optional[str] = None
    confidence: float = 1.0


@dataclass
class MonetaryValue:
    """Monetary value found in a document."""

    amount: float
    currency: str
    context: Optional[str] = None
    confidence: float = 1.0


@dataclass
class DateReference:
    """Date reference found in a document."""

    date: datetime
    context: Optional[str] = None
    type: Optional[str] = None  # e.g., "effective_date", "expiry_date"
    confidence: float = 1.0


@dataclass
class AnalysisResult:
    """Results from document analysis."""

    document_type: str  # e.g., "contract", "invoice", "report"
    key_entities: List[Entity] = field(default_factory=list)
    monetary_values: List[MonetaryValue] = field(default_factory=list)
    dates: List[DateReference] = field(default_factory=list)
    key_info: Dict[str, Any] = field(default_factory=dict)
    reference_id: Optional[str] = None
    changes_detected: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_doc_id: Optional[str] = None

    def model_dump(self) -> Dict[str, Any]:
        """Convert the analysis result to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the analysis result
        """
        return {
            "document_type": self.document_type,
            "key_entities": [
                {
                    "name": e.name,
                    "type": e.type,
                    "context": e.context,
                    "confidence": e.confidence,
                }
                for e in self.key_entities
            ],
            "monetary_values": [
                {
                    "amount": v.amount,
                    "currency": v.currency,
                    "context": v.context,
                    "confidence": v.confidence,
                }
                for v in self.monetary_values
            ],
            "dates": [
                {
                    "date": d.date.isoformat(),
                    "context": d.context,
                    "type": d.type,
                    "confidence": d.confidence,
                }
                for d in self.dates
            ],
            "key_info": self.key_info,
            "reference_id": self.reference_id,
            "changes_detected": self.changes_detected,
            "confidence_score": self.confidence_score,
            "metadata": self.metadata,
            "source_doc_id": self.source_doc_id,
        }


class AnalysisConfig:
    """Configuration for document analysis."""

    document_types: Dict[str, Dict[str, List[str]]] = {
        "contract": {
            "key_fields": [
                "parties",
                "value",
                "duration",
                "services",
                "deliverables",
            ]
        },
        "amendment": {
            "key_fields": [
                "changes",
                "value_changes",
                "timeline_changes",
                "scope_changes",
            ]
        },
        "report": {
            "key_fields": [
                "metrics",
                "progress",
                "challenges",
                "next_steps",
            ]
        },
    }
