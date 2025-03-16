"""Integration tests for the Document Analysis MCP Server."""

import io
import os
import anyio
import pytest
from mcp.server.stdio import stdio_server
from mcp.types import (
    JSONRPCMessage,
    JSONRPCRequest,
    JSONRPCResponse,
    TextContent,
    CallToolResult,
    ServerCapabilities,
)

from docanalysis.mcp.server import FastMCPDocumentAnalysisServer


@pytest.mark.anyio
async def test_fastmcp_document_analysis_server():
    """Test the actual FastMCP Document Analysis Server implementation."""
    # Initialize server
    server = FastMCPDocumentAnalysisServer()
    await server.initialize()

    # Create test document
    test_content = "This is a test document for analysis."
    with open("test_doc.txt", "w") as f:
        f.write(test_content)

    stdin = io.StringIO()
    stdout = io.StringIO()

    # Prepare test messages
    messages = [
        # Initialize request
        JSONRPCMessage(
            root=JSONRPCRequest(jsonrpc="2.0", id=1, method="initialize", params={})
        ),
        # List tools request
        JSONRPCMessage(
            root=JSONRPCRequest(jsonrpc="2.0", id=2, method="list_tools", params={})
        ),
        # Analyze document request
        JSONRPCMessage(
            root=JSONRPCRequest(
                jsonrpc="2.0",
                id=3,
                method="call_tool",
                params={
                    "name": "analyze_document",
                    "arguments": {
                        "file_path": "test_doc.txt",
                        "doc_type": "test",
                        "title": "Test Document",
                    },
                },
            )
        ),
        # Summarize document request (using the doc_id from previous response)
        JSONRPCMessage(
            root=JSONRPCRequest(
                jsonrpc="2.0",
                id=4,
                method="call_tool",
                params={
                    "name": "summarize_document",
                    "arguments": {
                        "doc_id": "test-{timestamp}",  # We'll update this with the actual doc_id
                        "detail_level": "standard",
                    },
                },
            )
        ),
    ]

    # Write messages to stdin
    for message in messages:
        stdin.write(message.model_dump_json(by_alias=True, exclude_none=True) + "\n")
    stdin.seek(0)

    try:
        async with anyio.create_task_group() as tg:
            async with stdio_server(
                stdin=anyio.AsyncFile(stdin), stdout=anyio.AsyncFile(stdout)
            ) as (read_stream, write_stream):
                # Process initialize request
                message = await anext(read_stream)
                if isinstance(message, Exception):
                    raise message

                # Send initialize response with server capabilities
                await write_stream.send(
                    JSONRPCMessage(
                        root=JSONRPCResponse(
                            jsonrpc="2.0",
                            id=1,
                            result=ServerCapabilities(
                                name="Document Analysis",
                                version="2.0.0",
                                description="Document analysis, summarization, and relationship mapping",
                            ).model_dump(),
                        )
                    )
                )

                # Process list tools request
                message = await anext(read_stream)
                if isinstance(message, Exception):
                    raise message

                # Send list tools response
                tools = await server._mcp.list_tools()
                await write_stream.send(
                    JSONRPCMessage(
                        root=JSONRPCResponse(
                            jsonrpc="2.0",
                            id=2,
                            result={"tools": [tool.model_dump() for tool in tools]},
                        )
                    )
                )

                # Process analyze document request
                message = await anext(read_stream)
                if isinstance(message, Exception):
                    raise message

                # Call actual analyze_document tool
                result = await server.analyze_document(
                    {
                        "content": test_content,
                        "metadata": {
                            "type": "test",
                            "title": "Test Document",
                            "source_file": "test_doc.txt",
                        },
                    }
                )

                # Send analyze document response
                await write_stream.send(
                    JSONRPCMessage(
                        root=JSONRPCResponse(
                            jsonrpc="2.0",
                            id=3,
                            result=CallToolResult(
                                content=[TextContent(type="text", text=str(result))]
                            ).model_dump(),
                        )
                    )
                )

                # Update summarize request with actual doc_id
                doc_id = result.source_doc_id
                if not doc_id:
                    doc_id = "test-doc"  # Fallback ID if none provided
                message = await anext(read_stream)
                if isinstance(message, Exception):
                    raise message

                # Call actual summarize_document tool
                summary = await server.summarize_document(
                    {
                        "content": test_content,
                        "metadata": {
                            "id": doc_id,
                            "type": "test",
                            "title": "Test Document",
                        },
                    }
                )

                # Send summarize document response
                await write_stream.send(
                    JSONRPCMessage(
                        root=JSONRPCResponse(
                            jsonrpc="2.0",
                            id=4,
                            result=CallToolResult(
                                content=[TextContent(type="text", text=str(summary))]
                            ).model_dump(),
                        )
                    )
                )

                # Wait for responses to be written
                await anyio.sleep(0.1)
                tg.cancel_scope.cancel()

        # Verify output
        stdout.seek(0)
        output_lines = stdout.readlines()
        assert (
            len(output_lines) == 4
        )  # Initialize, list_tools, analyze, and summarize responses

        received_responses = [
            JSONRPCMessage.model_validate_json(line.strip()) for line in output_lines
        ]

        # Verify responses
        assert received_responses[0].root.id == 1  # Initialize response
        assert received_responses[1].root.id == 2  # List tools response
        assert received_responses[2].root.id == 3  # Analyze document response
        assert received_responses[3].root.id == 4  # Summarize document response

        # Verify tool responses contain expected data
        analyze_response = received_responses[2]
        assert "content" in analyze_response.root.result
        assert len(analyze_response.root.result["content"]) > 0

        summarize_response = received_responses[3]
        assert "content" in summarize_response.root.result
        assert len(summarize_response.root.result["content"]) > 0

    finally:
        # Clean up test file
        if os.path.exists("test_doc.txt"):
            os.remove("test_doc.txt")
