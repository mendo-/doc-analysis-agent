"""Example of batch document processing using the Document Analysis Agent."""

import asyncio
import os
from pathlib import Path
from docanalysis.mcp.tools import batch_analyze
from docanalysis.mcp.server import FastMCPDocumentAnalysisServer
from docanalysis.core.storage import DocumentStore
from docanalysis.core.analysis import DocumentAnalyzer
from docanalysis.models.anthropic_agent import AnthropicAgent


async def main():
    # Create sample documents in a temporary directory
    docs_dir = Path("sample_docs")
    docs_dir.mkdir(exist_ok=True)

    # Create sample documents
    samples = {
        "contract1.txt": """
        Service Agreement
        Between: Company A and Company B
        Value: $25,000
        Date: 2024-03-15
        """,
        "report1.txt": """
        Quarterly Report
        Q1 2024
        Revenue: $1.2M
        Growth: 15%
        Key Achievements:
        - Market expansion
        - Product launch
        """,
        "invoice1.txt": """
        Invoice #12345
        Date: 2024-03-10
        Amount: $5,500
        Services:
        - Consulting
        - Training
        """,
    }

    # Write sample documents
    for filename, content in samples.items():
        (docs_dir / filename).write_text(content)

    try:
        # Initialize required components
        store = DocumentStore()
        await store.initialize()

        agent = AnthropicAgent(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            model="claude-3-opus-20240229",
        )

        analyzer = DocumentAnalyzer(agent)

        # Process all documents in the directory
        results = await batch_analyze(str(docs_dir))

        print("\nBatch Processing Results:")
        for result in results:
            print(f"\nFile: {result['file']}")
            if "error" in result:
                print(f"Error: {result['error']}")
            else:
                analysis = result["analysis"]
                print(f"Document Type: {analysis['document_type']}")
                print(f"Key Entities: {', '.join(analysis['key_entities'])}")
                print(
                    f"Monetary Values: ${', $'.join(map(str, analysis['monetary_values']))}"
                )

    except Exception as e:
        print(f"Error in batch processing: {e}")

    finally:
        # Clean up sample documents
        for file in docs_dir.glob("*.txt"):
            file.unlink()
        docs_dir.rmdir()


if __name__ == "__main__":
    asyncio.run(main())
