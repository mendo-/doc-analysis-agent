"""Integration tests for document relationships."""

import base64
import pytest
from pathlib import Path

from docanalysis.core.types import Document, AnalysisResult


async def read_pdf_as_base64(path: Path) -> str:
    """Read PDF file and encode as base64.

    Args:
        path: Path to PDF file

    Returns:
        str: Base64 encoded PDF content
    """
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


@pytest.mark.asyncio
async def test_document_relationships(mcp_server, test_pdfs):
    """Test analyzing relationships between documents.

    This test simulates a real-world scenario where:
    1. A contract is uploaded and analyzed
    2. An amendment referencing the contract is uploaded
    3. A progress report referencing both is uploaded
    4. An unrelated document is uploaded
    5. We verify that relationships are correctly identified
    """
    # 1. Upload and analyze the contract
    contract_b64 = await read_pdf_as_base64(test_pdfs["contract"])
    contract_doc = Document(
        content={"type": "pdf", "data": contract_b64},
        metadata={"type": "contract", "title": "Service Agreement"},
    )
    contract_result = await mcp_server.analyze_document(contract_doc.model_dump())
    assert contract_result["document_type"] == "contract"
    assert any(
        "TechCorp" in entity["name"] for entity in contract_result["key_entities"]
    )
    assert any(
        "$50,000" in str(value["amount"])
        for value in contract_result["monetary_values"]
    )

    # 2. Upload and analyze the amendment
    amendment_b64 = await read_pdf_as_base64(test_pdfs["amendment"])
    amendment_doc = Document(
        content={"type": "pdf", "data": amendment_b64},
        metadata={"type": "amendment", "title": "Contract Amendment"},
    )
    amendment_result = await mcp_server.analyze_document(amendment_doc.model_dump())
    assert amendment_result["document_type"] == "amendment"
    assert any(
        "$75,000" in str(value["amount"])
        for value in amendment_result["monetary_values"]
    )

    # 3. Upload and analyze the progress report
    report_b64 = await read_pdf_as_base64(test_pdfs["report"])
    report_doc = Document(
        content={"type": "pdf", "data": report_b64},
        metadata={"type": "report", "title": "Project Status Report"},
    )
    report_result = await mcp_server.analyze_document(report_doc.model_dump())
    assert report_result["document_type"] == "report"
    assert any(
        "$45,000" in str(value["amount"]) for value in report_result["monetary_values"]
    )

    # 4. Upload and analyze the unrelated document
    other_b64 = await read_pdf_as_base64(test_pdfs["other"])
    other_doc = Document(
        content={"type": "pdf", "data": other_b64},
        metadata={"type": "minutes", "title": "Meeting Minutes"},
    )
    other_result = await mcp_server.analyze_document(other_doc.model_dump())
    assert other_result["document_type"] == "minutes"

    # 5. Find relationships between documents
    # The amendment should be related to the contract
    amendment_relationships = await mcp_server.find_relationships(
        amendment_doc.model_dump()
    )
    assert any(
        rel["id"] == contract_result["source_doc_id"]
        for rel in amendment_relationships["related_docs"]
    )

    # The report should be related to both contract and amendment
    report_relationships = await mcp_server.find_relationships(report_doc.model_dump())
    related_ids = [rel["id"] for rel in report_relationships["related_docs"]]
    assert contract_result["source_doc_id"] in related_ids
    assert amendment_result["source_doc_id"] in related_ids

    # The unrelated document should not be related to any others
    other_relationships = await mcp_server.find_relationships(other_doc.model_dump())
    assert len(other_relationships["related_docs"]) == 0

    # Test finding similar documents
    similar_to_contract = await mcp_server.find_similar_documents(
        doc_id=contract_result["source_doc_id"]
    )
    assert any(
        doc["id"] == amendment_result["source_doc_id"]
        for doc in similar_to_contract["similar_docs"]
    )

    # Test finding documents by entity
    docs_with_techcorp = await mcp_server.find_documents_by_entity(
        entity_name="TechCorp"
    )
    assert len(docs_with_techcorp["documents"]) >= 1

    # Test finding documents by date range
    docs_in_range = await mcp_server.find_documents_by_date(
        start_date="2024-01-01", end_date="2024-12-31"
    )
    assert len(docs_in_range["documents"]) >= 3  # contract, amendment, and report
