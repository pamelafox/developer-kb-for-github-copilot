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

ENGINEERING_PRACTICE_OVERVIEW = {
    "container": "engineering-practices",
    "documents": [
        {
            "name": "cocoarynth-engineering-culture-presentation.pdf",
            "size": 52000,
            "lastModified": "2026-09-17T12:00:00+00:00",
            "url": "/api/engineering-practices/content/cocoarynth-engineering-culture-presentation.pdf",
        }
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

ENGINEERING_PRACTICE_CHUNKS = {
    "index": "cocoarynth-engineering-practices-index",
    "document": "cocoarynth-engineering-culture-presentation.pdf",
    "chunks": [
        {
            "chunk_id": "style-chunk-1",
            "title": "Engineering Culture",
            "chunk": "Code review is both a quality gate and a teaching system.",
            "page_number_from": 19,
            "page_number_to": 19,
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
            "type": "searchIndex",
            "id": 2,
            "knowledgeSourceName": "cocoarynth-engineering-practices-source",
            "count": 1,
            "elapsedMs": 11,
            "searchIndexArguments": {"search": "CSV API accessibility standards"},
        },
        {
            "type": "agenticReasoning",
            "id": 3,
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
            "type": "searchIndex",
            "id": "1",
            "activitySource": 2,
            "title": "API Design and Export Contracts Guide",
            "sourceData": {"chunk": "Generate CSV with a standards-based library."},
        },
    ],
}

MCP_RETRIEVAL = {
    "result": {
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    [{"ref_id": "0", "title": "Pilot requirements", "content": "Mapayca Markets requires CSV."}]
                ),
            }
        ],
        "isError": False,
    }
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

ENGINEERING_PRACTICE_SEARCH_RESULTS = {
    "index": "cocoarynth-engineering-practices-index",
    "query": "testing review rollout and monitoring standards",
    "matches": [
        {
            **ENGINEERING_PRACTICE_CHUNKS["chunks"][0],
            "@search.score": 0.88,
            "@search.reranker_score": 3.61,
        }
    ],
}

CONFIGURATION = {
    "knowledgeBases": [
        {
            "name": "cocoarynth-kb-docs",
            "description": "Documents only",
            "outputMode": "extractiveData",
            "rerankerThreshold": 1.7,
            "mcpUrl": "https://example.search.windows.net/knowledgebases/cocoarynth-kb-docs/mcp?api-version=2026-08-01-preview",
            "knowledgeSources": [{"name": "cocoarynth-documents-source"}],
        },
        {
            "name": "cocoarynth-kb-engineering-practices",
            "description": "Engineering practices only",
            "outputMode": "extractiveData",
            "rerankerThreshold": 1.7,
            "retrievalReasoningEffort": {"kind": "minimal"},
            "mcpUrl": "https://example.search.windows.net/knowledgebases/cocoarynth-kb-engineering-practices/mcp?api-version=2026-08-01-preview",
            "knowledgeSources": [{"name": "cocoarynth-engineering-practices-source"}],
        },
        {
            "name": "cocoarynth-kb-all",
            "description": "Project documents and company engineering practices",
            "outputMode": "extractiveData",
            "rerankerThreshold": 1.7,
            "retrievalReasoningEffort": {"kind": "low"},
            "mcpUrl": "https://example.search.windows.net/knowledgebases/cocoarynth-kb-all/mcp?api-version=2026-08-01-preview",
            "retrievalInstructions": (
                "Use project documents for product requirements, architecture decisions, policies, and support "
                "constraints. Use company engineering practices for React, API, frontend design, accessibility, "
                "and engineering culture. Distinguish product requirements from implementation guidance and cite "
                "factual claims."
            ),
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
                {"name": "cocoarynth-engineering-practices-source"},
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
                "sourceDataFields": [{"name": "title"}],
            },
        },
        {
            "name": "cocoarynth-engineering-practices-source",
            "kind": "searchIndex",
            "description": "Company engineering practices",
            "searchIndexParameters": {
                "searchIndexName": "cocoarynth-engineering-practices-index",
                "semanticConfigurationName": "semantic-configuration",
                "searchFields": [{"name": "chunk"}],
                "sourceDataFields": [{"name": "title"}],
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
            "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com",
            "AZURE_OPENAI_CHAT_DEPLOYMENT": "gpt-5.4-mini",
            "AZURE_OPENAI_CHAT_MODEL": "gpt-5.4-mini",
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": "text-embedding-3-large",
            "AZURE_OPENAI_EMBEDDING_MODEL": "text-embedding-3-large",
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
        re.compile(r".*/api/engineering-practices$"),
        lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(ENGINEERING_PRACTICE_OVERVIEW)),
    )
    page.route(
        re.compile(r".*/api/engineering-practices/chunks.*"),
        lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(ENGINEERING_PRACTICE_CHUNKS)),
    )
    page.route(
        re.compile(r".*/api/engineering-practices/search$"),
        lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(ENGINEERING_PRACTICE_SEARCH_RESULTS)),
    )
    page.route(
        re.compile(r".*/api/knowledge-bases$"),
        lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(CONFIGURATION)),
    )
    page.route(
        re.compile(r".*/api/mcp/retrieve$"),
        lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps(MCP_RETRIEVAL)),
    )
@pytest.mark.parametrize("viewport", [(390, 844), (768, 1024), (1280, 800)])
def test_home_is_responsive(
    page: Page, live_server_url: str, live_smoke: bool, viewport: tuple[int, int]
) -> None:
    mock_app_apis(page, live_smoke)
    page.set_viewport_size({"width": viewport[0], "height": viewport[1]})
    page.goto(live_server_url)

    expect(page).to_have_title("Foundry IQ workshop portal")
    expect(page.get_by_role("heading", name="Workshop portal")).to_be_visible()
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
        "project-requirements": "documents",
        "project-requirements/chunks": "chunks",
        "project-requirements/search": "search",
        "project-requirements/mcp": "documents-mcp",
        "engineering-practices": "engineering-practices",
        "engineering-practices/chunks": "engineering-practices-chunks",
        "engineering-practices/search": "engineering-practices-search",
        "engineering-practices/mcp": "engineering-practices-mcp",
        "combined/configuration": "combined-configuration",
        "combined/query": "combined-kb",
        "combined/mcp": "combined-mcp",
    }.items():
        page.goto(f"{live_server_url}{path}")
        expect(page.locator(f"#{panel_id}")).to_have_class(re.compile(r"\bactive\b"))
        expect(page).to_have_url(re.compile(rf"/{path}$"))

    page.goto(f"{live_server_url}project-requirements/search")

    expect(page.locator("#search")).to_have_class(re.compile(r"\bactive\b"))
    expect(page).to_have_url(re.compile(r"/project-requirements/search$"))

    page.locator('.nav-group').filter(has_text="Corpus 1: Project requirements").get_by_role("button", name="Call over MCP", exact=True).click()
    expect(page.locator("#documents-mcp")).to_have_class(re.compile(r"\bactive\b"))
    expect(page).to_have_url(re.compile(r"/project-requirements/mcp$"))

    page.go_back()
    expect(page.locator("#search")).to_have_class(re.compile(r"\bactive\b"))
    expect(page).to_have_url(re.compile(r"/project-requirements/search$"))


def test_loads_content_understanding_chunks(page: Page, live_server_url: str, live_smoke: bool) -> None:
    mock_app_apis(page, live_smoke)
    page.goto(live_server_url)
    page.locator('.nav-group').filter(has_text="Corpus 1: Project requirements").get_by_role("button", name="View document chunks", exact=True).click()

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
    page.locator('.nav-group').filter(has_text="Corpus 1: Project requirements").get_by_role("button", name="Search the index", exact=True).click()

    page.get_by_role("button", name="Search", exact=True).click()

    if live_smoke:
        expect(page.locator("#search-results article").first).to_be_visible()
    else:
        expect(page.locator("#search-results")).to_contain_text("Inventory imports must use CSV format.")
        expect(page.locator("#search-results")).to_contain_text("Reranker 3.750")
        expect(page.locator("#search-results")).to_contain_text("Search 0.910")
    expect(page.locator("#search-summary")).to_contain_text("hybrid semantic + vector")


def test_explores_engineering_practice_index(page: Page, live_server_url: str, live_smoke: bool) -> None:
    mock_app_apis(page, live_smoke)
    page.goto(live_server_url)

    page.locator('.nav-group').filter(has_text="Corpus 2: Engineering practices").get_by_role("button", name="Browse documents", exact=True).click()
    expect(page.locator("#engineering-practices-list")).to_contain_text("cocoarynth-engineering-culture-presentation.pdf")

    page.locator('.nav-group').filter(has_text="Corpus 2: Engineering practices").get_by_role("button", name="View document chunks", exact=True).click()
    page.locator("#engineering-practices-select").select_option(label="cocoarynth-engineering-culture-presentation.pdf")
    expect(page.locator("#engineering-practices-chunk-summary")).to_contain_text("cocoarynth-engineering-practices-index")
    expect(page.locator("#engineering-practices-chunk-list")).to_contain_text("Code review")

    page.locator('.nav-group').filter(has_text="Corpus 2: Engineering practices").get_by_role("button", name="Search the index", exact=True).click()
    page.locator("#engineering-practices-search-form").get_by_role("button", name="Search").click()
    expect(page.locator("#engineering-practices-search-summary")).to_contain_text("cocoarynth-engineering-practices-index")
    expect(page.locator("#engineering-practices-search-results")).to_contain_text("Engineering Culture")


def test_part3_portal_workflow(page: Page, live_server_url: str, live_smoke: bool) -> None:
    if live_smoke:
        pytest.skip("Model-judged workshop acceptance is covered by tests/live_smoke.py.")
    mock_app_apis(page, live_smoke)
    mcp_payloads: list[dict] = []
    search_payloads: list[dict] = []

    page.on(
        "request",
        lambda request: search_payloads.append(request.post_data_json)
        if request.url.endswith("/api/documents/search")
        else None,
    )

    def handle_mcp_retrieval(route: Route) -> None:
        mcp_payloads.append(route.request.post_data_json)
        route.fulfill(status=200, content_type="application/json", body=json.dumps(MCP_RETRIEVAL))

    page.route(re.compile(r".*/api/mcp/retrieve$"), handle_mcp_retrieval)
    page.goto(live_server_url)
    corpus = page.locator(".nav-group").filter(has_text="Corpus 1: Project requirements")

    corpus.get_by_role("button", name="Browse documents", exact=True).click()
    expect(page.locator("#document-list")).to_contain_text("mapayca-markets-traceability-pilot-requirements.pdf")

    corpus.get_by_role("button", name="View document chunks", exact=True).click()
    page.locator("#document-select").select_option(label="mapayca-markets-traceability-pilot-requirements.pdf")
    expect(page.locator("#chunk-list")).to_contain_text("Inventory imports must use CSV format.")
    expect(page.locator("#chunk-list")).to_contain_text("page_number_from")

    corpus.get_by_role("button", name="Search the index", exact=True).click()
    for query in ("CSV export requirements", "information excluded from wholesale exports"):
        page.locator("#search-query").fill(query)
        page.locator("#search-form").get_by_role("button", name="Search").click()
        expect(page.locator("#search-summary")).to_contain_text("cocoarynth-documents-index")
        expect(page.locator("#search-results")).to_contain_text("Inventory imports must use CSV format.")

    corpus.get_by_role("button", name="Call over MCP", exact=True).click()
    question = "What must change in the Origin Passport export for the Mapayça Markets pilot?"
    page.locator('#documents-mcp textarea').fill(question)
    page.locator("#documents-mcp").get_by_role("button", name="Call over MCP").click()
    expect(page.locator("#documents-mcp .mcp-output")).to_contain_text("Mapayca Markets requires CSV.")
    expect(page.locator("#documents-mcp .mcp-output")).to_contain_text("MCP content · 1 blocks")
    assert page.locator("#documents-mcp .mcp-content-block pre").text_content().startswith(
        '[\n  {\n    "ref_id": "0",'
    )

    assert [payload["query"] for payload in search_payloads] == [
        "CSV export requirements",
        "information excluded from wholesale exports",
    ]
    assert mcp_payloads == [{"question": question, "target": "documents"}]


def test_part4_portal_workflow(page: Page, live_server_url: str, live_smoke: bool) -> None:
    if live_smoke:
        pytest.skip("Model-judged workshop acceptance is covered by tests/live_smoke.py.")
    mock_app_apis(page, live_smoke)
    retrieval_payloads: list[dict] = []

    def handle_retrieval(route: Route) -> None:
        retrieval_payloads.append(route.request.post_data_json)
        route.fulfill(status=200, content_type="application/json", body=json.dumps(RETRIEVAL))

    page.route(re.compile(r".*/api/retrieve$"), handle_retrieval)
    page.goto(live_server_url)
    combined = page.locator(".nav-group").filter(has_text="Combined knowledge base")
    combined.get_by_role("button", name="Configuration", exact=True).click()

    configuration = page.locator("#combined-kb-configuration")
    expect(configuration).to_contain_text("cocoarynth-kb-all")
    expect(configuration).to_contain_text("Reranker threshold1.7")
    expect(configuration).to_contain_text("Reasoninglow")
    for source_name, index_name in (
        ("cocoarynth-documents-source", "cocoarynth-documents-index"),
        ("cocoarynth-engineering-practices-source", "cocoarynth-engineering-practices-index"),
    ):
        source = configuration.locator(".source-row").filter(has_text=source_name)
        expect(source.locator(".source-facts")).to_contain_text("KindsearchIndex")
        expect(source.locator(".source-facts")).to_contain_text(index_name)

    combined.get_by_role("button", name="Query knowledge base", exact=True).click()
    question = "What product requirements and company engineering standards should guide CSV Origin Passport support? Cite evidence from both corpora."
    page.locator('#combined-kb textarea').fill(question)
    page.locator("#combined-kb").get_by_role("button", name="Search combined KB").click()
    activity = page.locator("#combined-kb .activity-table")
    references = page.locator("#combined-kb .reference-list")
    expect(activity).to_contain_text("cocoarynth-documents-source")
    expect(activity).to_contain_text("CSV export")
    expect(activity).to_contain_text("cocoarynth-engineering-practices-source")
    expect(activity).to_contain_text("CSV API accessibility standards")
    expect(references).to_contain_text("Pilot requirements")
    expect(references).to_contain_text("API Design and Export Contracts Guide")
    assert retrieval_payloads == [{"question": question, "combined": True}]


def test_displays_knowledge_base_configuration(page: Page, live_server_url: str, live_smoke: bool) -> None:
    mock_app_apis(page, live_smoke)
    page.goto(live_server_url)
    page.locator(".nav-group").filter(has_text="Combined knowledge base").get_by_role("button", name="Configuration", exact=True).click()
    combined_config = page.locator("#combined-kb-configuration")
    expect(combined_config).to_contain_text("cocoarynth-kb-all")
    expect(combined_config).to_contain_text("cocoarynth-documents-source")
    expect(combined_config).to_contain_text("cocoarynth-engineering-practices-source")
    expect(combined_config).not_to_contain_text("Bearer")
    expect(combined_config.locator(".configuration-item")).to_have_count(1)
    expect(combined_config.locator(".config-facts").first).to_contain_text(
        "Use project documents for product requirements"
    )
    expect(combined_config.locator(".config-facts").first).to_contain_text("gpt-5.4-mini")
    document_source = combined_config.locator(".source-row").filter(has_text="cocoarynth-documents-source")
    expect(document_source.locator("h4")).to_have_text("cocoarynth-documents-source")
    expect(document_source.locator(".source-facts")).to_contain_text("KindsearchIndex")
    expect(document_source.locator(".source-facts")).to_contain_text("cocoarynth-documents-index")
    expect(document_source.locator(".source-facts")).to_contain_text("semantic-configuration")
    style_source = combined_config.locator(".source-row").filter(has_text="cocoarynth-engineering-practices-source")
    expect(style_source.locator(".source-facts")).to_contain_text("KindsearchIndex")
    expect(style_source.locator(".source-facts")).to_contain_text("cocoarynth-engineering-practices-index")
    expect(style_source.locator(".source-facts")).to_contain_text("semantic-configuration")
    expect(combined_config.get_by_text("Inspect source configuration")).to_have_count(0)


def test_retrieves_from_combined_knowledge_base(
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
    page.locator(".nav-group").filter(has_text="Combined knowledge base").get_by_role("button", name="Query knowledge base", exact=True).click()
    page.get_by_role("button", name="Search combined KB", exact=True).click()
    if live_smoke:
        expect(page.locator("#combined-kb .kb-output article").first).to_be_visible()
    else:
        expect(page.locator("#combined-kb .kb-output")).to_contain_text("Mapayca Markets requires CSV.")
        references = page.locator("#combined-kb .reference-list")
        expect(references).to_contain_text("API Design and Export Contracts Guide")
        expect(references).to_contain_text("Generate CSV with a standards-based library.")

    assert [payload["combined"] for payload in payloads] == [True]
    assert all("prefix" not in payload for payload in payloads)


def test_exposes_combined_mcp_config_and_three_call_pages(
    page: Page, live_server_url: str, live_smoke: bool
) -> None:
    mock_app_apis(page, live_smoke)
    page.goto(live_server_url)
    page.locator(".nav-group").filter(has_text="Combined knowledge base").get_by_role("button", name="Configuration", exact=True).click()
    expect(page.locator('#combined-kb-configuration .config-facts > .mcp-strip[data-kb="combined"] code')).to_contain_text(
        "cocoarynth-kb-all"
    )
    expect(page.locator("#combined-kb-configuration .config-facts").first).to_contain_text("MCP URL")
    expect(page.locator(".mcp-search")).to_have_count(3)
    expect(page.locator(".nav-group-combined")).to_have_css("border-top-style", "solid")


def test_inventory_error_is_visible(page: Page, live_server_url: str, live_smoke: bool) -> None:
    if live_smoke:
        pytest.skip("The intentional mocked failure is not part of live smoke testing.")
    mock_app_apis(page, live_smoke, document_error=True)
    page.goto(live_server_url)

    expect(page.locator("#toast")).to_have_text("Search inventory is unavailable.")
    expect(page.locator("#toast")).to_have_class(re.compile(r"\bshow\b"))
