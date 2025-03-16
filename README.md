# Document Analysis Agent

A powerful document analysis system built on the Model Context Protocol (MCP) that provides advanced document processing, analysis, and information extraction capabilities using Claude 3 Opus.

## Features

- 📄 Document Analysis: Extract key information, entities, dates, and monetary values
- 📊 Document Summarization: Generate summaries at different detail levels
- 🔍 Entity Search: Find documents mentioning specific entities
- 📁 Batch Processing: Process multiple documents efficiently
- 🤖 AI-Powered: Leverages Claude 3 Opus for intelligent analysis
- 🔄 MCP Integration: Built on the Model Context Protocol for standardized communication

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) for dependency management
- Anthropic API key for Claude 3 access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/doc-analysis-agent.git
cd doc-analysis-agent
```

2. Create a virtual environment and install dependencies using uv:
```bash
uv venv
source .venv/bin/activate  # On Unix/macOS
uv pip install -e .
```

3. Set up your environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your-api-key-here
```

## Usage

The Document Analysis Agent provides several ways to process and analyze documents. Here are some common use cases:

### Basic Document Analysis

```python
from docanalysis.mcp.server import FastMCPDocumentAnalysisServer

# Initialize the server
server = FastMCPDocumentAnalysisServer()
await server.initialize()

# Analyze a document
result = await server.analyze_document({
    "content": "Your document content here",
    "metadata": {
        "type": "contract",
        "title": "Sample Document"
    }
})
```

Check out the [examples](examples/) directory for more detailed examples:

- [Basic Analysis](examples/basic_analysis.py): Simple document analysis
- [Batch Processing](examples/batch_processing.py): Process multiple documents
- [Document Summary](examples/document_summary.py): Generate summaries
- [Entity Search](examples/entity_search.py): Search for entities

## API Reference

### Document Analysis

- `analyze_document(document)`: Analyze a single document
- `analyze_documents(documents)`: Process multiple documents
- `summarize_document(document, detail_level)`: Generate document summary
- `extract_info(document, info_types)`: Extract specific information
- `find_documents_by_entity(entity)`: Search for documents by entity

### Document Types

The system supports various document types with specialized analysis:

- Contracts
- Reports
- Invoices
- Amendments
- Press Releases
- And more...

## Development

### Running Tests

```bash
python -m pytest tests/ -v

# If using hatch
hatch run test:test
```

### Docker Support

Build and run using Docker:

```bash
docker-compose up --build
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [FastMCP](https://github.com/yourusername/fastmcp)
- Powered by [Anthropic's Claude 3](https://www.anthropic.com/claude) 