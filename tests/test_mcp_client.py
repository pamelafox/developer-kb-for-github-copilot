import asyncio
import unittest
from unittest.mock import Mock, patch

from app.backend.mcp_client import McpRetrievalError, retrieve_over_mcp


class AsyncContext:
    def __init__(self, value=None, **kwargs) -> None:
        self.value = value or self
        self.kwargs = kwargs

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, *_args) -> None:
        return None


class McpClientTests(unittest.TestCase):
    @patch("app.backend.mcp_client.Client")
    @patch("app.backend.mcp_client.streamable_http_client")
    @patch("app.backend.mcp_client.httpx2.AsyncClient")
    def test_calls_retrieve_tool_with_bearer_token(
        self,
        http_client_type: Mock,
        streamable_http_client: Mock,
        client_type: Mock,
    ) -> None:
        http_client = AsyncContext()
        http_client_type.return_value = http_client
        transport = object()
        streamable_http_client.return_value = transport
        client = Mock()
        client.list_tools = Mock(return_value=asyncio.sleep(0))
        result = Mock()
        result.model_dump.return_value = {
            "content": [{"type": "text", "text": "grounding"}],
            "isError": False,
        }
        client.call_tool = Mock(return_value=asyncio.sleep(0, result))
        client_type.return_value = AsyncContext(client)
        credential = Mock()
        credential.get_token.return_value = Mock(token="access-token")

        response = asyncio.run(
            retrieve_over_mcp(
                "https://example.search.windows.net/knowledgebases/kb/mcp",
                credential,
                "What changed?",
            )
        )

        self.assertEqual(response["result"]["content"][0]["text"], "grounding")
        credential.get_token.assert_called_once_with("https://search.azure.com/.default")
        self.assertEqual(
            http_client_type.call_args.kwargs["headers"],
            {"Authorization": "Bearer access-token"},
        )
        streamable_http_client.assert_called_once_with(
            "https://example.search.windows.net/knowledgebases/kb/mcp",
            http_client=http_client,
        )
        client_type.assert_called_once_with(transport)
        client.list_tools.assert_called_once_with()
        client.call_tool.assert_called_once_with(
            "knowledge_base_retrieve",
            {"query_variants": ["What changed?"]},
        )

    @patch("app.backend.mcp_client.Client")
    @patch("app.backend.mcp_client.streamable_http_client")
    @patch("app.backend.mcp_client.httpx2.AsyncClient")
    def test_raises_when_tool_returns_protocol_error(
        self,
        http_client_type: Mock,
        streamable_http_client: Mock,
        client_type: Mock,
    ) -> None:
        http_client_type.return_value = AsyncContext()
        streamable_http_client.return_value = object()
        client = Mock()
        client.list_tools = Mock(return_value=asyncio.sleep(0))
        result = Mock()
        result.model_dump.return_value = {
            "content": [{"type": "text", "text": "Knowledge base not found"}],
            "isError": True,
        }
        client.call_tool = Mock(return_value=asyncio.sleep(0, result))
        client_type.return_value = AsyncContext(client)
        credential = Mock()
        credential.get_token.return_value = Mock(token="access-token")

        with self.assertRaises(McpRetrievalError):
            asyncio.run(
                retrieve_over_mcp(
                    "https://example.search.windows.net/knowledgebases/kb/mcp",
                    credential,
                    "What changed?",
                )
            )


if __name__ == "__main__":
    unittest.main()