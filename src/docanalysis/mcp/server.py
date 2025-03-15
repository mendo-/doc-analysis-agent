"""MCP server implementation for document analysis."""

from typing import Dict, List, Any, Optional
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM

from ..core.analysis import DocumentAnalyzer, AnalysisResult, DocumentSummary
from ..core.storage import DocumentStore
from .tools.document_tools import DocumentTools


class MCPDocumentAnalysisServer:
    """MCP server that exposes document analysis capabilities."""

    def __init__(self):
        """Initialize the MCP document analysis server."""
        self._app = None
        self._agent = None
        self._analyzer = None
        self._doc_store = None
        self._doc_tools = None
        self._initialized = False

    async def initialize(self):
        """Initialize the MCP server with required capabilities."""
        if self._initialized:
            return

        # Initialize MCP agent app
        self._app = MCPApp(name="doc_analysis")
        async with self._app.run() as mcp_app:
            # Create agent with document analysis capabilities
            self._agent = Agent(
                name="doc_analyzer",
                instruction="""You are a document analysis agent that can:
                1. Analyze documents to extract key information
                2. Find relationships between documents
                3. Generate summaries at different detail levels
                4. Extract specific types of information
                
                You should always return results in structured JSON format.""",
                server_names=["fetch", "filesystem"],
            )
            await self._agent.initialize()

            # Initialize LLM
            llm = await self._agent.attach_llm(AnthropicAugmentedLLM)

            # Initialize core services
            self._doc_store = DocumentStore()
            await self._doc_store.initialize()

            self._analyzer = DocumentAnalyzer(llm)

            # Initialize document tools
            self._doc_tools = DocumentTools(self._doc_store, self._analyzer)

            # Register tools with agent
            self._agent.register_tools(self._doc_tools.tools)

            self._initialized = True

    async def analyze_document(self, document: Dict[str, Any]) -> AnalysisResult:
        """Analyze a single document using MCP capabilities.

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
        """Analyze multiple documents using MCP capabilities.

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
        """Generate a document summary using MCP capabilities.

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
        """Extract specific types of information using MCP capabilities.

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
        """Store a document using MCP capabilities.

        Args:
            document: Document to store

        Returns:
            str: Document ID
        """
        if not self._initialized:
            await self.initialize()

        return await self._doc_store.store_document(document)

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document using MCP capabilities.

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
        """Find similar documents using MCP capabilities.

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
        """Find documents by date using MCP capabilities.

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
        """Find documents by entity using MCP capabilities.

        Args:
            entity: Entity name to search for

        Returns:
            List[Dict]: List of matching documents
        """
        if not self._initialized:
            await self.initialize()

        return await self._doc_store.find_documents_by_entity(entity)
