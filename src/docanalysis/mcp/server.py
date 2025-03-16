"""FastMCP server implementation for document analysis."""

from typing import Dict, List, Any, Optional
import logging
import os

from mcp.server.fastmcp import FastMCP

from ..core.analysis import DocumentAnalyzer, AnalysisResult, DocumentSummary
from ..core.storage import DocumentStore
from ..models.anthropic_agent import AnthropicAgent
from .tools import document_tools


logger = logging.getLogger(__name__)


class FastMCPDocumentAnalysisServer:
    """FastMCP server that exposes document analysis capabilities."""

    def __init__(self):
        """Initialize the FastMCP document analysis server."""
        self._mcp = FastMCP(
            "Document Analysis",
            description="Document analysis, summarization, and relationship mapping",
            version="2.0.0",
        )
        self._analyzer = None
        self._doc_store = None
        self._initialized = False
        self._setup_tools()

    def _setup_tools(self):
        """Set up tool definitions using decorator pattern."""

        @self._mcp.tool()
        async def analyze_document(
            file_path: str,
            doc_type: Optional[str] = None,
            title: Optional[str] = None,
            reference_id: Optional[str] = None,
            category: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Analyze a document file to extract key information.

            Args:
                file_path: Path to document file
                doc_type: Document type (e.g., contract, report)
                title: Document title
                reference_id: Reference document ID
                category: Document category

            Returns:
                Analysis results
            """
            return await document_tools.analyze_document(
                file_path=file_path,
                doc_type=doc_type,
                title=title,
                reference_id=reference_id,
                category=category,
            )

        @self._mcp.tool()
        async def summarize_document(
            doc_id: str, detail_level: str = "standard"
        ) -> Dict[str, Any]:
            """Generate a summary of a document at different detail levels.

            Args:
                doc_id: Document ID
                detail_level: Summary detail level

            Returns:
                Generated summary
            """
            return await document_tools.summarize_document(
                doc_id=doc_id,
                detail_level=detail_level,
            )

        @self._mcp.tool()
        async def find_relationships(doc_id: str) -> Dict[str, List[Dict[str, Any]]]:
            """Find relationships between documents.

            Args:
                doc_id: Document ID

            Returns:
                Document relationships
            """
            return await document_tools.find_relationships(doc_id=doc_id)

        @self._mcp.tool()
        async def search_documents(
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            doc_type: Optional[str] = None,
            category: Optional[str] = None,
        ) -> List[Dict[str, Any]]:
            """Search for documents by date range, type, or category.

            Args:
                start_date: Start date (YYYY-MM-DD)
                end_date: End date (YYYY-MM-DD)
                doc_type: Filter by document type
                category: Filter by category

            Returns:
                Matching documents
            """
            return await document_tools.search_documents(
                start_date=start_date,
                end_date=end_date,
                doc_type=doc_type,
                category=category,
            )

        @self._mcp.tool()
        async def find_entity(entity: str) -> List[Dict[str, Any]]:
            """Find documents that mention a specific entity.

            Args:
                entity: Entity name to search for

            Returns:
                Matching documents
            """
            return await document_tools.find_entity(entity=entity)

        @self._mcp.tool()
        async def extract_info(doc_id: str, info_types: List[str]) -> Dict[str, Any]:
            """Extract specific types of information from a document.

            Args:
                doc_id: Document ID
                info_types: Types of information to extract

            Returns:
                Extracted information
            """
            return await document_tools.extract_info(
                doc_id=doc_id,
                info_types=info_types,
            )

        @self._mcp.tool()
        async def batch_analyze(
            directory: str, recursive: bool = False
        ) -> List[Dict[str, Any]]:
            """Analyze all documents in a directory.

            Args:
                directory: Directory path
                recursive: Whether to process subdirectories

            Returns:
                Analysis results
            """
            return await document_tools.batch_analyze(
                directory=directory,
                recursive=recursive,
            )

        # Add a sample prompt template
        @self._mcp.prompt()
        def analyze_new_document(
            file_path: str,
            doc_type: Optional[str] = None,
            category: Optional[str] = None,
        ) -> str:
            """Create a prompt to analyze a new document.

            Args:
                file_path: Path to the document file
                doc_type: Document type (optional)
                category: Document category (optional)

            Returns:
                Prompt text
            """
            type_str = f" of type {doc_type}" if doc_type else ""
            category_str = f" in category {category}" if category else ""
            return f"""Please analyze the document at {file_path}{type_str}{category_str}.
            
Extract the following information:
1. Key facts and entities
2. Main topics covered
3. Important dates mentioned
4. Relationships to other documents (if any)
5. A brief summary

Be thorough but concise in your analysis."""

        # Add a resource example for document schema
        @self._mcp.resource("schema://document")
        def document_schema() -> str:
            """Provide the document schema as a resource."""
            return """
Document Schema:
{
  "id": "string",
  "content": "string",
  "metadata": {
    "type": "string",
    "title": "string",
    "date": "string (YYYY-MM-DD)",
    "reference_id": "string (optional)",
    "category": "string (optional)",
    "source_file": "string"
  }
}
"""

    async def initialize(self):
        """Initialize the FastMCP server with required capabilities."""
        if self._initialized:
            return

        # Initialize core services
        self._doc_store = DocumentStore()
        await self._doc_store.initialize()

        # Create Agent using pydantic model instead of AnthropicLLM
        agent = AnthropicAgent(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            model="claude-3-opus-20240229",
        )

        self._analyzer = DocumentAnalyzer(agent)

        # Initialize document tools
        document_tools.init(self._doc_store, self._analyzer)

        self._initialized = True

    def app(self):
        """Get the FastAPI app instance.

        Returns:
            FastAPI: The FastAPI app instance
        """
        if not self._initialized:
            raise RuntimeError("Server not initialized. Call initialize() first.")
        return self._mcp.app

    async def analyze_document(self, document: Dict[str, Any]) -> AnalysisResult:
        """Analyze a single document using FastMCP capabilities.

        Args:
            document: Document to analyze with content and metadata

        Returns:
            AnalysisResult: Analysis results
        """
        if not self._initialized:
            await self.initialize()

        return await self._analyzer.analyze_document(
            content=document["content"], metadata=document.get("metadata", {})
        )

    async def analyze_documents(
        self,
        documents: List[Dict[str, Any]],
        relationships: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> List[AnalysisResult]:
        """Analyze multiple documents using FastMCP capabilities.

        Args:
            documents: List of documents to analyze
            relationships: Optional pre-computed relationships

        Returns:
            List[AnalysisResult]: Analysis results for each document
        """
        if not self._initialized:
            await self.initialize()

        return await self._analyzer.analyze_documents(documents, relationships)

    async def summarize_document(
        self, document: Dict[str, Any], detail_level: str = "standard"
    ) -> DocumentSummary:
        """Generate a document summary using FastMCP capabilities.

        Args:
            document: Document to summarize
            detail_level: Level of detail ("brief", "standard", or "detailed")

        Returns:
            DocumentSummary: Generated summary
        """
        if not self._initialized:
            await self.initialize()

        return await self._analyzer.summarize_document(
            content=document["content"],
            metadata=document.get("metadata", {}),
            detail_level=detail_level,
        )

    async def extract_info(
        self, document: Dict[str, Any], info_types: List[str]
    ) -> Dict[str, Any]:
        """Extract specific types of information using FastMCP capabilities.

        Args:
            document: Document to analyze
            info_types: Types of information to extract

        Returns:
            Dict[str, Any]: Extracted information by type
        """
        if not self._initialized:
            await self.initialize()

        return await self._analyzer.extract_info(
            content=document["content"],
            metadata=document.get("metadata", {}),
            info_types=info_types,
        )

    async def store_document(self, document: Dict[str, Any]) -> str:
        """Store a document using FastMCP capabilities.

        Args:
            document: Document to store

        Returns:
            str: Document ID
        """
        if not self._initialized:
            await self.initialize()

        return await self._doc_store.store_document(document)

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document using FastMCP capabilities.

        Args:
            doc_id: Document ID

        Returns:
            Optional[Dict]: Document if found, None otherwise
        """
        if not self._initialized:
            await self.initialize()

        return await self._doc_store.get_document(doc_id)

    async def find_similar_documents(
        self, doc_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar documents using FastMCP capabilities.

        Args:
            doc_id: Reference document ID
            limit: Maximum number of similar documents to return

        Returns:
            List[Dict]: List of similar documents
        """
        if not self._initialized:
            await self.initialize()

        return await self._doc_store.find_similar_documents(doc_id, limit)

    async def find_documents_by_date(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Find documents by date using FastMCP capabilities.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List[Dict]: List of matching documents
        """
        if not self._initialized:
            await self.initialize()

        return await self._doc_store.find_documents_by_date(start_date, end_date)

    async def find_documents_by_entity(self, entity: str) -> List[Dict[str, Any]]:
        """Find documents by entity using FastMCP capabilities.

        Args:
            entity: Entity name to search for

        Returns:
            List[Dict]: List of matching documents
        """
        if not self._initialized:
            await self.initialize()

        return await self._doc_store.find_documents_by_entity(entity)

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the FastMCP server.

        Args:
            host: Host to bind to
            port: Port to listen on
        """
        if not self._initialized:
            raise RuntimeError("Server not initialized. Call initialize() first.")

        logger.info(f"Starting FastMCP document analysis server on {host}:{port}")
        self._mcp.run(host=host, port=port)
