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
def sample_contract() -> Document:
    """A sample contract document for testing."""
    return Document(
        content="""SERVICE AGREEMENT
        
        This Agreement is made on March 14, 2024, between:
        
        TechCorp Solutions Inc. ("Provider")
        123 Tech Lane
        San Francisco, CA 94105
        
        and
        
        Global Enterprises Ltd. ("Client")
        456 Business Ave
        New York, NY 10001
        
        1. Services: Provider will deliver software development services including:
           - Full-stack web application development
           - API integration
           - Cloud infrastructure setup
        
        2. Term: 12 months from the effective date
        
        3. Compensation: Client will pay $175,000 USD as follows:
           - $50,000 initial payment
           - $125,000 in monthly installments
        
        4. Deliverables:
           4.1 Web application with user authentication
           4.2 REST API documentation
           4.3 Cloud deployment configuration
           4.4 Monthly progress reports""",
        metadata={
            "type": "contract",
            "title": "Service Agreement",
            "date": "2024-03-14",
            "id": "TECH-2024-001",
        },
    )


@pytest.fixture
def sample_amendment() -> Document:
    """A sample contract amendment document for testing."""
    return Document(
        content="""CONTRACT AMENDMENT 1
        
        Reference: Service Agreement TECH-2024-001
        Date: June 15, 2024
        
        The parties agree to amend the original agreement as follows:
        
        1. Scope Extension:
           - Add mobile application development
           - Include user analytics dashboard
        
        2. Financial Amendment:
           - Additional cost: $75,000
           - New total contract value: $250,000
        
        3. Timeline:
           - Extended by 6 months
           - New end date: September 14, 2025""",
        metadata={
            "type": "amendment",
            "title": "Contract Amendment 1",
            "date": "2024-06-15",
            "id": "TECH-2024-001-A1",
            "reference_id": "TECH-2024-001",
        },
    )


@pytest.fixture
def sample_report() -> Document:
    """A sample progress report document for testing."""
    return Document(
        content="""MONTHLY PROGRESS REPORT
        
        Project: TechCorp-Global Web Platform
        Period: May 1-31, 2024
        
        1. Accomplishments:
           - Completed user authentication system
           - Deployed initial database schema
           - Finished 60% of API endpoints
        
        2. Key Metrics:
           - Development velocity: 85 story points
           - Code coverage: 92%
           - Bug resolution rate: 95%
        
        3. Challenges:
           - Third-party API integration delays
           - Performance optimization needed
        
        4. Next Steps:
           - Complete remaining API endpoints
           - Start front-end development
           - Begin security audit""",
        metadata={
            "type": "report",
            "title": "May 2024 Progress Report",
            "date": "2024-05-31",
            "id": "TECH-2024-001-R3",
            "reference_id": "TECH-2024-001",
        },
    )


async def test_contract_analysis(doc_agent, sample_contract):
    """Test detailed contract document analysis."""
    result = await doc_agent.analyze_document(sample_contract)

    assert isinstance(result, AnalysisResult)
    assert result.document_type == "contract"

    # Test entity extraction
    assert "TechCorp Solutions Inc." in result.key_entities
    assert "Global Enterprises Ltd." in result.key_entities

    # Test monetary value extraction
    assert 175000 in result.monetary_values
    assert 50000 in result.monetary_values
    assert 125000 in result.monetary_values

    # Test date extraction
    assert "2024-03-14" in result.dates

    # Test key information extraction
    assert result.key_info["contract_value"] == 175000
    assert result.key_info["duration"] == "12 months"
    assert "web application development" in result.key_info["services"]
    assert "API integration" in result.key_info["services"]
    assert len(result.key_info["deliverables"]) >= 4


async def test_amendment_analysis(doc_agent, sample_amendment):
    """Test contract amendment analysis."""
    result = await doc_agent.analyze_document(sample_amendment)

    assert result.document_type == "amendment"
    assert result.reference_id == "TECH-2024-001"
    assert 75000 in result.monetary_values
    assert 250000 in result.monetary_values
    assert "2024-06-15" in result.dates

    # Test change detection
    assert result.changes_detected["value_change"] == 75000
    assert result.changes_detected["duration_change"] == "6 months"
    assert (
        "mobile application development" in result.changes_detected["scope_additions"]
    )


async def test_report_analysis(doc_agent, sample_report):
    """Test progress report analysis."""
    result = await doc_agent.analyze_document(sample_report)

    assert result.document_type == "report"
    assert result.reference_id == "TECH-2024-001"
    assert "2024-05-31" in result.dates

    # Test metrics extraction
    assert result.key_info["metrics"]["development_velocity"] == 85
    assert result.key_info["metrics"]["code_coverage"] == 92
    assert result.key_info["metrics"]["bug_resolution_rate"] == 95

    # Test progress tracking
    assert result.key_info["completion"]["api_endpoints"] == 60
    assert len(result.key_info["challenges"]) >= 2
    assert len(result.key_info["next_steps"]) >= 3


async def test_document_relationships(
    doc_agent, sample_contract, sample_amendment, sample_report
):
    """Test analysis of relationships between documents."""
    results = await doc_agent.analyze_documents(
        [sample_contract, sample_amendment, sample_report]
    )

    assert len(results) == 3

    # Contract should be linked to both amendment and report
    assert "TECH-2024-001-A1" in results[0].related_docs
    assert "TECH-2024-001-R3" in results[0].related_docs

    # Amendment should be linked to contract
    assert "TECH-2024-001" in results[1].related_docs
    assert results[1].changes_detected["value_change"] == 75000

    # Report should be linked to contract
    assert "TECH-2024-001" in results[2].related_docs
    assert results[2].key_info["project_status"]["completion_percentage"] == 60


async def test_summary_generation(doc_agent, sample_contract):
    """Test document summarization at different detail levels."""
    # Test brief summary
    brief = await doc_agent.summarize_document(sample_contract, detail_level="brief")
    assert isinstance(brief, DocumentSummary)
    assert len(brief.content) < len(sample_contract.content) / 4
    assert "TechCorp Solutions" in brief.content
    assert "$175,000" in brief.content

    # Test standard summary
    standard = await doc_agent.summarize_document(
        sample_contract, detail_level="standard"
    )
    assert len(standard.content) > len(brief.content)
    assert len(standard.key_points) >= 4

    # Test detailed summary
    detailed = await doc_agent.summarize_document(
        sample_contract, detail_level="detailed"
    )
    assert len(detailed.content) > len(standard.content)
    assert len(detailed.key_points) >= 6
    assert any("deliverables" in point.lower() for point in detailed.key_points)


async def test_custom_information_extraction(doc_agent, sample_contract):
    """Test extraction of specific types of information."""
    info_types = ["parties", "financial_terms", "timeline", "locations"]
    result = await doc_agent.extract_key_info(sample_contract, info_types)

    assert "parties" in result
    assert len(result["parties"]) == 2
    assert result["parties"][0]["name"] == "TechCorp Solutions Inc."
    assert result["parties"][0]["location"] == "San Francisco, CA"

    assert "financial_terms" in result
    assert result["financial_terms"]["total_value"] == 175000
    assert result["financial_terms"]["payment_schedule"]["initial"] == 50000

    assert "timeline" in result
    assert result["timeline"]["duration"] == "12 months"
    assert result["timeline"]["start_date"] == "2024-03-14"

    assert "locations" in result
    assert "San Francisco, CA" in result["locations"]
    assert "New York, NY" in result["locations"]
