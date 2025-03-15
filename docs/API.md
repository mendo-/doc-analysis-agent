# Document Analysis API

This documentation provides an overview of the Document Analysis API and its usage.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [API Reference](#api-reference)
    - [Document Service](#document-service)
    - [Analysis Service](#analysis-service)
    - [Document Analysis Agent (Deprecated)](#document-analysis-agent-deprecated)
5. [Data Models](#data-models)
6. [Examples](#examples)
7. [Best Practices](#best-practices)

## Prerequisites

Before using the API, ensure you have:

- Python 3.11 or later
- ChromaDB for document storage
- Anthropic API key (for LLM functionality)

## Installation

```bash
pip install docanalysis
```

## Configuration

Configure the API using environment variables or a `.env` file:

```bash
# ChromaDB settings
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION=documents
CHROMA_PERSIST_DIR=/path/to/persist

# Anthropic API (for LLM features)
ANTHROPIC_API_KEY=your_api_key_here

# General settings
ENVIRONMENT=development
DEBUG=false
```

## API Reference

### Document Service

The `DocumentService` class provides access to document storage, retrieval, and processing.

```python
from docanalysis.document_service import DocumentService

# Initialize
doc_service = DocumentService()
await doc_service.initialize()

# Store a document
doc_id = await doc_service.store_document({
    "id": "doc-001",
    "content": "Document content...",
    "metadata": {"type": "contract", "date": "2024-03-15"}
})

# Retrieve a document
document = await doc_service.get_document(doc_id)

# Find similar documents
similar_docs = await doc_service.find_similar_documents(doc_id)

# Find documents by date
may_docs = await doc_service.find_documents_by_date(
    start_date="2024-05-01", 
    end_date="2024-05-31"
)

# Find documents by entity
tech_docs = await doc_service.find_documents_by_entity("TechCorp Inc.")
```

### Analysis Service

The `AnalysisService` class provides document analysis using LLMs.

```python
from docanalysis.analysis_service import AnalysisService

# Initialize
analysis_service = AnalysisService()
await analysis_service.initialize()

# Analyze a document
analysis = await analysis_service.analyze_document({
    "content": "Document content...",
    "metadata": {"type": "contract"}
})

# Generate a summary
summary = await analysis_service.summarize_document(
    document={"content": "Document content..."},
    detail_level="standard"  # Options: "brief", "standard", "detailed"
)

# Extract specific information
info = await analysis_service.extract_info(
    document={"content": "Document content..."},
    info_types=["parties", "financial_terms", "timeline"]
)

# Analyze multiple documents with relationships
results = await analysis_service.analyze_documents(
    documents=[doc1, doc2, doc3],
    relationships=relationship_data  # Optional
)
```

### Document Analysis Agent (Deprecated)

> ⚠️ **Deprecated**: The `DocumentAnalysisAgent` class is deprecated and will be removed in a future version. Use `DocumentService` and `AnalysisService` instead.

```python
from docanalysis.agent import DocumentAnalysisAgent

# Initialize (deprecated)
agent = DocumentAnalysisAgent()
await agent.initialize()

# Analyze a document (deprecated)
analysis = await agent.analyze_document(document)

# Analyze multiple documents (deprecated)
results = await agent.analyze_documents([doc1, doc2, doc3])

# Generate a summary (deprecated)
summary = await agent.summarize_document(
    document, 
    detail_level="standard"
)

# Extract specific information (deprecated)
info = await agent.extract_key_info(
    document,
    info_types=["parties", "financial_terms", "timeline"]
)
```

## Data Models

The API uses the following data models:

- `Document`: Represents a document with content and metadata
- `AnalysisResult`: Results from document analysis
- `DocumentSummary`: Summary of a document's content

## Examples

### Basic Document Analysis

```python
from docanalysis.document_service import DocumentService
from docanalysis.analysis_service import AnalysisService

# Initialize services
doc_service = DocumentService()
analysis_service = AnalysisService()
await doc_service.initialize()
await analysis_service.initialize()

# Store and analyze a document
doc = {
    "id": "contract-001",
    "content": "SERVICE AGREEMENT...",
    "metadata": {"type": "contract", "date": "2024-03-15"}
}
doc_id = await doc_service.store_document(doc)
analysis = await analysis_service.analyze_document(doc)

print(f"Document type: {analysis['document_type']}")
print(f"Key entities: {analysis['key_entities']}")
print(f"Monetary values: {analysis['monetary_values']}")
```

### Finding Related Documents

```python
# Find documents related to a specific entity
tech_corp_docs = await doc_service.find_documents_by_entity("TechCorp Inc.")

# Find documents from a specific date range
may_docs = await doc_service.find_documents_by_date(
    start_date="2024-05-01", 
    end_date="2024-05-31"
)

# Find semantically similar documents
similar_docs = await doc_service.find_similar_documents(doc_id)
```

### Document Summarization

```python
# Generate a summary at different detail levels
brief = await analysis_service.summarize_document(
    document=doc,
    detail_level="brief"  # Or "standard", "detailed"
)

print(f"Summary: {brief['content']}")
print(f"Key points: {brief['key_points']}")
```

## Best Practices

1. Initialize `DocumentService` and `AnalysisService` separately for better resource management
2. Use proper error handling for LLM-based operations
3. Always clean up resources when done (`await doc_service.clear()`)
4. For summarization, choose the appropriate detail level based on needs
5. Set appropriate rate limits when making multiple LLM requests
6. Structure document content clearly for better analysis
7. Use ISO format (YYYY-MM-DD) for dates in metadata
8. Include as much metadata as possible for better document retrieval 