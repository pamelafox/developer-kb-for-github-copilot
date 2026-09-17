import asyncio
import json
import unittest

from azure.core.exceptions import ServiceRequestError

from app.backend.main import app, azure_service_error


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
        self.assertIn(("/api/knowledge-bases", "GET"), routes)
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


if __name__ == "__main__":
    unittest.main()