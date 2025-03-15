# Working with Different Document Types

This guide demonstrates how to analyze different types of documents.

## Basic Setup

```python
# Import the required modules
from docanalysis.document_service import DocumentService
from docanalysis.analysis_service import AnalysisService
from docanalysis.core.types import Document

# Initialize services
doc_service = DocumentService()
analysis_service = AnalysisService()

async def init():
    await doc_service.initialize()
    await analysis_service.initialize()

await init()  # Initialize services
```

## Analyzing Contracts

Contracts typically contain parties, financial terms, and timelines.

```python
# Create a contract document
contract = {
    "id": "contract-001",
    "content": """SERVICE AGREEMENT
    
    This Agreement is made on March 14, 2024, between:
    
    TechCorp Solutions Inc. ("Provider")
    and
    Global Enterprises Ltd. ("Client")
    
    1. Services: Provider will deliver software development services.
    2. Term: 12 months from the effective date
    3. Compensation: Client will pay $175,000 USD""",
    "metadata": {
        "type": "contract",
        "date": "2024-03-14"
    }
}

# Store and analyze the contract
doc_id = await doc_service.store_document(contract)
contract_analysis = await analysis_service.analyze_document(contract)

# Extract specific contract information
contract_info = await analysis_service.extract_info(
    contract,
    info_types=["parties", "financial_terms", "timeline"]
)

print(f"Contract analysis: {contract_analysis}")
print(f"Specific contract info: {contract_info}")
```

## Analyzing Reports

Reports often contain metrics, observations, and action items.

```python
# Create a report document
report = {
    "id": "report-001",
    "content": """MONTHLY PROGRESS REPORT
    
    Project: TechCorp Web Platform
    Period: May 1-31, 2024
    
    1. Accomplishments:
       - Completed user authentication system
       - Deployed initial database schema
       - Finished 60% of API endpoints
    
    2. Key Metrics:
       - Development velocity: 85 story points
       - Code coverage: 92%
       - Bug resolution rate: 95%
    
    3. Next Steps:
       - Complete remaining API endpoints
       - Start front-end development""",
    "metadata": {
        "type": "report",
        "date": "2024-05-31",
        "references": ["contract-001"]
    }
}

# Store and analyze the report
doc_id = await doc_service.store_document(report)
report_analysis = await analysis_service.analyze_document(report)

# Generate a summary of the report
report_summary = await analysis_service.summarize_document(
    report,
    detail_level="brief"
)

print(f"Report analysis: {report_analysis}")
print(f"Report summary: {report_summary}")
```

## Analyzing Relationships

You can analyze relationships between documents.

```python
# Get relationships between contract and report
contract_relationships = await doc_service.analyze_document_relationships("contract-001")

# Find documents from May 2024
may_docs = await doc_service.find_documents_by_date(
    start_date="2024-05-01",
    end_date="2024-05-31"
)

# Find documents mentioning TechCorp
techcorp_docs = await doc_service.find_documents_by_entity("TechCorp")

print(f"Contract relationships: {contract_relationships}")
print(f"May documents: {may_docs}")
print(f"TechCorp documents: {techcorp_docs}")
```

## Working with PDFs

The API can handle PDF documents as well.

```python
import base64

# Load a PDF file
with open("sample.pdf", "rb") as f:
    pdf_data = f.read()

# Create a PDF document
pdf_doc = {
    "id": "pdf-001",
    "content": {
        "type": "pdf",
        "data": base64.b64encode(pdf_data).decode("utf-8")
    },
    "metadata": {
        "type": "invoice",
        "date": "2024-06-10"
    }
}

# Store and analyze the PDF
doc_id = await doc_service.store_document(pdf_doc)
pdf_analysis = await analysis_service.analyze_document(pdf_doc)

print(f"PDF analysis: {pdf_analysis}")
```

## Best Practices for Document Types

1. **Consistent Metadata**
   - Use consistent metadata fields across similar document types
   - Always include: type, date, title, and category
   - Add reference_id when documents are related

2. **Content Structure**
   - Use clear section headers
   - Include key information in a structured format
   - Maintain consistent formatting within document types

3. **Document Relationships**
   - Use explicit references when documents are related
   - Maintain chronological order with clear dates
   - Include bidirectional references when applicable

4. **Document IDs**
   - Use meaningful, structured IDs
   - Include type and year in the ID
   - Use sequential numbers for related documents 