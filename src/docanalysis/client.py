"""MCP Client for Document Analysis."""

import asyncio
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from mcp_agent.client import MCPClient
from mcp_agent.config import MCPConfig, ToolConfig, PromptTemplate
from .types import Document, DocumentSummary, AnalysisResult
import json


class DocumentAnalysisClient:
    """Client for interacting with the Document Analysis MCP server.

    This client provides a high-level interface to the document analysis tools:
    - analyze_document: Extract key information from a single document
    - summarize_document: Generate document summaries at different detail levels
    - extract_info: Extract specific types of information from documents
    - analyze_documents: Analyze relationships between multiple documents
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        tools_config: Optional[List[ToolConfig]] = None,
        prompts_config: Optional[Dict[str, PromptTemplate]] = None,
    ):
        """Initialize the client.

        Args:
            host: MCP server host (default: localhost)
            port: MCP server port (default: 8000)
            tools_config: Optional list of tool configurations
            prompts_config: Optional prompt template configurations
        """
        self.host = host
        self.port = port
        self._client = None
        self._config = MCPConfig(
            tools=tools_config or self._default_tools_config(),
            prompts=prompts_config or self._default_prompts_config(),
            resources={},
        )

    @staticmethod
    def _default_prompts_config() -> Dict[str, PromptTemplate]:
        """Default prompt templates for document analysis."""
        return {
            "analyze": PromptTemplate(
                name="analyze_document",
                template="""Analyze the following document and extract key information:
                Content: {content}
                Type: {doc_type}
                
                Please identify:
                1. Key entities and their roles
                2. Important dates and deadlines
                3. Financial terms and values
                4. Main obligations and requirements
                5. Any notable conditions or constraints
                
                Provide a structured analysis focusing on these aspects.""",
            ),
            "summarize": PromptTemplate(
                name="summarize_document",
                template="""Generate a {detail_level} summary of the following document:
                Content: {content}
                
                For a {detail_level} summary, focus on:
                - Main points and key takeaways
                - Essential details and requirements
                - Critical dates and deadlines
                - Important stakeholders
                
                Provide the summary in a clear, concise format.""",
            ),
            "extract_info": PromptTemplate(
                name="extract_info",
                template="""Extract the following types of information from the document:
                Content: {content}
                Information Types: {info_types}
                
                For each requested information type, provide:
                - Relevant extracted data
                - Context or explanation if needed
                - Confidence level in the extraction
                
                Format the results in a structured manner.""",
            ),
            "analyze_relationships": PromptTemplate(
                name="analyze_relationships",
                template="""Analyze the relationships between the following documents:
                Documents: {documents}
                
                For each document pair, identify:
                1. References between documents
                2. Temporal relationships
                3. Modifications or amendments
                4. Conflicts or inconsistencies
                5. Dependencies
                
                Provide a detailed analysis of document relationships.""",
            ),
        }

    @staticmethod
    def _default_tools_config() -> List[ToolConfig]:
        """Default tool configurations for document analysis."""
        return [
            ToolConfig(
                name="analyze_document",
                description="Analyze a document to extract key information",
                parameters={
                    "document": {
                        "type": "object",
                        "description": "Document to analyze",
                        "properties": {
                            "content": {
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string", "enum": ["pdf"]},
                                            "data": {
                                                "type": "string",
                                                "format": "byte",
                                            },
                                        },
                                        "required": ["type", "data"],
                                    },
                                ]
                            },
                            "metadata": {"type": "object"},
                        },
                        "required": ["content"],
                    }
                },
            ),
            ToolConfig(
                name="summarize_document",
                description="Generate a document summary",
                parameters={
                    "document": {
                        "type": "object",
                        "description": "Document to summarize",
                        "properties": {
                            "content": {
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string", "enum": ["pdf"]},
                                            "data": {
                                                "type": "string",
                                                "format": "byte",
                                            },
                                        },
                                        "required": ["type", "data"],
                                    },
                                ]
                            },
                            "metadata": {"type": "object"},
                        },
                        "required": ["content"],
                    },
                    "detail_level": {
                        "type": "string",
                        "enum": ["brief", "standard", "detailed"],
                    },
                },
            ),
            ToolConfig(
                name="extract_info",
                description="Extract specific types of information",
                parameters={
                    "document": {
                        "type": "object",
                        "description": "Document to analyze",
                        "properties": {
                            "content": {
                                "oneOf": [
                                    {"type": "string"},
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {"type": "string", "enum": ["pdf"]},
                                            "data": {
                                                "type": "string",
                                                "format": "byte",
                                            },
                                        },
                                        "required": ["type", "data"],
                                    },
                                ]
                            },
                            "metadata": {"type": "object"},
                        },
                        "required": ["content"],
                    },
                    "info_types": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            ),
            ToolConfig(
                name="analyze_documents",
                description="Analyze relationships between documents",
                parameters={
                    "documents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {
                                    "oneOf": [
                                        {"type": "string"},
                                        {
                                            "type": "object",
                                            "properties": {
                                                "type": {
                                                    "type": "string",
                                                    "enum": ["pdf"],
                                                },
                                                "data": {
                                                    "type": "string",
                                                    "format": "byte",
                                                },
                                            },
                                            "required": ["type", "data"],
                                        },
                                    ]
                                },
                                "metadata": {"type": "object"},
                            },
                            "required": ["content"],
                        },
                    }
                },
            ),
        ]

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = MCPClient(
            host=self.host,
            port=self.port,
            config=self._config,
        )
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)

    def _prepare_document(
        self,
        content_or_doc: Union[str, bytes, Path, Document],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Prepare document for sending to MCP server.

        Args:
            content_or_doc: Either a string content, bytes (PDF), Path to PDF, or Document object
            metadata: Optional metadata if content is string/bytes/path

        Returns:
            Dictionary with document content and metadata
        """
        if isinstance(content_or_doc, str):
            return {"content": content_or_doc, "metadata": metadata or {}}
        elif isinstance(content_or_doc, bytes):
            return {
                "content": {
                    "type": "pdf",
                    "data": base64.b64encode(content_or_doc).decode(),
                },
                "metadata": metadata or {},
            }
        elif isinstance(content_or_doc, Path):
            with open(content_or_doc, "rb") as f:
                pdf_data = f.read()
            return {
                "content": {
                    "type": "pdf",
                    "data": base64.b64encode(pdf_data).decode(),
                },
                "metadata": metadata or {},
            }
        elif isinstance(content_or_doc, Document):
            if isinstance(content_or_doc.content, (bytes, Path)):
                return self._prepare_document(
                    content_or_doc.content, content_or_doc.metadata
                )
            return {
                "content": content_or_doc.content,
                "metadata": content_or_doc.metadata,
            }
        else:
            raise TypeError(
                "content_or_doc must be either str, bytes, Path, or Document"
            )

    async def analyze_document(
        self,
        content_or_doc: Union[str, bytes, Path, Document],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalysisResult:
        """Analyze a single document.

        Args:
            content_or_doc: Either document content as string, bytes (PDF), Path to PDF, or Document object
            metadata: Optional document metadata (only used if content_or_doc is str/bytes/Path)

        Returns:
            AnalysisResult containing extracted information
        """
        doc = self._prepare_document(content_or_doc, metadata)
        result = await self._client.execute_tool(
            "analyze_document",
            document=doc,
        )
        return AnalysisResult(**result)

    async def summarize_document(
        self,
        content_or_doc: Union[str, bytes, Path, Document],
        detail_level: str = "standard",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentSummary:
        """Generate a document summary.

        Args:
            content_or_doc: Either document content as string, bytes (PDF), Path to PDF, or Document object
            detail_level: Summary detail level ("brief", "standard", or "detailed")
            metadata: Optional document metadata (only used if content_or_doc is str/bytes/Path)

        Returns:
            DocumentSummary containing the summary and key points
        """
        doc = self._prepare_document(content_or_doc, metadata)
        result = await self._client.execute_tool(
            "summarize_document",
            document=doc,
            detail_level=detail_level,
        )
        return DocumentSummary(**result)

    async def extract_info(
        self,
        content_or_doc: Union[str, bytes, Path, Document],
        info_types: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Extract specific types of information from a document.

        Args:
            content_or_doc: Either document content as string, bytes (PDF), Path to PDF, or Document object
            info_types: List of information types to extract
            metadata: Optional document metadata (only used if content_or_doc is str/bytes/Path)

        Returns:
            Dictionary containing extracted information by type
        """
        doc = self._prepare_document(content_or_doc, metadata)
        return await self._client.execute_tool(
            "extract_info",
            document=doc,
            info_types=info_types,
        )

    async def analyze_documents(
        self,
        documents: List[Union[Dict[str, Any], bytes, Path, Document]],
    ) -> List[AnalysisResult]:
        """Analyze multiple documents and their relationships.

        Args:
            documents: List of documents (either dict with content/metadata or bytes/Path/Document objects)

        Returns:
            List of AnalysisResult objects with relationship information
        """
        prepared_docs = [
            self._prepare_document(doc) if isinstance(doc, Document) else doc
            for doc in documents
        ]
        results = await self._client.execute_tool(
            "analyze_documents",
            documents=prepared_docs,
        )
        return [AnalysisResult(**result) for result in results]


async def main():
    """Example usage of the Document Analysis Client."""
    # Example using string content
    contract_content = """SERVICE AGREEMENT
    
    This Agreement is made on March 14, 2024, between:
    TechCorp Solutions Inc. ("Provider") and Global Enterprises Ltd. ("Client")
    
    1. Services: Web application development
    2. Term: 12 months
    3. Value: $175,000 USD
    4. Payment Schedule:
       - Initial Payment: $50,000
       - Monthly Payments: $10,416.67
    """

    contract_metadata = {
        "type": "contract",
        "title": "Service Agreement",
        "date": "2024-03-14",
        "id": "TECH-2024-001",
    }

    # Example using Document object
    amendment = Document(
        content="""CONTRACT AMENDMENT 1
        
        Reference: Service Agreement TECH-2024-001
        Date: June 15, 2024
        
        The following changes are made to the original agreement:
        1. Contract value increased by $75,000
        2. Additional services:
           - Mobile application development
           - User analytics dashboard
        """,
        metadata={
            "type": "amendment",
            "title": "Contract Amendment 1",
            "date": "2024-06-15",
            "id": "TECH-2024-001-A1",
            "reference_id": "TECH-2024-001",
        },
    )

    async with DocumentAnalysisClient() as client:
        # 1. Analyze using string content
        analysis = await client.analyze_document(
            content_or_doc=contract_content,
            metadata=contract_metadata,
        )
        print("\nDocument Analysis:")
        print(f"Type: {analysis.document_type}")
        print(f"Entities: {analysis.key_entities}")
        print(f"Values: {analysis.monetary_values}")

        # 2. Generate summary using Document object
        summary = await client.summarize_document(
            content_or_doc=amendment,
            detail_level="brief",
        )
        print("\nDocument Summary:")
        print(summary.content)
        print("Key Points:", summary.key_points)

        # 3. Extract info using string content
        info = await client.extract_info(
            content_or_doc=contract_content,
            info_types=["parties", "financial_terms", "timeline"],
            metadata=contract_metadata,
        )
        print("\nExtracted Information:")
        print(json.dumps(info, indent=2))

        # 4. Analyze multiple documents (mix of string and Document objects)
        results = await client.analyze_documents(
            documents=[
                {"content": contract_content, "metadata": contract_metadata},
                amendment,
            ]
        )
        print("\nDocument Relationships:")
        for result in results:
            print(f"{result.document_type} is related to: {result.related_docs}")


if __name__ == "__main__":
    asyncio.run(main())
