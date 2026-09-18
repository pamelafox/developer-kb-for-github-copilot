import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from azure.core.exceptions import ServiceRequestError

from app.backend.main import (
    McpRetrievalRequest,
    app,
    azure_service_error,
    mcp_retrieve,
    mcp_service_error,
)
from app.backend.mcp_client import McpRetrievalError


class RouteContractTests(unittest.TestCase):
    def test_document_routes_are_read_only(self) -> None:
        routes = {
            (route.path, method)
            for route in app.routes
            for method in getattr(route, "methods", set())
        }

        self.assertIn(("/api/documents", "GET"), routes)
        self.assertIn(("/api/documents/content/{blob_name:path}", "GET"), routes)
        self.assertIn(("/api/documents/chunks", "GET"), routes)
        self.assertIn(("/api/documents/search", "POST"), routes)
        self.assertIn(("/api/engineering-practices", "GET"), routes)
        self.assertIn(("/api/engineering-practices/content/{blob_name:path}", "GET"), routes)
        self.assertIn(("/api/engineering-practices/chunks", "GET"), routes)
        self.assertIn(("/api/engineering-practices/search", "POST"), routes)
        self.assertIn(("/api/knowledge-bases", "GET"), routes)
        self.assertIn(("/api/mcp/retrieve", "POST"), routes)
        self.assertNotIn(("/api/mcp", "GET"), routes)
        self.assertNotIn(("/api/uploads", "POST"), routes)
        self.assertNotIn(("/api/workspaces", "POST"), routes)
        self.assertNotIn(("/api/workspaces/combined", "POST"), routes)
        self.assertFalse(any(method == "DELETE" for _, method in routes))

    def test_azure_service_failures_return_actionable_503(self) -> None:
        response = asyncio.run(
            azure_service_error(None, ServiceRequestError("Search endpoint could not be resolved."))  # type: ignore[arg-type]
        )

        self.assertEqual(503, response.status_code)
        self.assertIn("Verify AZURE_SEARCH_ENDPOINT", json.loads(response.body)["detail"])

    def test_mcp_service_failures_return_actionable_503(self) -> None:
        response = asyncio.run(mcp_service_error(None, McpRetrievalError()))  # type: ignore[arg-type]

        self.assertEqual(503, response.status_code)
        self.assertIn("knowledge base", json.loads(response.body)["detail"])

    @patch("app.backend.main.retrieve_over_mcp", new_callable=AsyncMock)
    def test_mcp_route_targets_selected_knowledge_base(self, retrieve: AsyncMock) -> None:
        retrieve.return_value = {"result": {"content": []}}
        credential = object()
        request = SimpleNamespace(
            app=SimpleNamespace(
                state=SimpleNamespace(
                    settings=SimpleNamespace(
                        search_endpoint="https://example.search.windows.net",
                    ),
                    credential=credential,
                )
            )
        )

        result = asyncio.run(
            mcp_retrieve(
                McpRetrievalRequest(question="How should docs be written?", target="engineering-practices"),
                request,
            )
        )

        self.assertEqual(result, {"result": {"content": []}})
        retrieve.assert_awaited_once_with(
            "https://example.search.windows.net/knowledgebases/"
            "cocoarynth-kb-engineering-practices/mcp?api-version=2026-08-01-preview",
            credential,
            "How should docs be written?",
        )


if __name__ == "__main__":
    unittest.main()