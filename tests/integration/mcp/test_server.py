"""Integration tests for MCP document analysis server."""

import os
import pytest
from typing import Dict, Any

from docanalysis.mcp.server import MCPDocumentAnalysisServer
from docanalysis.core.analysis import AnalysisResult, DocumentSummary

# Skip integration tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set"
)


@pytest.fixture
async def mcp_server():
    """Create and initialize an MCP document analysis server."""
    server = MCPDocumentAnalysisServer()
    await server.initialize()
    return server


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


async def test_mcp_server_initialization(mcp_server):
    """Test that the MCP server initializes correctly."""
    # Server should already be initialized by the fixture
    assert mcp_server._initialized
    assert mcp_server._app is not None
    assert mcp_server._agent is not None
    assert mcp_server._analyzer is not None


async def test_document_analysis_capability(mcp_server, sample_document):
    """Test the document analysis capability of the MCP server."""
    result = await mcp_server.analyze_document(sample_document)

    # Verify result type
    assert isinstance(result, AnalysisResult)

    # Verify basic document analysis
    assert result.document_type == "contract"
    assert any("TechCorp" in entity for entity in result.key_entities)
    assert any("Global" in entity for entity in result.key_entities)
    assert "2024-03-14" in result.dates
    assert result.source_doc_id == "TECH-2024-001"


async def test_document_summary_capability(mcp_server, sample_document):
    """Test the document summarization capability of the MCP server."""
    # Test different detail levels
    detail_levels = ["brief", "standard", "detailed"]

    for level in detail_levels:
        summary = await mcp_server.summarize_document(sample_document, level)

        # Verify result type
        assert isinstance(summary, DocumentSummary)

        # Verify summary properties
        assert summary.detail_level == level
        assert len(summary.key_points) > 0
        assert summary.source_doc_id == "TECH-2024-001"

        # Brief summaries should be shorter than standard ones
        if level == "brief":
            assert len(summary.content) < len(sample_document["content"]) / 2


async def test_info_extraction_capability(mcp_server, sample_document):
    """Test the information extraction capability of the MCP server."""
    info_types = ["parties", "dates", "locations"]
    result = await mcp_server.extract_info(sample_document, info_types)

    # Verify result structure
    assert isinstance(result, dict)
    assert all(info_type in result for info_type in info_types)

    # Verify extracted information
    assert any("TechCorp" in str(party) for party in result["parties"])
    assert any("Global" in str(party) for party in result["parties"])
    assert "2024-03-14" in str(result["dates"])
    assert any("San Francisco" in str(loc) for loc in result["locations"])
    assert any("New York" in str(loc) for loc in result["locations"])
