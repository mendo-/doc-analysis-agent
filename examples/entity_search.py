"""Example of entity search using the Document Analysis Agent."""

import asyncio
import os
from docanalysis.mcp.server import FastMCPDocumentAnalysisServer
from docanalysis.mcp.tools import find_entity


async def main():
    # Initialize the server
    server = FastMCPDocumentAnalysisServer()
    await server.initialize()

    # Create sample documents with various entities
    documents = [
        {
            "content": """
            Partnership Agreement
            Between Microsoft Corporation and OpenAI
            Regarding: AI Technology Development
            Value: $10B
            Date: 2024-01-15
            """,
            "metadata": {
                "type": "agreement",
                "title": "MS-OpenAI Partnership",
                "category": "legal",
            },
        },
        {
            "content": """
            Press Release
            Microsoft announces new Azure AI features in collaboration
            with OpenAI's latest models. Google and Amazon also
            expanding their AI offerings.
            """,
            "metadata": {
                "type": "press_release",
                "title": "Azure AI Update",
                "category": "news",
            },
        },
        {
            "content": """
            Market Analysis
            Tech giants Microsoft, Google, and Apple leading the AI race.
            Startups like Anthropic and OpenAI disrupting the market.
            """,
            "metadata": {
                "type": "report",
                "title": "AI Market Analysis",
                "category": "research",
            },
        },
    ]

    try:
        # Store and analyze documents
        for doc in documents:
            await server.analyze_document(doc)

        # Search for specific entities
        entities = ["Microsoft", "OpenAI", "Google"]

        print("\nEntity Search Results:")
        print("-" * 50)

        for entity in entities:
            print(f"\nSearching for: {entity}")
            results = await server.find_documents_by_entity(entity)

            if results:
                print(f"Found in {len(results)} documents:")
                for doc in results:
                    print(f"- {doc['metadata']['title']} ({doc['metadata']['type']})")
            else:
                print("No documents found")

    except Exception as e:
        print(f"Error searching entities: {e}")


if __name__ == "__main__":
    asyncio.run(main())
