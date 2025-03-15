"""Unit tests for core document analysis functionality."""

import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

from docanalysis.core.analysis import DocumentAnalyzer, AnalysisResult, DocumentSummary


class MockLLMService:
    """Mock LLM service for testing."""

    def __init__(self):
        """Initialize with mock responses."""
        self.generate_str = AsyncMock()
        self._setup_mock_responses()

    def _setup_mock_responses(self):
        """Set up mock responses for different document analysis requests."""

        def mock_analysis_response(*args, **kwargs):
            return """{
                "document_type": "contract",
                "key_entities": ["TechCorp Solutions Inc.", "Global Enterprises Ltd."],
                "monetary_values": [],
                "dates": ["2024-03-14"],
                "key_info": {
                    "parties": {
                        "provider": "TechCorp Solutions Inc.",
                        "client": "Global Enterprises Ltd."
                    },
                    "locations": ["San Francisco, CA", "New York, NY"]
                },
                "confidence_score": 0.95
            }"""

        def mock_summary_response(*args, **kwargs):
            return """{
                "content": "Service agreement between TechCorp Solutions Inc. and Global Enterprises Ltd.",
                "key_points": [
                    "Agreement dated March 14, 2024",
                    "Between TechCorp (Provider) and Global Enterprises (Client)",
                    "Located in San Francisco and New York respectively"
                ],
                "detail_level": "brief",
                "word_count": 15
            }"""

        def mock_info_response(*args, **kwargs):
            return """{
                "parties": [
                    {"name": "TechCorp Solutions Inc.", "role": "Provider"},
                    {"name": "Global Enterprises Ltd.", "role": "Client"}
                ],
                "dates": ["2024-03-14"],
                "locations": ["San Francisco, CA", "New York, NY"]
            }"""

        # Set up different responses based on the prompt content
        self.generate_str.side_effect = lambda prompt: (
            mock_analysis_response()
            if "Analyze" in prompt
            else (
                mock_summary_response()
                if "Generate" in prompt
                else mock_info_response()
            )
        )


@pytest.fixture
def mock_llm():
    """Create a mock LLM service."""
    return MockLLMService()


@pytest.fixture
def document_analyzer(mock_llm):
    """Create a document analyzer with mock LLM."""
    return DocumentAnalyzer(mock_llm)


@pytest.fixture
def sample_document() -> Dict[str, Any]:
    """A sample document for testing."""
    return {
        "content": """SERVICE AGREEMENT
        
        This Agreement is made on March 14, 2024, between:
        
        TechCorp Solutions Inc. ("Provider")
        123 Tech Lane
        San Francisco, CA 94105
        
        and
        
        Global Enterprises Ltd. ("Client")
        456 Business Ave
        New York, NY 10001""",
        "metadata": {
            "type": "contract",
            "title": "Service Agreement",
            "date": "2024-03-14",
            "id": "TECH-2024-001",
        },
    }


async def test_document_analysis(document_analyzer, sample_document):
    """Test document analysis with mock LLM."""
    result = await document_analyzer.analyze_document(
        content=sample_document["content"], metadata=sample_document["metadata"]
    )

    # Verify result type and structure
    assert isinstance(result, AnalysisResult)
    assert result.document_type == "contract"
    assert len(result.key_entities) == 2
    assert "TechCorp Solutions Inc." in result.key_entities
    assert "Global Enterprises Ltd." in result.key_entities
    assert "2024-03-14" in result.dates
    assert result.confidence_score == 0.95


async def test_document_summary(document_analyzer, sample_document):
    """Test document summarization with mock LLM."""
    summary = await document_analyzer.summarize_document(
        content=sample_document["content"],
        metadata=sample_document["metadata"],
        detail_level="brief",
    )

    # Verify summary structure
    assert isinstance(summary, DocumentSummary)
    assert summary.detail_level == "brief"
    assert len(summary.key_points) == 3
    assert any("TechCorp" in point for point in summary.key_points)
    assert any("Global Enterprises" in point for point in summary.key_points)


async def test_info_extraction(document_analyzer, sample_document):
    """Test information extraction with mock LLM."""
    info_types = ["parties", "dates", "locations"]
    result = await document_analyzer.extract_info(
        content=sample_document["content"],
        metadata=sample_document["metadata"],
        info_types=info_types,
    )

    # Verify extracted information
    assert isinstance(result, dict)
    assert all(info_type in result for info_type in info_types)
    assert len(result["parties"]) == 2
    assert result["dates"] == ["2024-03-14"]
    assert len(result["locations"]) == 2
    assert "San Francisco, CA" in result["locations"]
    assert "New York, NY" in result["locations"]
