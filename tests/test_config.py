import unittest
from unittest.mock import patch

from app.backend.config import Settings, is_running_in_production, load_local_environment


class EnvironmentLoadingTests(unittest.TestCase):
    @patch("app.backend.config.load_azd_env")
    def test_loads_selected_azd_environment_locally(self, load_azd_env) -> None:
        with patch.dict("os.environ", {}, clear=True):
            load_local_environment()

        load_azd_env.assert_called_once_with(quiet=True)

    @patch("app.backend.config.load_azd_env")
    def test_skips_azd_environment_in_production(self, load_azd_env) -> None:
        with patch.dict("os.environ", {"RUNNING_IN_PRODUCTION": "true"}, clear=True):
            self.assertTrue(is_running_in_production())
            load_local_environment()

        load_azd_env.assert_not_called()

    @patch("app.backend.config.load_azd_env")
    def test_uses_supported_github_mcp_tools_by_default(self, load_azd_env) -> None:
        with patch.dict(
            "os.environ",
            {
                "AZURE_SEARCH_ENDPOINT": "https://example.search.windows.net",
                "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
                "AZURE_SEARCH_QUERY_KEY": "query-key",
                "AZURE_STORAGE_ACCOUNT_NAME": "storage",
            },
            clear=True,
        ):
            settings = Settings.from_environment()

        self.assertEqual(
            settings.github_mcp_tools,
            ("search_code", "search_issues", "get_file_contents", "issue_read", "pull_request_read"),
        )


if __name__ == "__main__":
    unittest.main()