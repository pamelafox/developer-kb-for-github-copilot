import unittest

from app.backend.config import Settings
from app.backend.main import build_mcp_config
from app.backend.naming import shared_resources


class McpConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            search_endpoint="https://example.search.windows.net",
            openai_endpoint="https://example.openai.azure.com",
            embedding_deployment="embedding",
            embedding_model="embedding",
            chat_deployment="chat",
            chat_model="chat",
            search_query_key="read-only-key",
            github_pat="server-only-token",
            github_mcp_url="https://api.githubcopilot.com/mcp/readonly",
            github_mcp_tools=("get_file_contents",),
            managed_identity_client_id=None,
        )

    def test_builds_query_key_config_for_documents(self) -> None:
        config = build_mcp_config(self.settings, shared_resources(), combined=False)

        self.assertIn("cocoarynth-kb-docs/mcp", config["url"])
        server = config["vscode"]["servers"]["cocoarynth-kb-docs"]
        self.assertEqual(server["headers"]["api-key"], "read-only-key")
        self.assertNotIn(self.settings.github_pat, str(config))

    def test_selects_combined_knowledge_base(self) -> None:
        config = build_mcp_config(self.settings, shared_resources(), combined=True)

        self.assertEqual(config["knowledgeBase"], "cocoarynth-kb-all")
        self.assertIn("api-version=2026-08-01-preview", config["url"])


if __name__ == "__main__":
    unittest.main()