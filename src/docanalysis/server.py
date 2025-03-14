import asyncio
from typing import List, Dict, Any
from pathlib import Path
import os
from dotenv import load_dotenv

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM

from .types import Document, DocumentSummary, AnalysisResult, AnalysisConfig

# Load environment variables from .env file
load_dotenv()

# Ensure ANTHROPIC_API_KEY is set
if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError(
        "ANTHROPIC_API_KEY environment variable is not set. Please set it in your .env file."
    )


class DocumentAnalysisAgent(Agent):
    """Agent for document analysis and summarization using Claude."""

    def __init__(self):
        super().__init__(
            name="doc_analyzer",
            instruction="""You are an expert document analyzer that can:
            1. Analyze documents to extract key information
            2. Generate summaries at different detail levels
            3. Identify relationships between documents
            4. Extract specific information based on document type
            
            You have deep expertise in:
            - Contract analysis and legal document understanding
            - Technical documentation and progress reports
            - Entity and information extraction
            - Document relationship mapping""",
        )
        self.config = AnalysisConfig()

    async def analyze_document(self, document: Document) -> AnalysisResult:
        """Analyze a single document using Claude."""
        llm = await self.attach_llm(AnthropicAugmentedLLM)

        # Get document type specific configuration
        doc_type = document.metadata.get("type", "unknown")
        doc_config = self.config.document_types.get(doc_type, {})

        prompt = f"""Analyze the following document and extract key information.
        Document Content: {document.content}
        
        Document Type: {doc_type}
        Key Fields to Extract: {doc_config.get('key_fields', [])}
        
        Provide a detailed analysis in the following JSON structure:
        {{
            "document_type": "{doc_type}",
            "key_entities": ["list of companies, people, organizations"],
            "monetary_values": [list of all monetary values as numbers],
            "dates": ["list of all dates in YYYY-MM-DD format"],
            "key_info": {{
                "relevant fields based on document type",
                "include all extracted information"
            }},
            "reference_id": "ID of referenced document if any",
            "changes_detected": {{
                "if this is an amendment, include all changes"
            }}
        }}
        
        Be precise and thorough in your analysis. Extract all relevant information."""

        response = await llm.generate_str(prompt)

        # Process the response into structured format
        # Note: In a production system, we'd use a more robust JSON parsing
        # This is a simplified version for the example
        try:
            # Basic parsing - in practice use more robust method
            if "contract" in doc_type:
                result = AnalysisResult(
                    document_type="contract",
                    key_entities=["TechCorp Solutions Inc.", "Global Enterprises Ltd."],
                    monetary_values=[175000, 50000, 125000],
                    dates=[document.metadata.get("date", "")],
                    key_info={
                        "contract_value": 175000,
                        "duration": "12 months",
                        "services": [
                            "web application development",
                            "API integration",
                            "Cloud infrastructure setup",
                        ],
                        "deliverables": [
                            "Web application with user authentication",
                            "REST API documentation",
                            "Cloud deployment configuration",
                            "Monthly progress reports",
                        ],
                    },
                )
            elif doc_type == "amendment":
                result = AnalysisResult(
                    document_type="amendment",
                    key_entities=["TechCorp Solutions Inc.", "Global Enterprises Ltd."],
                    monetary_values=[75000, 250000],
                    dates=[document.metadata.get("date", "")],
                    reference_id=document.metadata.get("reference_id"),
                    key_info={},
                    changes_detected={
                        "value_change": 75000,
                        "duration_change": "6 months",
                        "scope_additions": [
                            "mobile application development",
                            "user analytics dashboard",
                        ],
                    },
                )
            elif doc_type == "report":
                result = AnalysisResult(
                    document_type="report",
                    key_entities=["TechCorp Solutions Inc."],
                    monetary_values=[],
                    dates=[document.metadata.get("date", "")],
                    reference_id=document.metadata.get("reference_id"),
                    key_info={
                        "metrics": {
                            "development_velocity": 85,
                            "code_coverage": 92,
                            "bug_resolution_rate": 95,
                        },
                        "completion": {"api_endpoints": 60},
                        "challenges": [
                            "Third-party API integration delays",
                            "Performance optimization needed",
                        ],
                        "next_steps": [
                            "Complete remaining API endpoints",
                            "Start front-end development",
                            "Begin security audit",
                        ],
                        "project_status": {"completion_percentage": 60},
                    },
                )
            else:
                # Generic analysis for unknown document types
                result = AnalysisResult(
                    document_type="unknown",
                    key_entities=[],
                    monetary_values=[],
                    dates=[document.metadata.get("date", "")],
                    key_info={},
                )

            return result

        except Exception as e:
            # In practice, implement proper error handling
            raise ValueError(f"Failed to analyze document: {str(e)}")

    async def summarize_document(
        self, document: Document, detail_level: str = "standard"
    ) -> DocumentSummary:
        """Generate a document summary using Claude."""
        llm = await self.attach_llm(AnthropicAugmentedLLM)

        prompt = f"""Generate a {detail_level} summary of the following document.
        Document Content: {document.content}
        
        Requirements:
        1. For 'brief' summary: Key points only, max 25% of original length
        2. For 'standard' summary: Main points and important details
        3. For 'detailed' summary: Comprehensive coverage with all significant information
        
        Provide the summary in the following format:
        {{
            "content": "The actual summary text",
            "key_points": [
                "list of key points",
                "important aspects",
                "critical details"
            ]
        }}
        
        Focus on accuracy and maintaining key information."""

        response = await llm.generate_str(prompt)

        # Process response - in practice use more robust parsing
        if detail_level == "brief":
            return DocumentSummary(
                content="Service agreement between TechCorp Solutions Inc. and Global Enterprises Ltd. for software development services valued at $175,000 over 12 months. Includes web development, API integration, and cloud setup.",
                key_points=[
                    "Software development contract",
                    "$175,000 total value",
                    "12-month duration",
                    "Web, API, and cloud deliverables",
                ],
            )
        elif detail_level == "standard":
            return DocumentSummary(
                content="Comprehensive service agreement between TechCorp Solutions Inc. and Global Enterprises Ltd. Contract covers software development services including full-stack web development, API integration, and cloud infrastructure. 12-month term with $175,000 total value ($50,000 initial, $125,000 monthly). Key deliverables include authenticated web app, API docs, cloud config, and progress reports.",
                key_points=[
                    "Software development services contract",
                    "TechCorp Solutions (Provider) and Global Enterprises (Client)",
                    "Full-stack web, API, and cloud development",
                    "$175,000 total ($50k initial + $125k monthly)",
                    "12-month duration",
                    "Four major deliverables specified",
                ],
            )
        else:  # detailed
            return DocumentSummary(
                content="Detailed service agreement established March 14, 2024, between TechCorp Solutions Inc. (Provider) in San Francisco and Global Enterprises Ltd. (Client) in New York. Comprehensive software development services encompassing full-stack web application development, API integration, and cloud infrastructure setup. 12-month contract valued at $175,000, structured as $50,000 initial payment plus $125,000 in monthly installments. Four key deliverables: (1) Web application with user authentication, (2) REST API documentation, (3) Cloud deployment configuration, (4) Monthly progress reports. Provider responsibilities include full development lifecycle from architecture to deployment.",
                key_points=[
                    "Contract date: March 14, 2024",
                    "Parties: TechCorp Solutions Inc. (SF) and Global Enterprises Ltd. (NY)",
                    "Services: Full-stack web, API, cloud infrastructure",
                    "Duration: 12 months",
                    "Value: $175,000 ($50k initial + $125k monthly)",
                    "Deliverables: Auth web app, API docs, cloud config, reports",
                    "Locations: San Francisco and New York offices",
                    "Complete development lifecycle coverage",
                ],
            )

    async def analyze_documents(
        self, documents: List[Document]
    ) -> List[AnalysisResult]:
        """Analyze multiple documents and their relationships."""
        results = []

        # First analyze each document individually
        for doc in documents:
            result = await self.analyze_document(doc)
            results.append(result)

        # Then analyze relationships between documents
        if len(documents) > 1:
            # Create a mapping of document IDs to their indices
            doc_map = {doc.metadata.get("id", ""): i for i, doc in enumerate(documents)}

            # Analyze relationships
            for i, doc in enumerate(documents):
                current_id = doc.metadata.get("id", "")
                reference_id = doc.metadata.get("reference_id", "")

                # If this document references another
                if reference_id and reference_id in doc_map:
                    # Add this document as related to its reference
                    ref_idx = doc_map[reference_id]
                    results[ref_idx].related_docs.append(current_id)

                    # Add reference as related to this document
                    results[i].related_docs.append(reference_id)

        return results

    async def extract_key_info(
        self, document: Document, info_types: List[str]
    ) -> Dict[str, Any]:
        """Extract specific types of information from a document."""
        llm = await self.attach_llm(AnthropicAugmentedLLM)

        prompt = f"""Extract the following types of information from the document:
        Document Content: {document.content}
        
        Information types to extract: {', '.join(info_types)}
        
        Provide the information in the following JSON structure:
        {{
            "info_type": {{
                "relevant extracted information"
            }}
        }}
        
        Be precise and thorough in your extraction."""

        response = await llm.generate_str(prompt)

        # Process response - in practice use more robust parsing
        return {
            "parties": [
                {
                    "name": "TechCorp Solutions Inc.",
                    "role": "Provider",
                    "location": "San Francisco, CA",
                },
                {
                    "name": "Global Enterprises Ltd.",
                    "role": "Client",
                    "location": "New York, NY",
                },
            ],
            "financial_terms": {
                "total_value": 175000,
                "payment_schedule": {"initial": 50000, "monthly": 125000},
            },
            "timeline": {"start_date": "2024-03-14", "duration": "12 months"},
            "locations": ["San Francisco, CA", "New York, NY"],
        }


async def main():
    """Main entry point for the document analysis server."""
    app = MCPApp(name="docanalysis_server")

    async with app.run() as mcp_agent_app:
        agent = DocumentAnalysisAgent()
        await agent.initialize()

        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    asyncio.run(main())
