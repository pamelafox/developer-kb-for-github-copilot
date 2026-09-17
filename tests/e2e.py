import json
import os
import re
import socket
import time
from collections.abc import Generator
from contextlib import closing
from multiprocessing import Process
from unittest import mock

import pytest
import requests
import uvicorn
from playwright.sync_api import Page, Route, expect

from app.backend.config import Settings
from app.backend.main import app


expect.set_options(timeout=10_000)

DOCUMENT_OVERVIEW = {
    "container": "knowledge",
    "documents": [
        {
            "name": "mapayca-markets-traceability-pilot-requirements.pdf",
            "size": 42000,
            "lastModified": "2026-09-16T12:00:00+00:00",
            "url": "/api/documents/content/mapayca-markets-traceability-pilot-requirements.pdf",
        },
        {
            "name": "origin-passport-support-runbook.pdf",
            "size": 38000,
            "lastModified": "2026-09-16T12:00:00+00:00",
            "url": "/api/documents/content/origin-passport-support-runbook.pdf",
        },
    ],
}

CHUNKS = {
    "index": "cocoarynth-documents-index",
    "document": "mapayca-markets-traceability-pilot-requirements.pdf",
    "chunks": [
        {
            "chunk_id": "chunk-1",
            "title": "Mapayca Markets pilot requirements",
            "chunk": "Inventory imports must use CSV format.",
            "page_number_from": 1,
            "page_number_to": 2,
            "image_path": None,
        }
    ],
}

RETRIEVAL = {
    "response": [
        {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        [{"ref_id": 0, "title": "Pilot requirements", "content": "Mapayca Markets requires CSV."}]
                    ),
                }
            ],
        }
    ],
    "activity": [
        {
            "type": "modelQueryPlanning",
            "id": 0,
            "modelName": "gpt-5.4-mini",
            "inputTokens": 640,
            "outputTokens": 32,
            "elapsedMs": 120,
        },
        {
            "type": "searchIndex",
            "id": 1,
            "knowledgeSourceName": "cocoarynth-documents-source",
            "count": 1,
            "elapsedMs": 14,
            "searchIndexArguments": {"search": "CSV export"},
        },
        {
            "type": "agenticReasoning",
            "id": 2,
            "reasoningTokens": 480,
            "retrievalReasoningEffort": {"kind": "low"},
        },
    ],
    "references": [
        {
            "type": "searchIndex",
            "id": "0",
            "activitySource": 1,
            "title": "Pilot requirements",
            "rerankerScore": 3.9,
            "sourceData": {"chunk": "Mapayca Markets requires CSV."},
        },
        {
            "type": "mcpServer",
            "id": "1",
            "activitySource": 2,
            "title": "cocoarynth-github-source search_code 1",
            "toolName": "search_code",
            "sourceData": {
                "content": json.dumps(
                    {
                        "total_count": 1,
                        "items": [{"name": "export.py", "path": "src/export.py"}],
                    }
                )
            },
        },
    ],
}

SEARCH_RESULTS = {
    "index": "cocoarynth-documents-index",
    "query": "CSV export",
    "matches": [
        {
            **CHUNKS["chunks"][0],
            "@search.score": 0.91,
            "@search.reranker_score": 3.75,
        }
    ],
}

CONFIGURATION = {
    "knowledgeBases": [
        {
            "name": "cocoarynth-kb-docs",
            "description": "Documents only",
            "outputMode": "extractiveData",
            "knowledgeSources": [{"name": "cocoarynth-documents-source"}],
        },
        {
            "name": "cocoarynth-kb-all",
            "description": "Documents and GitHub",
            "outputMode": "extractiveData",
            "retrievalInstructions": "Use documents and live GitHub evidence.",
            "models": [
                {
                    "kind": "azureOpenAI",
                    "azureOpenAIParameters": {
                        "deploymentId": "gpt-5.4-mini",
                        "modelName": "gpt-5.4-mini",
                    },
                }
            ],
            "knowledgeSources": [
                {"name": "cocoarynth-documents-source"},
                {"name": "cocoarynth-github-source"},
            ],
        },
    ],
    "knowledgeSources": [
        {
            "name": "cocoarynth-documents-source",
            "kind": "searchIndex",
            "description": "Workshop documents",
            "searchIndexParameters": {
                "searchIndexName": "cocoarynth-documents-index",
                "semanticConfigurationName": "semantic-configuration",
                "searchFields": [{"name": "chunk"}],
                "sourceDataFields": [{"name": "title"}, {"name": "chunk"}],
            },
        },
        {
            "name": "cocoarynth-github-source",
            "kind": "mcpServer",
            "description": "Live GitHub evidence",
            "mcpServerParameters": {
                "serverURL": "https://api.githubcopilot.com/mcp/readonly",
                "tools": [{"name": "get_file_contents"}, {"name": "issue_read"}],
            },
        },
    ],
}


def wait_for_server_ready(url: str, timeout: float = 10.0, check_interval: float = 0.2) -> None:
    error = "Server did not become ready."
    for _ in range(int(timeout / check_interval)):
        try:
            response = requests.get(f"{url}health", timeout=1)
            response.raise_for_status()
        except requests.RequestException as exc:
            error = str(exc)
            time.sleep(check_interval)
        else:
            return
    raise RuntimeError(error)


@pytest.fixture(scope="session")
def free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return server_socket.getsockname()[1]


def run_server(port: int, live_smoke: bool) -> None:
    if live_smoke:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")
        return

    with mock.patch.dict(
        os.environ,
        {
            "AZURE_SEARCH_ENDPOINT": "https://example.search.windows.net",
            "AZURE_SEARCH_QUERY_KEY": "test-query-key",
            "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
            "AZURE_OPENAI_CHAT_DEPLOYMENT": "gpt-5.4-mini",
            "AZURE_OPENAI_CHAT_MODEL": "gpt-5.4-mini",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-3-large",
            "AZURE_OPENAI_EMBEDDING_MODEL": "text-embedding-3-large",
            "GITHUB_LAB_PAT": "test-github-token",
            "AZURE_STORAGE_ACCOUNT_NAME": "examplestorage",
        },
        clear=True,
    ):
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")


@pytest.fixture(scope="session")
def live_server_url(
    free_port: int, live_smoke: bool, smoke_base_url: str | None
) -> Generator[str, None, None]:
    if smoke_base_url:
        url = f"{smoke_base_url.rstrip('/')}/"
        wait_for_server_ready(url, timeout=60)
        yield url
        return

    if live_smoke:
        try:
            settings = Settings.from_environment()
        except KeyError as exc:
            pytest.exit(
                f"Live smoke tests require a provisioned azd environment; missing {exc.args[0]}.",
                returncode=1,
            )
        if "example." in settings.search_endpoint:
            pytest.exit("Live smoke tests cannot use a placeholder Search endpoint.", returncode=1)

    process = Process(target=run_server, args=(free_port, live_smoke), daemon=True)
    process.start()
    url = f"http://127.0.0.1:{free_port}/"
    try:
        wait_for_server_ready(url)
        yield url
    finally:
        process.kill()
        process.join(timeout=5)


def mock_app_apis(page: Page, live_smoke: bool, document_error: bool = False) -> None:
    if live_smoke:
        return

    page.route(
        re.compile(r".*/api/documents$"),
        lambda route: route.fulfill(
            status=503 if document_error else 200,
            content_type="application/json",
            body=json.dumps(
                {"detail": "Search inventory is unavailable."} if document_error else DOCUMENT_OVERVIEW
            ),
        ),
    )
    page.route(
        re.compile(r".*/api/documents/chunks.*"),
        lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(CHUNKS)),
    )
    page.route(
        re.compile(r".*/api/documents/search$"),
        lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(SEARCH_RESULTS)),
    )
    page.route(
        re.compile(r".*/api/knowledge-bases$"),
        lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(CONFIGURATION)),
    )
    page.route(
        re.compile(r".*/api/mcp.*"),
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "url": "https://example.search.windows.net/knowledgebases/"
                    + ("cocoarynth-kb-all" if "combined=true" in route.request.url else "cocoarynth-kb-docs")
                    + "/mcp?api-version=2026-08-01-preview"
                }
            ),
        ),
    )


@pytest.mark.parametrize("viewport", [(390, 844), (768, 1024), (1280, 800)])
def test_home_is_responsive(
    page: Page, live_server_url: str, live_smoke: bool, viewport: tuple[int, int]
) -> None:
    mock_app_apis(page, live_smoke)
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(live_server_url)

    expect(page).to_have_title("Foundry IQ workshop portal")
    expect(page.get_by_role("heading", name="Knowledge explorer")).to_be_visible()
    expect(page.get_by_role("img", name="Cocoarynth")).to_be_visible()
    expect(page.get_by_role("img", name="Cocoarynth")).to_have_attribute(
        "src", re.compile(r"/assets/cocoarynth-mark\.png")
    )
    expect(page.locator("#prefix")).to_have_count(0)
    expect(page.locator("#create-combined")).to_have_count(0)
    assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")


def test_loads_corpus_inventory(page: Page, live_server_url: str, live_smoke: bool) -> None:
    mock_app_apis(page, live_smoke)
    page.goto(live_server_url)

    expect(page.locator("#document-list")).to_contain_text("mapayca-markets-traceability-pilot-requirements.pdf")
    expect(page.locator("#document-list a").first).to_have_attribute("href", re.compile(r"/api/documents/content/"))
    expect(page.locator("#documents .mcp-strip")).to_have_count(0)


def test_page_permalinks_and_browser_history(page: Page, live_server_url: str, live_smoke: bool) -> None:
    mock_app_apis(page, live_smoke)
    for path, panel_id in {
        "documents": "documents",
        "document-chunks": "chunks",
        "document-search": "search",
        "documents-kb": "documents-kb",
        "combined-kb": "combined-kb",
    }.items():
        page.goto(f"{live_server_url}{path}")
        expect(page.locator(f"#{panel_id}")).to_have_class(re.compile(r"\bactive\b"))
        expect(page).to_have_url(re.compile(rf"/{path}$"))

    page.goto(f"{live_server_url}document-search")

    expect(page.locator("#search")).to_have_class(re.compile(r"\bactive\b"))
    expect(page).to_have_url(re.compile(r"/document-search$"))

    page.get_by_role("button", name="Documents knowledge base", exact=True).click()
    expect(page.locator("#documents-kb")).to_have_class(re.compile(r"\bactive\b"))
    expect(page).to_have_url(re.compile(r"/documents-kb$"))

    page.go_back()
    expect(page.locator("#search")).to_have_class(re.compile(r"\bactive\b"))
    expect(page).to_have_url(re.compile(r"/document-search$"))


def test_loads_content_understanding_chunks(page: Page, live_server_url: str, live_smoke: bool) -> None:
    mock_app_apis(page, live_smoke)
    page.goto(live_server_url)
    page.get_by_role("button", name="Document chunks", exact=True).click()

    page.locator("#document-select").select_option(label="mapayca-markets-traceability-pilot-requirements.pdf")

    if live_smoke:
        expect(page.locator("#chunk-list")).to_contain_text("mapayca-markets-traceability-pilot-requirements.pdf")
        assert page.locator("#chunk-list article").count() > 1
    else:
        expect(page.locator("#chunk-list")).to_contain_text("Inventory imports must use CSV format.")
    expect(page.locator("#chunk-list")).to_contain_text("page_number_from")


def test_runs_hybrid_document_search(page: Page, live_server_url: str, live_smoke: bool) -> None:
    mock_app_apis(page, live_smoke)
    page.goto(live_server_url)
    page.get_by_role("button", name="Document search", exact=True).click()

    page.get_by_role("button", name="Search", exact=True).click()

    if live_smoke:
        expect(page.locator("#search-results article").first).to_be_visible()
    else:
        expect(page.locator("#search-results")).to_contain_text("Inventory imports must use CSV format.")
        expect(page.locator("#search-results")).to_contain_text("Reranker 3.750")
        expect(page.locator("#search-results")).to_contain_text("Search 0.910")
    expect(page.locator("#search-summary")).to_contain_text("hybrid semantic + vector")


def test_displays_knowledge_base_configuration(page: Page, live_server_url: str, live_smoke: bool) -> None:
    mock_app_apis(page, live_smoke)
    page.goto(live_server_url)
    page.get_by_role("button", name="Documents knowledge base", exact=True).click()

    documents_config = page.locator("#documents-kb-configuration")
    expect(documents_config).to_contain_text("cocoarynth-kb-docs")
    expect(documents_config).to_contain_text("cocoarynth-documents-source")
    expect(documents_config).not_to_contain_text("cocoarynth-github-source")
    expect(documents_config).not_to_contain_text("Bearer")
    expect(documents_config.locator(".configuration-item")).to_have_count(1)
    expect(documents_config.locator(".config-facts").first).to_contain_text("Description")
    expect(documents_config.locator(".config-details")).to_have_count(0)

    page.get_by_role("button", name="Combined knowledge base", exact=True).click()
    combined_config = page.locator("#combined-kb-configuration")
    expect(combined_config).to_contain_text("cocoarynth-kb-all")
    expect(combined_config).to_contain_text("cocoarynth-documents-source")
    expect(combined_config).to_contain_text("cocoarynth-github-source")
    expect(combined_config).not_to_contain_text("Bearer")
    expect(combined_config.locator(".configuration-item")).to_have_count(1)
    expect(combined_config.locator(".config-facts").first).to_contain_text("Use documents and live GitHub evidence.")
    expect(combined_config.locator(".config-facts").first).to_contain_text("gpt-5.4-mini")
    document_source = combined_config.locator(".source-row").filter(has_text="cocoarynth-documents-source")
    expect(document_source.locator("h4")).to_have_text("cocoarynth-documents-source")
    expect(document_source.locator(".source-facts")).to_contain_text("KindsearchIndex")
    expect(document_source.locator(".source-facts")).to_contain_text("cocoarynth-documents-index")
    expect(document_source.locator(".source-facts")).to_contain_text("semantic-configuration")
    github_source = combined_config.locator(".source-row").filter(has_text="cocoarynth-github-source")
    expect(github_source.locator(".source-facts")).to_contain_text("KindmcpServer")
    expect(github_source.locator(".source-facts")).to_contain_text(
        "https://api.githubcopilot.com/mcp/readonly"
    )
    expect(github_source.locator(".source-facts")).to_contain_text("get_file_contents, issue_read")
    expect(combined_config.get_by_text("Inspect source configuration")).to_have_count(0)


def test_retrieves_from_both_shared_knowledge_bases(
    page: Page, live_server_url: str, live_smoke: bool
) -> None:
    payloads: list[dict] = []
    mock_app_apis(page, live_smoke)

    def handle_retrieval(route: Route) -> None:
        payloads.append(route.request.post_data_json)
        route.fulfill(status=200, content_type="application/json", body=json.dumps(RETRIEVAL))

    if live_smoke:
        page.set_default_timeout(180_000)
        page.on(
            "request",
            lambda request: payloads.append(request.post_data_json)
            if request.url.endswith("/api/retrieve")
            else None,
        )
    else:
        page.route(re.compile(r".*/api/retrieve$"), handle_retrieval)
    page.goto(live_server_url)
    page.get_by_role("button", name="Documents knowledge base", exact=True).click()
    page.get_by_role("button", name="Search documents KB", exact=True).click()
    if live_smoke:
        expect(page.locator("#documents-kb .kb-output article").first).to_be_visible()
    else:
        expect(page.locator("#documents-kb .kb-output")).to_contain_text("Mapayca Markets requires CSV.")
    activity = page.locator("#documents-kb .activity-table")
    expect(activity).to_contain_text("Index search")
    if live_smoke:
        expect(activity).to_contain_text("Input")
        expect(activity).to_contain_text("Output")
        expect(activity).to_contain_text("Reasoning")
    else:
        expect(activity).to_contain_text("Input 640")
        expect(activity).to_contain_text("Output 32")
        expect(activity).to_contain_text("Reasoning 480")
    expect(activity.locator(".token-meter")).to_have_count(2)

    page.get_by_role("button", name="Combined knowledge base", exact=True).click()
    page.get_by_role("button", name="Search combined KB", exact=True).click()
    if live_smoke:
        expect(page.locator("#combined-kb .kb-output article").first).to_be_visible()
    else:
        expect(page.locator("#combined-kb .kb-output")).to_contain_text("Mapayca Markets requires CSV.")
        references = page.locator("#combined-kb .reference-list")
        expect(references).to_contain_text("cocoarynth-github-source search_code 1")
        expect(references).to_contain_text('"path": "src/export.py"')

    assert [payload["combined"] for payload in payloads] == [False, True]
    assert all("prefix" not in payload for payload in payloads)


def test_generates_both_shared_mcp_configs(
    page: Page, live_server_url: str, live_smoke: bool
) -> None:
    mock_app_apis(page, live_smoke)
    page.goto(live_server_url)
    page.get_by_role("button", name="Documents knowledge base", exact=True).click()

    expect(page.locator('#documents-kb-configuration .config-facts > .mcp-strip[data-kb="documents"] code')).to_contain_text(
        "cocoarynth-kb-docs"
    )
    expect(page.locator('#combined-kb-configuration .config-facts > .mcp-strip[data-kb="combined"] code')).to_contain_text(
        "cocoarynth-kb-all"
    )
    expect(page.locator("#documents-kb-configuration .config-facts").first).to_contain_text("MCP URL")
    expect(page.locator("#combined-kb-configuration .config-facts").first).to_contain_text("MCP URL")
    expect(page.locator(".mcp-strip")).to_have_count(2)
    expect(page.locator("#chunks .mcp-strip, #search .mcp-strip")).to_have_count(0)


def test_inventory_error_is_visible(page: Page, live_server_url: str, live_smoke: bool) -> None:
    if live_smoke:
        pytest.skip("The intentional mocked failure is not part of live smoke testing.")
    mock_app_apis(page, live_smoke, document_error=True)
    page.goto(live_server_url)

    expect(page.locator("#toast")).to_have_text("Search inventory is unavailable.")
    expect(page.locator("#toast")).to_have_class(re.compile(r"\bshow\b"))
