from collections.abc import Callable, Generator

import pytest
import requests
from azure.identity import AzureDeveloperCliCredential, get_bearer_token_provider
from openai import OpenAI
from playwright.sync_api import Page, expect

from app.backend.config import Settings


expect.set_options(timeout=180_000)

PART3_QUESTION = "What must change in the Origin Passport export for the Mapayça Markets pilot?"
PART4_QUESTION = (
    "What product requirements and company engineering standards should guide CSV Origin Passport support? "
    "Cite evidence from both corpora."
)
AZURE_OPENAI_SCOPE = "https://cognitiveservices.azure.com/.default"
Judge = Callable[[str, str, str, str], str]


@pytest.fixture(scope="session")
def live_portal_url(pytestconfig: pytest.Config) -> str:
    base_url = pytestconfig.getoption("--smoke-base-url")
    if not base_url:
        pytest.skip("Run with --smoke-base-url pointing to the deployed workshop portal.")
    url = f"{base_url.rstrip('/')}/"
    response = requests.get(f"{url}health", timeout=30)
    response.raise_for_status()
    return url


@pytest.fixture(scope="session")
def azure_openai_judge() -> Generator[Judge, None, None]:
    settings = Settings.from_environment()
    credential = AzureDeveloperCliCredential()
    client = OpenAI(
        base_url=f"{settings.openai_endpoint}/openai/v1/",
        api_key=get_bearer_token_provider(credential, AZURE_OPENAI_SCOPE),
    )

    def judge(question: str, answer: str, references: str, rubric: str) -> str:
        response = client.responses.create(
            model=settings.chat_deployment,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You judge an extractive retrieval system acceptance test. The system returns evidence, "
                        "not a synthesized answer. Evaluate whether the supplied evidence and references are "
                        "relevant and sufficient to answer the question. Do not fail because the evidence is not "
                        "rewritten as a direct prose answer. Start with PASS or FAIL, then give one concise reason."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Question:\n{question}\n\nRubric:\n{rubric}\n\n"
                        f"Retrieved evidence:\n{answer}\n\nDisplayed references:\n{references}"
                    ),
                },
            ],
            max_output_tokens=300,
            timeout=180,
        )
        output_text = response.output_text.strip()
        if not output_text:
            raise AssertionError(f"Azure OpenAI judge returned no text: {response.model_dump_json()}")
        return output_text

    yield judge
    client.close()
    credential.close()


def test_part3_live_workflow(page: Page, live_portal_url: str, azure_openai_judge: Judge) -> None:
    page.goto(live_portal_url)
    corpus = page.locator(".nav-group").filter(has_text="Corpus 1: Project requirements")

    corpus.get_by_role("button", name="Browse documents", exact=True).click()
    expect(page.locator("#document-list")).to_contain_text(
        "mapayca-markets-traceability-pilot-requirements.pdf"
    )

    corpus.get_by_role("button", name="View document chunks", exact=True).click()
    page.locator("#document-select").select_option(
        label="mapayca-markets-traceability-pilot-requirements.pdf"
    )
    expect(page.locator("#chunk-list article").first).to_be_visible()
    expect(page.locator("#chunk-list")).to_contain_text("page_number_from")

    corpus.get_by_role("button", name="Search the index", exact=True).click()
    for query in ("CSV export requirements", "information excluded from wholesale exports"):
        page.locator("#search-query").fill(query)
        page.locator("#search-form").get_by_role("button", name="Search").click()
        expect(page.locator("#search-summary")).to_contain_text("cocoarynth-documents-index")
        expect(page.locator("#search-results article").first).to_be_visible()

    corpus.get_by_role("button", name="Call over MCP", exact=True).click()
    mcp_panel = page.locator("#documents-mcp")
    expect(mcp_panel.locator(".mcp-strip code")).to_contain_text("cocoarynth-kb-docs")
    mcp_panel.locator("textarea").fill(PART3_QUESTION)
    mcp_panel.get_by_role("button", name="Call over MCP").click()

    output = mcp_panel.locator(".mcp-output")
    expect(output.locator(".mcp-content-block").first).to_be_visible()
    expect(output).to_contain_text("MCP content")

    verdict = azure_openai_judge(
        PART3_QUESTION,
        output.inner_text(),
        output.inner_text(),
        (
            "PASS only if the retrieved evidence contains concrete Origin Passport export changes for the Mapayça "
            "Markets pilot, is grounded in the project requirements, and displays at least one relevant citation."
        ),
    )
    assert verdict.upper().startswith("PASS"), verdict


def test_part4_live_workflow(page: Page, live_portal_url: str, azure_openai_judge: Judge) -> None:
    page.goto(live_portal_url)
    combined = page.locator(".nav-group").filter(has_text="Combined knowledge base")
    combined.get_by_role("button", name="Configuration", exact=True).click()

    configuration = page.locator("#combined-kb-configuration")
    expect(configuration).to_contain_text("cocoarynth-kb-all")
    for source_name, index_name in (
        ("cocoarynth-documents-source", "cocoarynth-documents-index"),
        ("cocoarynth-engineering-practices-source", "cocoarynth-engineering-practices-index"),
    ):
        source = configuration.locator(".source-row").filter(has_text=source_name)
        expect(source.locator(".source-facts")).to_contain_text("KindsearchIndex")
        expect(source.locator(".source-facts")).to_contain_text(index_name)

    combined.get_by_role("button", name="Query knowledge base", exact=True).click()
    page.locator("#combined-kb textarea").fill(PART4_QUESTION)
    page.locator("#combined-kb").get_by_role("button", name="Search combined KB").click()

    output = page.locator("#combined-kb .kb-output")
    references = page.locator("#combined-kb .reference-list")
    activity = page.locator("#combined-kb .activity-table")
    expect(output.locator("article").first).to_be_visible()
    expect(references.locator("article").first).to_be_visible()
    expect(activity).to_contain_text("Index search")

    verdict = azure_openai_judge(
        PART4_QUESTION,
        output.inner_text(),
        references.inner_text(),
        (
            "PASS only if the retrieved evidence includes both product requirements and engineering standards "
            "relevant to CSV Origin Passport support, and the displayed references include evidence from both "
            "project requirements and engineering practices."
        ),
    )
    assert verdict.upper().startswith("PASS"), verdict