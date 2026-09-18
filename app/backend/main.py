from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from azure.core.exceptions import AzureError
from azure.identity import AzureDeveloperCliCredential, ManagedIdentityCredential
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import Settings, is_running_in_production
from .foundry_iq import ENGINEERING_PRACTICE_CONTAINER, FoundryIqService
from .mcp_client import McpRetrievalError, retrieve_over_mcp
from .naming import SharedResources, shared_resources


STATIC_DIR = Path(__file__).parent / "static"
SHARED_RESOURCES = shared_resources()


class RetrievalRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    combined: bool = False


class McpRetrievalRequest(BaseModel):
    question: str = Field(min_length=3, max_length=400)
    target: str = Field(pattern="^(documents|engineering-practices|combined)$")


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.from_environment()
    credential = (
        ManagedIdentityCredential(client_id=settings.managed_identity_client_id)
        if is_running_in_production()
        else AzureDeveloperCliCredential()
    )
    app.state.settings = settings
    app.state.credential = credential
    app.state.service = FoundryIqService(settings, credential)
    yield
    app.state.service.index_client.close()
    app.state.service.blob_service.close()
    credential.close()


app = FastAPI(title="Foundry IQ workshop", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.exception_handler(AzureError)
async def azure_service_error(_: Request, error: AzureError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "Azure Search is unavailable. Verify AZURE_SEARCH_ENDPOINT, authenticate with azd, "
                "and confirm the shared corpus has been provisioned."
            )
        },
    )


@app.exception_handler(McpRetrievalError)
async def mcp_service_error(_: Request, error: McpRetrievalError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "The MCP retrieval endpoint is unavailable. Confirm that the selected knowledge base "
                "has been provisioned and that the application identity can query Azure AI Search."
            )
        },
    )


@app.get("/", include_in_schema=False)
@app.get("/project-requirements", include_in_schema=False)
@app.get("/project-requirements/chunks", include_in_schema=False)
@app.get("/project-requirements/search", include_in_schema=False)
@app.get("/project-requirements/mcp", include_in_schema=False)
@app.get("/engineering-practices", include_in_schema=False)
@app.get("/engineering-practices/chunks", include_in_schema=False)
@app.get("/engineering-practices/search", include_in_schema=False)
@app.get("/engineering-practices/mcp", include_in_schema=False)
@app.get("/combined/configuration", include_in_schema=False)
@app.get("/combined/query", include_in_schema=False)
@app.get("/combined/mcp", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/documents")
async def document_overview(request: Request) -> dict[str, Any]:
    return await run_in_threadpool(request.app.state.service.list_documents)


@app.get("/api/documents/content/{blob_name:path}")
async def document_content(blob_name: str, request: Request) -> Response:
    if not blob_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=404, detail="Document not found.")
    content, _ = await run_in_threadpool(
        request.app.state.service.download_document, blob_name
    )
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{Path(blob_name).name}"'},
    )


@app.get("/api/documents/chunks")
async def chunks(request: Request, document: str, limit: int = 100) -> dict[str, Any]:
    return await run_in_threadpool(
        request.app.state.service.list_chunks,
        SHARED_RESOURCES,
        document,
        min(limit, 500),
    )


@app.post("/api/documents/search")
async def search_documents(payload: SearchRequest, request: Request) -> dict[str, Any]:
    return await run_in_threadpool(
        request.app.state.service.search_documents,
        SHARED_RESOURCES,
        payload.query,
        payload.limit,
    )


@app.get("/api/engineering-practices")
async def engineering_practice_overview(request: Request) -> dict[str, Any]:
    return await run_in_threadpool(
        request.app.state.service.list_documents,
        ENGINEERING_PRACTICE_CONTAINER,
        "/api/engineering-practices/content",
    )


@app.get("/api/engineering-practices/content/{blob_name:path}")
async def engineering_practice_content(blob_name: str, request: Request) -> Response:
    if not blob_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=404, detail="Document not found.")
    content, _ = await run_in_threadpool(
        request.app.state.service.download_document,
        blob_name,
        ENGINEERING_PRACTICE_CONTAINER,
    )
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{Path(blob_name).name}"'},
    )


@app.get("/api/engineering-practices/chunks")
async def engineering_practice_chunks(request: Request, document: str, limit: int = 100) -> dict[str, Any]:
    return await run_in_threadpool(
        request.app.state.service.list_chunks,
        SHARED_RESOURCES,
        document,
        min(limit, 500),
        SHARED_RESOURCES.engineering_practice_index,
    )


@app.post("/api/engineering-practices/search")
async def search_engineering_practices(payload: SearchRequest, request: Request) -> dict[str, Any]:
    return await run_in_threadpool(
        request.app.state.service.search_documents,
        SHARED_RESOURCES,
        payload.query,
        payload.limit,
        SHARED_RESOURCES.engineering_practice_index,
    )


@app.get("/api/knowledge-bases")
async def knowledge_bases(request: Request, response: Response) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    return await run_in_threadpool(
        request.app.state.service.get_knowledge_base_configuration,
        SHARED_RESOURCES,
    )


@app.post("/api/retrieve")
async def retrieve(payload: RetrievalRequest, request: Request) -> dict[str, Any]:
    return await run_in_threadpool(
        request.app.state.service.retrieve,
        SHARED_RESOURCES,
        payload.question,
        payload.combined,
    )


@app.post("/api/mcp/retrieve")
async def mcp_retrieve(payload: McpRetrievalRequest, request: Request) -> dict[str, Any]:
    knowledge_base_names = {
        "documents": SHARED_RESOURCES.document_knowledge_base,
        "engineering-practices": SHARED_RESOURCES.engineering_practice_knowledge_base,
        "combined": SHARED_RESOURCES.combined_knowledge_base,
    }
    knowledge_base_name = knowledge_base_names[payload.target]
    server_url = (
        f"{request.app.state.settings.search_endpoint}/knowledgebases/{knowledge_base_name}/mcp"
        "?api-version=2026-08-01-preview"
    )
    return await retrieve_over_mcp(
        server_url,
        request.app.state.credential,
        payload.question,
    )
