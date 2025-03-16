"""Example of basic document analysis using the Document Analysis Agent."""

import asyncio
import os
from docanalysis.mcp.server import FastMCPDocumentAnalysisServer


async def main():
    # Initialize the server
    server = FastMCPDocumentAnalysisServer()
    await server.initialize()

    # Create a sample document
    sample_doc = """
    Contract Agreement
    
    Between ABC Corp and XYZ Ltd
    Date: 2024-03-18
    
    This agreement outlines the terms for software development services
    to be provided by XYZ Ltd to ABC Corp for a total value of $50,000.
    The project duration is 6 months starting from April 1, 2024.
    
    Deliverables include:
    1. Web application development
    2. Mobile app integration
    3. API documentation
    """

    # Create a document dictionary with content and metadata
    document = {
        "content": sample_doc,
        "metadata": {
            "type": "contract",
            "title": "Software Development Agreement",
            "category": "legal",
        },
    }

    try:
        # Analyze the document
        result = await server.analyze_document(document)

        print("\nDocument Analysis Results:")
        print(f"Document Type: {result.document_type}")
        print(f"Key Entities: {', '.join(result.key_entities)}")
        print(f"Monetary Values: ${', $'.join(map(str, result.monetary_values))}")
        print(f"Dates: {', '.join(result.dates)}")
        print("\nKey Information:")
        for key, value in result.key_info.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"Error analyzing document: {e}")


if __name__ == "__main__":
    asyncio.run(main())
