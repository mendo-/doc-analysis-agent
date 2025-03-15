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
    "reference_id": "ID of referenced document if any",
    "changes_detected": {{
        "if this is an amendment, include all changes"
    }},
    "confidence_score": 0.95,
    "metadata": {{
        "additional analysis metadata"
    }}
}}

Be precise and thorough in your analysis. Extract all relevant information.
Return ONLY the JSON object, no additional text."""

        try:
            response = await self._llm.generate_str(prompt)
            result_dict = self._parse_llm_response(response)

            # Add source document ID if available
            if "id" in metadata:
                result_dict["source_doc_id"] = metadata["id"]

            return AnalysisResult(**result_dict)

        except Exception as e:
            # Return a basic result on error
            return AnalysisResult(
                document_type=doc_type,
                key_entities=[],
                monetary_values=[],
                dates=[metadata.get("date", "")],
                key_info={},
                confidence_score=0.0,
                metadata=metadata,
                source_doc_id=metadata.get("id"),
            )

    async def analyze_documents(
        self,
        documents: List[Dict[str, Any]],
        relationships: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> List[AnalysisResult]:
        """Analyze multiple documents and their relationships.

        Args:
            documents: List of documents to analyze
            relationships: Optional pre-computed relationships

        Returns:
            List[AnalysisResult]: Analysis results for each document
        """
        # Analyze each document
        results = []
        for doc in documents:
            result = await self.analyze_document(
                content=doc["content"], metadata=doc.get("metadata", {})
            )
            results.append(result)

        # Add relationship information if provided
        if relationships:
            for i, doc in enumerate(documents):
                doc_id = doc.get("metadata", {}).get("id")
                if doc_id and doc_id in relationships:
                    doc_relationships = relationships[doc_id]
                    related_ids = []

                    # Extract IDs from relationships
                    for rel_type, rel_docs in doc_relationships.items():
                        for rel_doc in rel_docs:
                            related_ids.append(rel_doc["id"])

                    # Update result with relationships
                    results[i].key_info["related_docs"] = list(set(related_ids))

        return results

    async def summarize_document(
        self, content: str, metadata: Dict[str, Any], detail_level: str = "standard"
    ) -> DocumentSummary:
        """Generate a document summary.

        Args:
            content: Document content
            metadata: Document metadata
            detail_level: Level of detail ("brief", "standard", or "detailed")

        Returns:
            DocumentSummary: Generated summary
        """
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
            response = await self._llm.generate_str(prompt)
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
        prompt = f"""Extract the following types of information from the document:
{', '.join(info_types)}

Document Content: {content}

For each information type, provide structured data in the following format:
{{
    "parties": [
        {{"name": "party name", "role": "party role"}},
        ...
    ],
    "dates": ["YYYY-MM-DD", ...],
    "locations": ["full address or location name", ...],
    ... (other requested types)
}}

Be precise and thorough in extraction. Return ONLY the JSON object, no additional text."""

        try:
            response = await self._llm.generate_str(prompt)
            result = self._parse_llm_response(response)

            # Ensure all requested types are present
            for info_type in info_types:
                if info_type not in result:
                    result[info_type] = []

            return result

        except Exception as e:
            # Return empty results for each type on error
            return {info_type: [] for info_type in info_types}
