# Document Analysis Agent

A powerful document analysis system built on the Model Context Protocol (MCP) that uses Claude to analyze, summarize, and understand relationships between various types of documents, with a special focus on contracts, amendments, and technical reports.

## Overview

This project provides an intelligent document analysis system that can:

- Extract key information from documents
- Generate summaries at different detail levels
- Identify and track relationships between related documents
- Analyze specific document types (contracts, amendments, reports)
- Handle complex document structures and relationships

### Key Features

- **Smart Document Analysis**: Extracts entities, dates, monetary values, and key information
- **Multi-level Summarization**: Generate brief, standard, or detailed summaries
- **Document Relationship Tracking**: Automatically identifies and tracks relationships between documents
- **Type-specific Analysis**: Specialized handling for different document types
- **Error Handling**: Robust error handling and fallback mechanisms
- **Integration & Unit Tests**: Comprehensive test suite with both mock and real LLM testing

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/doc-analysis-agent.git
cd doc-analysis-agent
```

2. Install uv (if not already installed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

4. Install dependencies:

```bash
uv pip install -e .
```

4. Set up your environment:

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### Basic Usage

```python
from docanalysis.server import DocumentAnalysisAgent
from docanalysis.core.types import Document

# Initialize the agent
agent = DocumentAnalysisAgent()
await agent.initialize()

# Analyze a document
doc = Document(
    content="Your document content here",
    metadata={
        "type": "contract",
        "title": "Service Agreement",
        "date": "2024-03-14",
        "id": "DOC-001"
    }
)

# Get analysis
result = await agent.analyze_document(doc)
print(f"Document type: {result.document_type}")
print(f"Key entities: {result.key_entities}")
print(f"Monetary values: {result.monetary_values}")

# Get a summary
summary = await agent.summarize_document(doc, detail_level="standard")
print(f"Summary: {summary.content}")
print(f"Key points: {summary.key_points}")
```

### Analyzing Multiple Documents

```python
# Analyze multiple related documents
docs = [doc1, doc2, doc3]
results = await agent.analyze_documents(docs)

# Check relationships
for result in results:
    print(f"Document {result.document_type} is related to: {result.related_docs}")
```

## Testing

The project includes both unit tests with mocked LLM responses and integration tests using the real Claude API.

Run unit tests:
```bash
pytest tests/test_doc_analysis_server.py -v
```

Run integration tests (requires API key):

```bash
pytest tests/test_doc_analysis_integration.py -v
```

Run all tests:

```bash
pytest tests/ -v
```

## Project Structure

```
doc-analysis-agent/
├── src/
│   └── docanalysis/
│       ├── server.py      # Main agent implementation
│       └── types.py       # Type definitions
├── tests/
│   └── integration/
│       └── test_doc_analysis_integration.py # Integration tests
│   └── unit/ 
│       └── test_doc_analysis_server.py    # Unit tests
├── .env.example          # Example environment variables
└── README.md             # This file
```
