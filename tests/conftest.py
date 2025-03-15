"""Test fixtures for document analysis."""

import os
import time
import pytest
import requests
import subprocess
import chromadb
from pathlib import Path
from typing import AsyncGenerator, Dict, Generator

from docanalysis.core.storage import DocumentStore
from docanalysis.config import Settings
from docanalysis.mcp.server import MCPDocumentAnalysisServer
from tests.data.test_pdfs import create_test_pdfs

# Load test configuration
settings = Settings.load(load_test_env=True)


@pytest.fixture(scope="session")
def test_pdfs() -> Dict[str, Path]:
    """Create test PDF files.

    Returns:
        Dict[str, Path]: Dictionary of test PDF paths
    """
    return create_test_pdfs()


@pytest.fixture(scope="session")
def chroma_server() -> Generator[None, None, None]:
    """Start a ChromaDB server for integration tests.

    This fixture starts a ChromaDB server before running tests and stops it after.
    It uses the default configuration with an in-memory backend for tests.
    """
    # Get configuration from environment variables
    host = settings.chroma.host
    port = settings.chroma.port
    persist_directory = settings.chroma.persist_directory or ":memory:"

    # Start ChromaDB server
    server_process = subprocess.Popen(
        [
            "chroma",
            "run",
            "--host",
            host,
            "--port",
            str(port),
            "--path",
            persist_directory,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    max_retries = 30
    retry_interval = 1
    server_url = f"http://{host}:{port}/api/v1/heartbeat"

    for _ in range(max_retries):
        try:
            response = requests.get(server_url)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(retry_interval)
    else:
        server_process.terminate()
        raise RuntimeError("ChromaDB server failed to start")

    yield

    # Stop ChromaDB server
    server_process.terminate()
    server_process.wait()


@pytest.fixture(scope="session")
def chroma_client(chroma_server) -> chromadb.HttpClient:
    """Create a ChromaDB client for testing.

    This fixture creates a shared client for the test session. Test isolation is maintained through:
    1. Unique collection names in doc_store fixture
    2. Explicit collection cleanup after each test
    3. Client reset after each test
    """
    client = chromadb.HttpClient(
        host=settings.chroma.host,
        port=settings.chroma.port,
        settings=chromadb.Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        ),
    )

    yield client

    # Clean up all collections at end of session
    client.reset()


@pytest.fixture(scope="function")
async def doc_store(chroma_client) -> AsyncGenerator[DocumentStore, None]:
    """Create a clean document store for each test.

    Args:
        chroma_client: ChromaDB client fixture

    Yields:
        DocumentStore: Document store instance
    """
    # Use a unique collection name for each test
    collection_name = f"test_docs_{os.urandom(4).hex()}"
    store = DocumentStore(
        collection_name=collection_name,
        host=settings.chroma.host,
        port=settings.chroma.port,
    )
    await store.initialize()

    yield store

    # Cleanup
    await store.clear()
    chroma_client.delete_collection(collection_name)


@pytest.fixture(scope="function")
async def mcp_server(doc_store) -> AsyncGenerator[MCPDocumentAnalysisServer, None]:
    """Create MCP server instance for testing.

    Args:
        doc_store: Document store fixture

    Yields:
        MCPDocumentAnalysisServer: Server instance
    """
    server = MCPDocumentAnalysisServer(
        host="localhost",
        port=8000,
        chroma_host=settings.chroma.host,
        chroma_port=settings.chroma.port,
    )
    await server.initialize()

    yield server

    # No cleanup needed - doc_store fixture handles it
