"""MCP tools for document operations."""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from mcp_agent.tools import Tool, ToolRegistry

from ...core.storage import DocumentStore
from ...core.analysis import DocumentAnalyzer


class DocumentTools:
    """MCP tools for document operations."""

    def __init__(self, doc_store: DocumentStore, analyzer: DocumentAnalyzer):
        """Initialize document tools.

        Args:
            doc_store: Document storage service
            analyzer: Document analyzer
        """
        self.doc_store = doc_store
        self.analyzer = analyzer
        self.tools = ToolRegistry()
        self._register_tools()

    def _register_tools(self):
        """Register document operation tools."""

        @self.tools.register("analyze_document")
        async def analyze_document(
            file_path: str,
            doc_type: Optional[str] = None,
            title: Optional[str] = None,
            reference_id: Optional[str] = None,
            category: Optional[str] = None,
        ) -> Dict[str, Any]:
            """Analyze a document file.

            Args:
                file_path: Path to document file
                doc_type: Document type (e.g., contract, report)
                title: Document title
                reference_id: Reference document ID
                category: Document category

            Returns:
                Dict[str, Any]: Analysis results
            """
            # Read document content
            content = Path(file_path).read_text()

            # Generate document ID
            doc_id = f"{doc_type or 'doc'}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            # Create document
            doc = {
                "id": doc_id,
                "content": content,
                "metadata": {
                    "type": doc_type or "unknown",
                    "title": title or Path(file_path).stem,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "reference_id": reference_id,
                    "category": category,
                    "source_file": file_path,
                },
            }

            # Store document
            await self.doc_store.store_document(doc)

            # Analyze document
            result = await self.analyzer.analyze_document(
                content=content, metadata=doc["metadata"]
            )

            return result.model_dump()

        @self.tools.register("summarize_document")
        async def summarize_document(
            doc_id: str, detail_level: str = "standard"
        ) -> Dict[str, Any]:
            """Generate a document summary.

            Args:
                doc_id: Document ID
                detail_level: Summary detail level

            Returns:
                Dict[str, Any]: Generated summary
            """
            # Get document
            doc = await self.doc_store.get_document(doc_id)
            if not doc:
                raise ValueError(f"Document {doc_id} not found")

            # Generate summary
            summary = await self.analyzer.summarize_document(
                content=doc["content"],
                metadata=doc["metadata"],
                detail_level=detail_level,
            )

            return summary.model_dump()

        @self.tools.register("find_relationships")
        async def find_relationships(doc_id: str) -> Dict[str, List[Dict[str, Any]]]:
            """Find document relationships.

            Args:
                doc_id: Document ID

            Returns:
                Dict[str, List[Dict[str, Any]]]: Document relationships
            """
            # Get similar documents
            similar_docs = await self.doc_store.find_similar_documents(doc_id)

            # Get document metadata
            doc = await self.doc_store.get_document(doc_id)
            if not doc:
                raise ValueError(f"Document {doc_id} not found")

            # Check for explicit references
            ref_id = doc["metadata"].get("reference_id")
            referenced_doc = None
            if ref_id:
                referenced_doc = await self.doc_store.get_document(ref_id)

            return {
                "similar": similar_docs,
                "references": [referenced_doc] if referenced_doc else [],
                "referenced_by": [],  # TODO: Implement reverse reference lookup
            }

        @self.tools.register("search_documents")
        async def search_documents(
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            doc_type: Optional[str] = None,
            category: Optional[str] = None,
        ) -> List[Dict[str, Any]]:
            """Search for documents.

            Args:
                start_date: Start date (YYYY-MM-DD)
                end_date: End date (YYYY-MM-DD)
                doc_type: Filter by document type
                category: Filter by category

            Returns:
                List[Dict[str, Any]]: Matching documents
            """
            if start_date and end_date:
                docs = await self.doc_store.find_documents_by_date(start_date, end_date)
            else:
                # Get all documents
                docs = []
                # TODO: Implement get_all_documents in DocumentStore

            # Apply filters
            if doc_type:
                docs = [d for d in docs if d["metadata"]["type"] == doc_type]
            if category:
                docs = [d for d in docs if d["metadata"]["category"] == category]

            return docs

        @self.tools.register("find_entity")
        async def find_entity(entity: str) -> List[Dict[str, Any]]:
            """Find documents mentioning an entity.

            Args:
                entity: Entity name to search for

            Returns:
                List[Dict[str, Any]]: Matching documents
            """
            return await self.doc_store.find_documents_by_entity(entity)

        @self.tools.register("extract_info")
        async def extract_info(doc_id: str, info_types: List[str]) -> Dict[str, Any]:
            """Extract specific information from a document.

            Args:
                doc_id: Document ID
                info_types: Types of information to extract

            Returns:
                Dict[str, Any]: Extracted information
            """
            # Get document
            doc = await self.doc_store.get_document(doc_id)
            if not doc:
                raise ValueError(f"Document {doc_id} not found")

            # Extract information
            return await self.analyzer.extract_info(
                content=doc["content"], metadata=doc["metadata"], info_types=info_types
            )

        @self.tools.register("batch_analyze")
        async def batch_analyze(
            directory: str, recursive: bool = False
        ) -> List[Dict[str, Any]]:
            """Analyze all documents in a directory.

            Args:
                directory: Directory path
                recursive: Whether to process subdirectories

            Returns:
                List[Dict[str, Any]]: Analysis results
            """
            path = Path(directory)
            pattern = "**/*" if recursive else "*"
            files = [f for f in path.glob(pattern) if f.is_file()]

            results = []
            for file_path in files:
                try:
                    result = await analyze_document(
                        file_path=str(file_path),
                        doc_type="unknown",
                        title=file_path.stem,
                    )
                    results.append({"file": str(file_path), "analysis": result})
                except Exception as e:
                    results.append({"file": str(file_path), "error": str(e)})

            return results
