"""Tests for the MCP protocol communication."""

import io
import anyio
import pytest
from mcp.server.stdio import stdio_server
from mcp.types import (
    JSONRPCMessage,
    JSONRPCRequest,
    JSONRPCResponse,
    TextContent,
    ServerCapabilities,
    CallToolResult,
)


@pytest.mark.anyio
async def test_mcp_protocol_stdio():
    """Test basic stdio server protocol communication."""
    stdin = io.StringIO()
    stdout = io.StringIO()

    # Prepare test messages
    messages = [
        # Test capabilities request
        JSONRPCMessage(
            root=JSONRPCRequest(jsonrpc="2.0", id=1, method="initialize", params={})
        ),
        # Test analyze document request
        JSONRPCMessage(
            root=JSONRPCRequest(
                jsonrpc="2.0",
                id=2,
                method="call_tool",
                params={
                    "name": "analyze_document",
                    "arguments": {"file_path": "test.pdf"},
                },
            )
        ),
    ]

    # Write test messages to stdin
    for message in messages:
        stdin.write(message.model_dump_json(by_alias=True, exclude_none=True) + "\n")
    stdin.seek(0)

    async with anyio.create_task_group() as tg:
        # Set up stdio server
        async with stdio_server(
            stdin=anyio.AsyncFile(stdin), stdout=anyio.AsyncFile(stdout)
        ) as (read_stream, write_stream):
            # Process initialize request
            message = await anext(read_stream)
            if isinstance(message, Exception):
                raise message

            # Verify initialize request
            assert message == JSONRPCMessage(
                root=JSONRPCRequest(jsonrpc="2.0", id=1, method="initialize", params={})
            )

            # Send initialize response
            await write_stream.send(
                JSONRPCMessage(
                    root=JSONRPCResponse(
                        jsonrpc="2.0",
                        id=1,
                        result=ServerCapabilities(
                            name="Document Analysis",
                            version="1.0.0",
                            description="Document analysis, summarization, and relationship mapping",
                        ).model_dump(),
                    )
                )
            )

            # Wait for the response to be written
            await anyio.sleep(0.1)

            # Process analyze document request
            message = await anext(read_stream)
            if isinstance(message, Exception):
                raise message

            # Verify analyze document request
            assert message == JSONRPCMessage(
                root=JSONRPCRequest(
                    jsonrpc="2.0",
                    id=2,
                    method="call_tool",
                    params={
                        "name": "analyze_document",
                        "arguments": {"file_path": "test.pdf"},
                    },
                )
            )

            # Send analyze document response
            await write_stream.send(
                JSONRPCMessage(
                    root=JSONRPCResponse(
                        jsonrpc="2.0",
                        id=2,
                        result=CallToolResult(
                            content=[TextContent(type="text", text="Analyzed test.pdf")]
                        ).model_dump(),
                    )
                )
            )

            # Wait for the response to be written
            await anyio.sleep(0.1)

            # Cancel the task group to clean up
            tg.cancel_scope.cancel()

    # Verify output
    stdout.seek(0)
    output_lines = stdout.readlines()
    assert len(output_lines) == 2

    received_responses = [
        JSONRPCMessage.model_validate_json(line.strip()) for line in output_lines
    ]

    # Verify initialize response
    init_response = received_responses[0]
    assert init_response.root.id == 1
    assert init_response.root.result["name"] == "Document Analysis"
    assert init_response.root.result["version"] == "1.0.0"

    # Verify analyze document response
    analyze_response = received_responses[1]
    assert analyze_response.root.id == 2
    assert analyze_response.root.result["content"][0]["text"] == "Analyzed test.pdf"
