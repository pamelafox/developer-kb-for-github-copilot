import asyncio
import hashlib
import os
import subprocess
from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest
import requests
from copilot import CopilotClient, ToolSet
from copilot.generated.rpc import PermissionDecisionApproveOnce, PermissionDecisionReject
from copilot.generated.session_events import (
    AssistantMessageData,
    PermissionRequest,
    PermissionRequestMcp,
    PermissionRequestRead,
    PermissionRequestWrite,
    SessionMcpServerStatusChangedData,
    SessionMcpServersLoadedData,
)
from copilot.session import PreMcpToolCallHookInput
from copilot.tools import Tool, ToolInvocation, ToolResult

from app.backend.config import load_local_environment


REPOSITORY_URL = "https://github.com/pamelafox/cocoarynth-trace.git"
PRD_FILE = "origin-passport-csv-prd.md"
DOCUMENTS_SERVER = "acceptance-cocoarynth-documents"
COMBINED_SERVER = "acceptance-cocoarynth-combined"
PART3_PROMPT = (
    "Before answering, make a new call to `cocoarynth-documents` and a new call to GitHub MCP; do not rely only "
    "on evidence from the previous answer. Can Cocoarynth support Mapayça Markets' traceability import today? "
    "Identify the blocker, check relevant issues for related open work, and cite both the pilot requirements and "
    "current implementation evidence."
)
PART3_DOCUMENT_PROMPT = (
    "Use `cocoarynth-documents` to answer: What file format does Mapayça Markets require for the Cocoarynth "
    "traceability pilot, and does its importer accept JSON? Cite the supporting document."
)
PART4_PROMPT = (
    f"Create a local Markdown file named `{PRD_FILE}` containing a product requirements document for adding CSV "
    "Origin Passport export support to Cocoarynth Trace. Before drafting, retrieve evidence from both direct GitHub "
    "MCP and `cocoarynth-combined`. Use GitHub for current code, issues, pull requests, and discussions. Use the "
    "combined knowledge base for project requirements, architecture, policy, support constraints, and company "
    "engineering standards. Address Mapayça Markets' CSV requirement and rejection of JSON, and whether CSV export "
    "must preserve the immutable Origin Passport snapshot. Distinguish required behavior, current implementation, "
    "and recommendations. Include context, goals, non-goals, user stories, API and export contract, UI and "
    "accessibility requirements, implementation considerations, acceptance criteria, testing, rollout and "
    "observability, open questions, and source links. Do not modify application code or any GitHub artifact. Do not "
    "finish until the Markdown file has been created."
)
PART4_SECTIONS = (
    "context",
    "goals",
    "non-goals",
    "user stories",
    "api",
    "accessibility",
    "implementation",
    "acceptance criteria",
    "testing",
    "rollout",
    "observability",
    "open questions",
    "source",
)


@dataclass(frozen=True)
class CopilotSmokeConfig:
    base_url: str
    search_key: str = field(repr=False)
    github_token: str = field(repr=False)


@pytest.fixture(scope="session")
def copilot_smoke_config(pytestconfig: pytest.Config) -> CopilotSmokeConfig:
    if not pytestconfig.getoption("--copilot-smoke"):
        pytest.skip("Run with --copilot-smoke to consume GitHub Copilot quota.")
    base_url = pytestconfig.getoption("--smoke-base-url")
    if not base_url:
        pytest.fail("--copilot-smoke requires --smoke-base-url for the deployed workshop portal.")
    load_local_environment()
    try:
        search_key = os.environ["AZURE_SEARCH_QUERY_KEY"]
    except KeyError:
        pytest.fail("--copilot-smoke requires AZURE_SEARCH_QUERY_KEY or a selected azd environment.")
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        try:
            github_token = subprocess.run(
                ["gh", "auth", "token"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (FileNotFoundError, subprocess.CalledProcessError):
            pytest.fail("--copilot-smoke requires GITHUB_TOKEN or an authenticated GitHub CLI.")
    assert github_token
    return CopilotSmokeConfig(base_url.rstrip("/"), search_key, github_token)


@pytest.fixture(scope="session")
def knowledge_base_urls(copilot_smoke_config: CopilotSmokeConfig) -> dict[str, str]:
    response = requests.get(f"{copilot_smoke_config.base_url}/api/knowledge-bases", timeout=30)
    response.raise_for_status()
    return {
        knowledge_base["name"]: knowledge_base["mcpUrl"]
        for knowledge_base in response.json()["knowledgeBases"]
    }


@pytest.fixture()
def cocoarynth_checkout(copilot_smoke_config: CopilotSmokeConfig) -> Generator[Path, None, None]:
    del copilot_smoke_config
    with TemporaryDirectory(prefix="cocoarynth-copilot-smoke-") as temp_directory:
        checkout = Path(temp_directory) / "cocoarynth-trace"
        subprocess.run(
            ["git", "clone", "--depth", "1", REPOSITORY_URL, str(checkout)],
            check=True,
            capture_output=True,
            text=True,
        )
        yield checkout


def _workspace_snapshot(checkout: Path) -> dict[str, str]:
    return {
        str(file.relative_to(checkout)): hashlib.sha256(file.read_bytes()).hexdigest()
        for file in checkout.rglob("*")
        if file.is_file() and ".git" not in file.relative_to(checkout).parts
    }


def _is_within(path: str, checkout: Path) -> bool:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = checkout / candidate
    return candidate.resolve().is_relative_to(checkout.resolve())


def _permission_handler(
    checkout: Path,
    knowledge_base_server: str,
    rejected_requests: list[tuple[str, str | None, str | None, str | None]],
    writable_file: str | None = None,
) -> Callable[..., Any]:
    writable_path = (checkout / writable_file).resolve() if writable_file else None

    def decide(request: PermissionRequest, invocation: dict[str, str]) -> Any:
        del invocation
        if isinstance(request, PermissionRequestMcp):
            is_allowed_knowledge_retrieval = (
                request.server_name == knowledge_base_server
                and request.tool_name
                == f"{knowledge_base_server}-knowledge_base_retrieve"
            )
            if request.read_only or is_allowed_knowledge_retrieval:
                return PermissionDecisionApproveOnce()
        if isinstance(request, PermissionRequestRead):
            resolved_path = request.resolved_path or request.path
            if _is_within(resolved_path, checkout):
                return PermissionDecisionApproveOnce()
        if isinstance(request, PermissionRequestWrite):
            resolved_path = Path(request.resolved_path or request.file_name)
            if not resolved_path.is_absolute():
                resolved_path = checkout / resolved_path
            resolved_path = resolved_path.resolve()
            if writable_path and resolved_path == writable_path:
                return PermissionDecisionApproveOnce()
        rejected_requests.append(
            (
                request.kind,
                getattr(request, "server_name", None),
                getattr(request, "tool_name", None),
                getattr(request, "url", "").partition("?")[0] or None,
            )
        )
        return PermissionDecisionReject(feedback="The acceptance test permits only scoped local reads and writes.")

    return decide


async def _run_session(
    checkout: Path,
    server_name: str,
    mcp_url: str,
    search_key: str,
    github_token: str,
    prompt: str,
    writable_file: str | None = None,
    preliminary_prompt: str | None = None,
) -> tuple[
    str,
    list[tuple[str, str]],
    list[tuple[str, str, str | None]],
    list[tuple[str, str | None, str | None, str | None]],
]:
    calls: list[tuple[str, str]] = []
    mcp_statuses: list[tuple[str, str, str | None]] = []
    rejected_requests: list[tuple[str, str | None, str | None, str | None]] = []
    output_created = asyncio.Event()

    async def write_prd(invocation: ToolInvocation) -> ToolResult:
        if writable_file is None:
            return ToolResult(
                text_result_for_llm="No output file is allowed in this session.",
                result_type="failure",
            )
        content = invocation.arguments.get("content")
        if not isinstance(content, str) or not content.strip():
            return ToolResult(
                text_result_for_llm="The PRD content must be a non-empty string.",
                result_type="failure",
            )
        (checkout / writable_file).write_text(content, encoding="utf-8")
        output_created.set()
        return ToolResult(
            text_result_for_llm=f"Created {writable_file}.",
            result_type="success",
        )

    tools = []
    if writable_file:
        tools.append(
            Tool(
                name="write_prd",
                description=f"Write the completed Markdown PRD to the only allowed output file, {writable_file}.",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "The complete grounded PRD in Markdown.",
                        }
                    },
                    "required": ["content"],
                },
                handler=write_prd,
                skip_permission=True,
                defer="never",
            )
        )

    def record_mcp_call(hook_input: PreMcpToolCallHookInput, context: dict[str, str]) -> None:
        del context
        calls.append((hook_input["serverName"], hook_input["toolName"]))

    def record_event(event: Any) -> None:
        if isinstance(event.data, SessionMcpServersLoadedData):
            mcp_statuses.extend(
                (server.name, str(server.status), None) for server in event.data.servers
            )
        elif isinstance(event.data, SessionMcpServerStatusChangedData):
            mcp_statuses.append(
                (event.data.server_name, str(event.data.status), event.data.error)
            )

    client = CopilotClient(
        working_directory=str(checkout),
        base_directory=str(checkout.parent / "copilot-home"),
        github_token=github_token,
        use_logged_in_user=False,
        mode="empty",
    )
    await client.start()
    try:
        async with await client.create_session(
            working_directory=str(checkout),
            on_permission_request=_permission_handler(
                checkout, server_name, rejected_requests, writable_file
            ),
            on_event=record_event,
            hooks={"on_pre_mcp_tool_call": record_mcp_call},
            tools=tools,
            mcp_servers={
                server_name: {
                    "type": "http",
                    "url": mcp_url,
                    "headers": {"api-key": search_key},
                    "tools": ["knowledge_base_retrieve"],
                }
            },
            github_mcp_tool_config={
                "enable_all_tools": False,
                "additional_toolsets": ["repos", "issues", "pull_requests", "discussions"],
            },
            tool_search={"enabled": False},
            available_tools=(
                ToolSet().add_builtin("read_file").add_mcp("*").add_custom("write_prd")
                if writable_file
                else ToolSet().add_builtin("read_file").add_mcp("*")
            ),
            enable_config_discovery=True,
            skip_custom_instructions=False,
            enable_host_git_operations=False,
            system_message={
                "mode": "append",
                "content": (
                    "This is an acceptance test in a disposable clone. Use only read-only GitHub and MCP calls. "
                    "Never run shell commands or write to GitHub. Do not modify local files unless the user names "
                    f"the exact allowed output file ({writable_file or 'none'}). You must retrieve evidence from "
                    f"the `{server_name}` MCP server and direct GitHub MCP before completing the task. "
                    + ("Use the `write_prd` tool once to create the completed file." if writable_file else "")
                ),
            },
        ) as session:
            if preliminary_prompt:
                preliminary_response = await session.send_and_wait(
                    preliminary_prompt.replace("`cocoarynth-documents`", f"`{server_name}`"),
                    timeout=300,
                )
                if preliminary_response is None:
                    raise AssertionError("Copilot returned no response to the preliminary workshop prompt.")
            resolved_prompt = prompt.replace(
                "`cocoarynth-documents`", f"`{server_name}`"
            ).replace("`cocoarynth-combined`", f"`{server_name}`")
            if writable_file:
                await session.send(resolved_prompt)
                await asyncio.wait_for(output_created.wait(), timeout=300)
                return "", calls, mcp_statuses, rejected_requests
            response = await session.send_and_wait(
                resolved_prompt,
                timeout=300,
            )
            if response is None or not isinstance(response.data, AssistantMessageData):
                raise AssertionError("Copilot returned no final assistant message.")
            return response.data.content, calls, mcp_statuses, rejected_requests
    finally:
        await client.stop()


def _assert_servers_called(
    calls: list[tuple[str, str]],
    knowledge_base_server: str,
    mcp_statuses: list[tuple[str, str, str | None]],
) -> None:
    servers = {server.lower() for server, _ in calls}
    assert knowledge_base_server.lower() in servers, (calls, mcp_statuses)
    assert any("github" in server for server in servers), calls


def test_part3_copilot_coordinates_documents_and_github(
    copilot_smoke_config: CopilotSmokeConfig,
    knowledge_base_urls: dict[str, str],
    cocoarynth_checkout: Path,
) -> None:
    before = _workspace_snapshot(cocoarynth_checkout)
    answer, calls, mcp_statuses, _ = asyncio.run(
        _run_session(
            cocoarynth_checkout,
            DOCUMENTS_SERVER,
            knowledge_base_urls["cocoarynth-kb-docs"],
            copilot_smoke_config.search_key,
            copilot_smoke_config.github_token,
            PART3_PROMPT,
            preliminary_prompt=PART3_DOCUMENT_PROMPT,
        )
    )

    _assert_servers_called(calls, DOCUMENTS_SERVER, mcp_statuses)
    normalized = answer.lower()
    assert "csv" in normalized and "json" in normalized
    assert any(term in normalized for term in ("reject", "does not accept", "not accept"))
    assert any(term in normalized for term in ("issue", "open work", "open"))
    assert _workspace_snapshot(cocoarynth_checkout) == before


def test_part4_copilot_creates_grounded_prd_only(
    copilot_smoke_config: CopilotSmokeConfig,
    knowledge_base_urls: dict[str, str],
    cocoarynth_checkout: Path,
) -> None:
    before = _workspace_snapshot(cocoarynth_checkout)
    _, calls, mcp_statuses, _ = asyncio.run(
        _run_session(
            cocoarynth_checkout,
            COMBINED_SERVER,
            knowledge_base_urls["cocoarynth-kb-all"],
            copilot_smoke_config.search_key,
            copilot_smoke_config.github_token,
            PART4_PROMPT,
            writable_file=PRD_FILE,
        )
    )

    _assert_servers_called(calls, COMBINED_SERVER, mcp_statuses)
    after = _workspace_snapshot(cocoarynth_checkout)
    assert set(after) - set(before) == {PRD_FILE}
    assert {name: digest for name, digest in after.items() if name != PRD_FILE} == before

    prd = (cocoarynth_checkout / PRD_FILE).read_text().lower()
    for section in PART4_SECTIONS:
        assert section in prd
    for requirement in ("utf-8", "text/csv", "immutable", "mapay", "csv", "json"):
        assert requirement in prd
    assert any(term in prd for term in ("confidential", "personal", "unapproved"))
    assert "bulk export" in prd
    assert "http" in prd