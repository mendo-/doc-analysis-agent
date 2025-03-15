"""Command-line interface for document analysis operations."""

import asyncio
import click
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .mcp.server import MCPDocumentAnalysisServer


@click.group()
def cli():
    """Document Analysis CLI tool."""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--doc-type", type=str, help="Document type (e.g., contract, report)")
@click.option("--title", type=str, help="Document title")
@click.option("--reference-id", type=str, help="Reference document ID")
@click.option("--category", type=str, help="Document category")
async def analyze(
    file_path: str,
    doc_type: Optional[str] = None,
    title: Optional[str] = None,
    reference_id: Optional[str] = None,
    category: Optional[str] = None,
):
    """Analyze a document file."""
    server = MCPDocumentAnalysisServer()
    await server.initialize()

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

    # Store and analyze document
    await server.store_document(doc)
    result = await server.analyze_document(doc)
    click.echo(json.dumps(result.model_dump(), indent=2))


@cli.command()
@click.argument("doc_id", type=str)
@click.option(
    "--detail-level",
    type=click.Choice(["brief", "standard", "detailed"]),
    default="standard",
    help="Summary detail level",
)
async def summarize(doc_id: str, detail_level: str):
    """Generate a document summary."""
    server = MCPDocumentAnalysisServer()
    await server.initialize()

    # Get document
    doc = await server.get_document(doc_id)
    if not doc:
        click.echo(f"Document {doc_id} not found", err=True)
        return

    # Generate summary
    summary = await server.summarize_document(doc, detail_level=detail_level)
    click.echo(json.dumps(summary.model_dump(), indent=2))


@cli.command()
@click.argument("doc_id", type=str)
async def relationships(doc_id: str):
    """Find document relationships."""
    server = MCPDocumentAnalysisServer()
    await server.initialize()

    # Get similar documents
    similar = await server.find_similar_documents(doc_id)

    # Get document metadata
    doc = await server.get_document(doc_id)
    if not doc:
        click.echo(f"Document {doc_id} not found", err=True)
        return

    # Check for explicit references
    ref_id = doc["metadata"].get("reference_id")
    referenced_doc = None
    if ref_id:
        referenced_doc = await server.get_document(ref_id)

    relationships = {
        "similar": similar,
        "references": [referenced_doc] if referenced_doc else [],
        "referenced_by": [],  # TODO: Implement reverse reference lookup
    }

    click.echo(json.dumps(relationships, indent=2))


@cli.command()
@click.option("--start-date", type=str, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", type=str, help="End date (YYYY-MM-DD)")
@click.option("--doc-type", type=str, help="Filter by document type")
@click.option("--category", type=str, help="Filter by category")
async def search(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    doc_type: Optional[str] = None,
    category: Optional[str] = None,
):
    """Search for documents."""
    server = MCPDocumentAnalysisServer()
    await server.initialize()

    # Search by date if provided
    if start_date and end_date:
        docs = await server.find_documents_by_date(start_date, end_date)
    else:
        # TODO: Implement get_all_documents
        docs = []

    # Apply filters
    if doc_type:
        docs = [d for d in docs if d["metadata"]["type"] == doc_type]
    if category:
        docs = [d for d in docs if d["metadata"]["category"] == category]

    click.echo(json.dumps(docs, indent=2))


@cli.command()
@click.argument("entity", type=str)
async def find_entity(entity: str):
    """Find documents mentioning a specific entity."""
    server = MCPDocumentAnalysisServer()
    await server.initialize()

    docs = await server.find_documents_by_entity(entity)
    click.echo(json.dumps(docs, indent=2))


@cli.command()
@click.argument("doc_id", type=str)
@click.option(
    "--info-type",
    "-i",
    multiple=True,
    help="Types of information to extract (can be used multiple times)",
)
async def extract_info(doc_id: str, info_type: tuple):
    """Extract specific information from a document."""
    server = MCPDocumentAnalysisServer()
    await server.initialize()

    # Get document
    doc = await server.get_document(doc_id)
    if not doc:
        click.echo(f"Document {doc_id} not found", err=True)
        return

    # Extract information
    info = await server.extract_info(doc, list(info_type))
    click.echo(json.dumps(info, indent=2))


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option(
    "--recursive/--no-recursive", default=False, help="Recursively process directory"
)
async def batch_analyze(directory: str, recursive: bool):
    """Analyze all documents in a directory."""
    server = MCPDocumentAnalysisServer()
    await server.initialize()

    # Get all files
    path = Path(directory)
    pattern = "**/*" if recursive else "*"
    files = [f for f in path.glob(pattern) if f.is_file()]

    results = []
    with click.progressbar(files, label="Analyzing documents") as file_list:
        for file_path in file_list:
            try:
                content = file_path.read_text()
                doc = {
                    "id": f"doc-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    "content": content,
                    "metadata": {
                        "type": "unknown",
                        "title": file_path.stem,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "source_file": str(file_path),
                    },
                }

                # Store and analyze document
                await server.store_document(doc)
                result = await server.analyze_document(doc)
                results.append(
                    {"file": str(file_path), "analysis": result.model_dump()}
                )
            except Exception as e:
                click.echo(f"Error processing {file_path}: {e}", err=True)
                results.append({"file": str(file_path), "error": str(e)})

    click.echo(json.dumps(results, indent=2))


def main():
    """Entry point for the CLI."""
    asyncio.run(cli())
