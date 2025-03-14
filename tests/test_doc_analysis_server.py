import pytest
from pathlib import Path
from typing import List, Dict
from mcp_agent.app import MCPApp

from src.docanalysis.server import DocumentAnalysisAgent
from src.docanalysis.types import Document, AnalysisResult, DocumentSummary


@pytest.fixture
async def doc_agent():
    app = MCPApp(name="test_docanalysis")
    async with app.run() as mcp_agent_app:
        agent = DocumentAnalysisAgent()
        await agent.initialize()
        yield agent


@pytest.fixture
def sample_document() -> Document:
    return Document(
        content="This is a sample contract between Company A and Company B. "
        "The contract value is $100,000. The duration is 12 months. "
        "Key deliverables include: software development, maintenance, and support.",
        metadata={
            "type": "contract",
            "title": "Service Agreement",
            "date": "2024-03-14",
        },
    )


async def test_agent_initialization(doc_agent: DocumentAnalysisAgent):
    """Test that the agent initializes correctly."""
    assert doc_agent.name == "doc_analyzer"
    assert "analyze documents" in doc_agent.instruction.lower()


async def test_document_analysis(
    doc_agent: DocumentAnalysisAgent, sample_document: Document
):
    """Test the main document analysis functionality."""
    result = await doc_agent.analyze_document(sample_document)

    assert isinstance(result, AnalysisResult)
    assert "contract" in result.document_type.lower()
    assert result.key_entities == ["Company A", "Company B"]
    assert result.monetary_values == [100000]
    assert result.dates == ["2024-03-14"]

    # Verify key information extraction
    assert result.key_info["contract_value"] == 100000
    assert "software development" in result.key_info.get("deliverables", "")


async def test_document_summary(
    doc_agent: DocumentAnalysisAgent, sample_document: Document
):
    """Test document summarization at different detail levels."""
    summary = await doc_agent.summarize_document(
        document=sample_document, detail_level="brief"
    )

    assert isinstance(summary, DocumentSummary)
    assert len(summary.content) < len(sample_document.content)
    assert "Company A" in summary.content
    assert "Company B" in summary.content
    assert "$100,000" in summary.content


async def test_cross_document_analysis(doc_agent: DocumentAnalysisAgent):
    """Test analysis across multiple related documents."""
    doc1 = Document(
        content="Initial contract value: $100,000",
        metadata={"type": "contract", "id": "001"},
    )
    doc2 = Document(
        content="Contract amendment: value increased to $150,000",
        metadata={"type": "amendment", "id": "001-A"},
    )

    results = await doc_agent.analyze_documents([doc1, doc2])

    assert len(results) == 2
    assert results[0].related_docs == ["001-A"]
    assert results[1].related_docs == ["001"]
    assert results[1].changes_detected.get("value_change") == 50000
