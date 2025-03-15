"""Core document storage functionality."""

from typing import Dict, List, Optional, Any
import base64
import tempfile
from datetime import datetime

import chromadb
import pypdf

from ..config import settings


class DocumentStore:
    """Document storage service with vector database integration."""

    def __init__(
        self,
        collection_name: str = None,
        host: str = None,
        port: int = None,
    ):
        """Initialize the document store.

        Args:
            collection_name: Name of the vector DB collection
            host: Database server host
            port: Database server port
        """
        self.collection_name = collection_name or settings.chroma.collection_name
        self.host = host or settings.chroma.host
        self.port = port or settings.chroma.port
        self.client = chromadb.HttpClient(host=self.host, port=self.port)
        self.collection = None

    async def initialize(self):
        """Initialize the vector database collection."""
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # Using cosine similarity
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize vector database collection: {e}")

    def _extract_pdf_text(self, pdf_data: bytes) -> str:
        """Extract text from PDF data.

        Args:
            pdf_data: Raw PDF bytes

        Returns:
            str: Extracted text content
        """
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp_file:
            tmp_file.write(pdf_data)
            tmp_file.flush()

            text_content = []
            with open(tmp_file.name, "rb") as pdf_file:
                pdf_reader = pypdf.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())

            return "\n".join(text_content)

    def _get_document_content(self, document: Dict[str, Any]) -> str:
        """Extract text content from document.

        Args:
            document: Document object with content and metadata

        Returns:
            str: Text content of the document
        """
        content = document["content"]
        if isinstance(content, str):
            return content
        elif isinstance(content, dict) and content["type"] == "pdf":
            pdf_data = base64.b64decode(content["data"])
            return self._extract_pdf_text(pdf_data)
        elif isinstance(content, bytes):
            return self._extract_pdf_text(content)
        else:
            raise ValueError("Invalid document content format")

    def prepare_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare document for storage and analysis.

        Args:
            doc_data: Document data from client

        Returns:
            Dict[str, Any]: Document dictionary ready for storage
        """
        content = self._get_document_content(doc_data)
        metadata = doc_data.get("metadata", {})
        doc_id = metadata.get("id", f"doc_{hash(content)}")

        return {
            "id": doc_id,
            "content": content,
            "metadata": metadata,
        }

    async def store_document(self, document: Dict[str, Any]) -> str:
        """Store a document in the collection.

        Args:
            document: Document dictionary with id, content, and metadata

        Returns:
            str: Document ID
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        if isinstance(document.get("content"), (dict, bytes)):
            document = self.prepare_document(document)

        doc_id = document["id"]
        content = document["content"]
        metadata = document.get("metadata", {}).copy()

        if not metadata:
            metadata = {"type": "document"}

        # Convert complex types to strings for ChromaDB
        for key, value in metadata.items():
            if isinstance(value, (list, dict)):
                metadata[key] = str(value)

        # Update or insert document
        existing_doc = await self.get_document(doc_id)
        if existing_doc:
            self.collection.update(
                ids=[doc_id], documents=[content], metadatas=[metadata]
            )
        else:
            self.collection.add(ids=[doc_id], documents=[content], metadatas=[metadata])

        return doc_id

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Optional[Dict]: Document if found, None otherwise
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        result = self.collection.get(ids=[doc_id], include=["documents", "metadatas"])
        if not result["ids"]:
            return None

        return {
            "id": doc_id,
            "content": result["documents"][0],
            "metadata": result["metadatas"][0],
        }

    async def find_similar_documents(
        self, doc_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find semantically similar documents.

        Args:
            doc_id: Reference document ID
            limit: Maximum number of similar documents to return

        Returns:
            List[Dict]: List of similar documents
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        ref_doc = await self.get_document(doc_id)
        if not ref_doc:
            return []

        results = self.collection.query(
            query_texts=[ref_doc["content"]],
            n_results=limit + 1,  # Add 1 to account for the reference document
        )

        similar_docs = []
        for i, result_id in enumerate(results["ids"][0]):
            if result_id != doc_id:  # Skip the reference document
                similar_docs.append(
                    {
                        "id": result_id,
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                    }
                )

        return similar_docs

    async def find_documents_by_date(
        self, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Find documents within a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List[Dict]: List of matching documents
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        # Query documents with date metadata
        results = self.collection.get(
            where={"date": {"$gte": start_date, "$lte": end_date}},
            include=["documents", "metadatas"],
        )

        return [
            {
                "id": doc_id,
                "content": content,
                "metadata": metadata,
            }
            for doc_id, content, metadata in zip(
                results["ids"], results["documents"], results["metadatas"]
            )
        ]

    async def find_documents_by_entity(self, entity: str) -> List[Dict[str, Any]]:
        """Find documents mentioning a specific entity.

        Args:
            entity: Entity name to search for

        Returns:
            List[Dict]: List of matching documents
        """
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        # Search for documents containing the entity
        results = self.collection.query(
            query_texts=[entity],
            n_results=10,
            where={"$contains": entity},  # Additional filter for exact matches
        )

        return [
            {
                "id": doc_id,
                "content": content,
                "metadata": metadata,
            }
            for doc_id, content, metadata in zip(
                results["ids"][0], results["documents"][0], results["metadatas"][0]
            )
        ]

    async def clear(self):
        """Clear all documents from the collection."""
        if self.collection:
            self.client.delete_collection(self.collection_name)
            await self.initialize()
