# Document Analysis MCP Server

A powerful document analysis system built using the Model Context Protocol (MCP) and Claude. This system helps organizations efficiently process, analyze, and understand their documents using advanced AI capabilities.

## Features

- Document Analysis: Extract key information, entities, values, and dates
- Smart Summarization: Generate summaries at different detail levels
- Cross-document Analysis: Understand relationships between related documents
- Extensible Architecture: Built on MCP for easy integration and expansion

## Requirements

- Python 3.11 or higher
- Anthropic API key for Claude access
- UV package manager

## Installation

1. Clone the repository
2. Install dependencies:
```bash
uv pip install -r requirements.txt
```

3. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

## Usage

```python
from docanalysis.server import DocumentAnalysisServer
from docanalysis.types import Document

# Initialize the server
server = DocumentAnalysisServer()
await server.initialize()

# Analyze a document
doc = Document(
    content="Your document content here",
    metadata={"type": "contract", "date": "2024-03-14"}
)
result = await server.analyze_document(doc)

# Generate a summary
summary = await server.summarize_document(doc, detail_level="brief")
```

## Testing

Run the tests using pytest:

```bash
pytest tests/
```

## License

MIT License 