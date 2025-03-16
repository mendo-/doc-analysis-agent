"""Core document analysis functionality."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class AnalysisResult:
    """Result of document analysis."""

    document_type: str
    key_entities: List[str]
    monetary_values: List[float]
    dates: List[str]
    key_info: Dict[str, Any]
    reference_id: Optional[str] = None
    changes_detected: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = None
    source_doc_id: Optional[str] = None


@dataclass
class DocumentSummary:
    """Document summary with configurable detail level."""

    content: str
    key_points: List[str]
    detail_level: str
    word_count: int
    source_doc_id: Optional[str] = None


class DocumentAnalyzer:
    """Core document analysis functionality."""

    def __init__(self, llm_service: Any):
        """Initialize with an LLM service.

        Args:
            llm_service: Any service that provides text generation capabilities
        """
        self._llm = llm_service

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into a dictionary.

        Args:
            response: Raw response from the LLM

        Returns:
            Dict[str, Any]: Parsed response

        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # First try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Find the first { and last } to extract JSON
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON object found in response")

            json_str = response[start:end]
            return json.loads(json_str)

    async def analyze_document(
        self, content: str, metadata: Dict[str, Any]
    ) -> AnalysisResult:
        """Analyze a single document.

        Args:
            content: Document content
            metadata: Document metadata

        Returns:
            AnalysisResult: Analysis results
        """
        doc_type = metadata.get("type", "unknown")
        prompt = f"""Analyze the following document and extract key information.

Document Content: {content}

Document Type: {doc_type}

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
    "source_doc_id": "{metadata.get('id', '')}"
}}

Return ONLY the JSON object, no additional text."""

        try:
            # Update to use generate instead of generate_str for pydantic-based Agent
            response = await self._llm.generate(prompt)
            result_dict = self._parse_llm_response(response)

            # Add source document ID if available and not already included
            if "source_doc_id" not in result_dict and "id" in metadata:
                result_dict["source_doc_id"] = metadata["id"]

            # Use dict unpacking to create the result
            return AnalysisResult(**result_dict)
        except Exception as e:
            # Return basic analysis on error
            return AnalysisResult(
                document_type=doc_type,
                key_entities=[],
                monetary_values=[],
                dates=[],
                key_info={},
                source_doc_id=metadata.get("id", ""),
            )

    async def analyze_documents(
        self,
        documents: List[Dict[str, Any]],
        relationships: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> List[AnalysisResult]:
        """Analyze multiple documents and identify relationships.

        Args:
            documents: List of documents
            relationships: Optional pre-computed relationships

        Returns:
            List[AnalysisResult]: Analysis results for each document
        """
        results = []
        for doc in documents:
            result = await self.analyze_document(
                content=doc["content"], metadata=doc.get("metadata", {})
            )
            results.append(result)

        # Process relationships if provided
        if relationships:
            for doc_id, related_docs in relationships.items():
                for i, result in enumerate(results):
                    if result.source_doc_id == doc_id or doc_id in str(
                        result.source_doc_id
                    ):
                        results[i].relationships = related_docs

        return results

    async def summarize_document(
        self, content: str, metadata: Dict[str, Any], detail_level: str = "standard"
    ) -> DocumentSummary:
        """Generate a document summary.

        Args:
            content: Document content
            metadata: Document metadata
            detail_level: Summary detail level (brief, standard, detailed)

        Returns:
            DocumentSummary: Generated summary
        """
        # Validate detail level
        if detail_level not in ["brief", "standard", "detailed"]:
            detail_level = "standard"

        prompt = f"""Generate a {detail_level} summary of the following document.

Document Content: {content}

Requirements:
1. For 'brief' summary: Key points only, max 25% of original length
2. For 'standard' summary: Main points and important details
3. For 'detailed' summary: Comprehensive coverage with all significant information

Provide the summary in the following JSON structure:
{{
    "content": "The actual summary text",
    "key_points": [
        "list of key points",
        "important aspects",
        "critical details"
    ],
    "detail_level": "{detail_level}",
    "word_count": 123
}}

Return ONLY the JSON object, no additional text."""

        try:
            # Update to use generate instead of generate_str for pydantic-based Agent
            response = await self._llm.generate(prompt)
            result_dict = self._parse_llm_response(response)

            # Add source document ID if available
            if "id" in metadata:
                result_dict["source_doc_id"] = metadata["id"]

            return DocumentSummary(**result_dict)

        except Exception as e:
            # Return a basic summary on error
            word_count = len(content.split())
            return DocumentSummary(
                content=f"Failed to generate {detail_level} summary.",
                key_points=[],
                detail_level=detail_level,
                word_count=word_count,
                source_doc_id=metadata.get("id"),
            )

    async def extract_info(
        self, content: str, metadata: Dict[str, Any], info_types: List[str]
    ) -> Dict[str, Any]:
        """Extract specific types of information.

        Args:
            content: Document content
            metadata: Document metadata
            info_types: Types of information to extract

        Returns:
            Dict[str, Any]: Extracted information by type
        """
        info_types_str = ", ".join(info_types)
        prompt = f"""Extract the following information types from the document:
{info_types_str}

Document Content: {content}

For each information type, provide a list of relevant items.
Return results in the following JSON structure:
{{
    "type1": ["item1", "item2", ...],
    "type2": ["item1", "item2", ...],
    ...
}}

Return ONLY the JSON object, no additional text."""

        try:
            # Update to use generate instead of generate_str for pydantic-based Agent
            response = await self._llm.generate(prompt)
            return self._parse_llm_response(response)
        except Exception as e:
            # Return empty results on error
            return {info_type: [] for info_type in info_types}
