"""MCP tools for document operations as standalone functions."""

from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from ...core.storage import DocumentStore
from ...core.analysis import DocumentAnalyzer


# Global instances to be initialized by the server
doc_store: DocumentStore = None
analyzer: DocumentAnalyzer = None


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
    await doc_store.store_document(doc)

    # Analyze document
    result = await analyzer.analyze_document(content=content, metadata=doc["metadata"])

    return result.model_dump()


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
    doc = await doc_store.get_document(doc_id)
    if not doc:
        raise ValueError(f"Document {doc_id} not found")

    # Generate summary
    summary = await analyzer.summarize_document(
        content=doc["content"],
        metadata=doc["metadata"],
        detail_level=detail_level,
    )

    return summary.model_dump()


async def find_relationships(doc_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Find document relationships.

    Args:
        doc_id: Document ID

    Returns:
        Dict[str, List[Dict[str, Any]]]: Document relationships
    """
    # Get similar documents
    similar_docs = await doc_store.find_similar_documents(doc_id)

    # Get document metadata
    doc = await doc_store.get_document(doc_id)
    if not doc:
        raise ValueError(f"Document {doc_id} not found")

    # Check for explicit references
    ref_id = doc["metadata"].get("reference_id")
    referenced_doc = None
    if ref_id:
        referenced_doc = await doc_store.get_document(ref_id)

    return {
        "similar": similar_docs,
        "references": [referenced_doc] if referenced_doc else [],
        "referenced_by": [],  # TODO: Implement reverse reference lookup
    }


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
        docs = await doc_store.find_documents_by_date(start_date, end_date)
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


async def find_entity(entity: str) -> List[Dict[str, Any]]:
    """Find documents mentioning an entity.

    Args:
        entity: Entity name to search for

    Returns:
        List[Dict[str, Any]]: Matching documents
    """
    return await doc_store.find_documents_by_entity(entity)


async def extract_info(doc_id: str, info_types: List[str]) -> Dict[str, Any]:
    """Extract specific information from a document.

    Args:
        doc_id: Document ID
        info_types: Types of information to extract

    Returns:
        Dict[str, Any]: Extracted information
    """
    # Get document
    doc = await doc_store.get_document(doc_id)
    if not doc:
        raise ValueError(f"Document {doc_id} not found")

    # Extract information
    return await analyzer.extract_info(
        content=doc["content"], metadata=doc["metadata"], info_types=info_types
    )


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


def init(store: DocumentStore, doc_analyzer: DocumentAnalyzer):
    """Initialize the document tools with required dependencies.

    Args:
        store: Document storage service
        doc_analyzer: Document analyzer
    """
    global doc_store, analyzer
    doc_store = store
    analyzer = doc_analyzer
