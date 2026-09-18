import asyncio
from typing import Any

import httpx2
from azure.core.credentials import TokenCredential
from mcp import Client
from mcp.client.streamable_http import streamable_http_client


class McpRetrievalError(RuntimeError):
    pass


async def retrieve_over_mcp(
    server_url: str,
    credential: TokenCredential,
    question: str,
) -> dict[str, Any]:
    try:
        access_token = await asyncio.to_thread(
            credential.get_token,
            "https://search.azure.com/.default",
        )
        async with httpx2.AsyncClient(
            headers={"Authorization": f"Bearer {access_token.token}"},
            timeout=httpx2.Timeout(30.0, read=300.0),
        ) as http_client:
            transport = streamable_http_client(server_url, http_client=http_client)
            async with Client(transport) as client:
                await client.list_tools()
                result = await client.call_tool(
                    "knowledge_base_retrieve",
                    {"query_variants": [question]},
                )
    except Exception as error:
        raise McpRetrievalError from error
    payload = result.model_dump(by_alias=True, exclude_none=True)
    if payload.get("isError"):
        raise McpRetrievalError
    return {"result": payload}