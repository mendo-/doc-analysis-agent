"""Integration tests for document analysis functionality."""

import pytest
from pathlib import Path

from docanalysis.core.types import Document


async def test_error_handling(mcp_server):
    """Test error handling with malformed input."""
    # Test with empty document
    empty_doc = Document(content="", metadata={"type": "unknown"})
    result = await mcp_server.analyze_document(empty_doc.model_dump())
    assert result["document_type"] == "unknown"
    assert len(result["key_entities"]) == 0
    assert result["confidence_score"] < 0.5

    # Test with very short document
    short_doc = Document(content="Hello world", metadata={"type": "unknown"})
    result = await mcp_server.analyze_document(short_doc.model_dump())
    assert result["document_type"] == "unknown"
    assert isinstance(result["key_info"], dict)
    assert result["confidence_score"] < 0.8


async def test_information_extraction(mcp_server, test_pdfs):
    """Test extracting specific information types from documents."""
    # Load the contract PDF
    with open(test_pdfs["contract"], "rb") as f:
        contract_bytes = f.read()

    contract_doc = Document(
        content={"type": "pdf", "data": contract_bytes.hex()},
        metadata={"type": "contract", "title": "Service Agreement"},
    )

    # Test extraction of standard information types
    info_types = ["parties", "financial_terms", "timeline", "locations"]
    result = await mcp_server.extract_info(
        document=contract_doc.model_dump(), info_types=info_types
    )

    # Verify parties information
    assert "parties" in result
    assert len(result["parties"]) > 0
    assert any("TechCorp" in party["name"] for party in result["parties"])
    assert any("DataCo" in party["name"] for party in result["parties"])

    # Verify financial terms
    assert "financial_terms" in result
    assert "total_value" in result["financial_terms"]
    assert isinstance(result["financial_terms"]["total_value"], (int, float))
    assert result["financial_terms"]["total_value"] == 50000

    # Verify timeline information
    assert "timeline" in result
    assert "start_date" in result["timeline"]
    assert "duration" in result["timeline"]
    assert "2024-01-01" in result["timeline"]["start_date"]
    assert "12 months" in result["timeline"]["duration"]

    # Test extraction of custom information types
    custom_types = ["services", "deliverables", "contact_info"]
    custom_result = await mcp_server.extract_info(
        document=contract_doc.model_dump(), info_types=custom_types
    )

    # Verify custom information types are present
    assert all(t in custom_result for t in custom_types)
    assert "AI Model Development" in str(custom_result["services"])

    # Test error handling with empty document
    empty_doc = Document(content="", metadata={"type": "unknown"})
    empty_result = await mcp_server.extract_info(
        document=empty_doc.model_dump(), info_types=info_types
    )
    assert all(info_type in empty_result for info_type in info_types)
    assert all(
        isinstance(empty_result[info_type], (dict, list)) for info_type in info_types
    )
