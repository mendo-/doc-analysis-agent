"""Example of document summarization using the Document Analysis Agent."""

import asyncio
import os
from docanalysis.mcp.server import FastMCPDocumentAnalysisServer


async def main():
    # Initialize the server
    server = FastMCPDocumentAnalysisServer()
    await server.initialize()

    # Create a sample document
    sample_doc = """
    Quarterly Business Report - Q1 2024
    
    Executive Summary:
    The first quarter of 2024 showed strong performance across all business units.
    Total revenue reached $5.2M, representing a 25% YoY growth. Customer satisfaction
    scores improved to 92%, and we launched three new product features.
    
    Key Achievements:
    1. Successfully expanded into two new markets: Canada and Mexico
    2. Completed migration to cloud infrastructure, reducing operational costs by 30%
    3. Hired 15 new team members across engineering and sales departments
    4. Secured two major enterprise clients with total contract value of $1.5M
    
    Challenges:
    - Supply chain disruptions caused minor delays in hardware deliveries
    - Increasing competition in the European market
    
    Next Steps:
    - Begin Phase 2 of the international expansion plan
    - Launch customer loyalty program in Q2
    - Initiate recruitment for leadership positions in new markets
    """

    # Create document dictionary with content and metadata
    document = {
        "content": sample_doc,
        "metadata": {
            "type": "report",
            "title": "Q1 2024 Business Report",
            "category": "business",
        },
    }

    try:
        # Generate summaries at different detail levels
        detail_levels = ["brief", "standard", "detailed"]

        for level in detail_levels:
            summary = await server.summarize_document(document, level)

            print(f"\n{level.upper()} Summary:")
            print("-" * 50)
            print(f"Content:\n{summary.content}\n")
            print("Key Points:")
            for point in summary.key_points:
                print(f"- {point}")
            print(f"\nWord Count: {summary.word_count}")
            print("-" * 50)

    except Exception as e:
        print(f"Error generating summaries: {e}")


if __name__ == "__main__":
    asyncio.run(main())
