import hashlib
import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

from azure.core.exceptions import HttpResponseError, ResourceNotFoundError
from azure.core.rest import HttpRequest
from azure.identity import AzureDeveloperCliCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import SearchIndex
from azure.storage.blob import BlobServiceClient, ContainerClient

from app.backend.config import Settings
from app.backend.foundry_iq import FoundryIqService
from app.backend.naming import shared_resources


CORPUS_DIR = Path(__file__).parents[1] / "documents"
SHARED_RESOURCES = shared_resources()
SEARCH_API_VERSION = "2026-05-01-preview"
CORPUS_CONTAINER = "knowledge"
EXTRACTED_IMAGES_CONTAINER = "extracted-images"
SEMANTIC_CONFIGURATION = "semantic-configuration"
VECTOR_PROFILE = "vector-search-profile"
EMBEDDING_DIMENSIONS = 3072
INDEXER_POLL_SECONDS = 10
INDEXER_TIMEOUT = timedelta(minutes=30)


def build_index(settings: Settings) -> SearchIndex:
    return SearchIndex(
        {
            "name": SHARED_RESOURCES.generated_index,
            "fields": [
                {
                    "name": "chunk_id",
                    "type": "Edm.String",
                    "key": True,
                    "searchable": True,
                    "retrievable": True,
                    "stored": True,
                    "sortable": True,
                    "analyzer": "keyword",
                },
                {
                    "name": "parent_id",
                    "type": "Edm.String",
                    "filterable": True,
                    "retrievable": True,
                    "stored": True,
                },
                {
                    "name": "title",
                    "type": "Edm.String",
                    "searchable": True,
                    "retrievable": True,
                    "stored": True,
                },
                {
                    "name": "blob_path",
                    "type": "Edm.String",
                    "filterable": True,
                    "retrievable": True,
                    "stored": True,
                },
                {
                    "name": "chunk",
                    "type": "Edm.String",
                    "searchable": True,
                    "retrievable": True,
                    "stored": True,
                },
                {
                    "name": "page_number_from",
                    "type": "Edm.Int32",
                    "filterable": True,
                    "retrievable": True,
                    "stored": True,
                    "sortable": True,
                },
                {
                    "name": "page_number_to",
                    "type": "Edm.Int32",
                    "filterable": True,
                    "retrievable": True,
                    "stored": True,
                    "sortable": True,
                },
                {
                    "name": "image_path",
                    "type": "Edm.String",
                    "retrievable": True,
                    "stored": True,
                },
                {
                    "name": "text_vector",
                    "type": "Collection(Edm.Single)",
                    "searchable": True,
                    "retrievable": False,
                    "stored": False,
                    "dimensions": EMBEDDING_DIMENSIONS,
                    "vectorSearchProfile": VECTOR_PROFILE,
                },
            ],
            "semantic": {
                "defaultConfiguration": SEMANTIC_CONFIGURATION,
                "configurations": [
                    {
                        "name": SEMANTIC_CONFIGURATION,
                        "prioritizedFields": {
                            "titleField": {"fieldName": "title"},
                            "prioritizedContentFields": [{"fieldName": "chunk"}],
                        },
                    }
                ],
            },
            "vectorSearch": {
                "profiles": [
                    {
                        "name": VECTOR_PROFILE,
                        "algorithm": "vector-search-algorithm",
                        "vectorizer": "azure-openai-vectorizer",
                    }
                ],
                "algorithms": [
                    {
                        "name": "vector-search-algorithm",
                        "kind": "hnsw",
                        "hnswParameters": {"metric": "cosine"},
                    }
                ],
                "vectorizers": [
                    {
                        "name": "azure-openai-vectorizer",
                        "kind": "azureOpenAI",
                        "azureOpenAIParameters": {
                            "resourceUri": settings.openai_endpoint,
                            "deploymentId": settings.embedding_deployment,
                            "modelName": settings.embedding_model,
                        },
                    }
                ],
            },
        }
    )


def build_indexer_payloads(
    settings: Settings,
    storage_resource_id: str,
    foundry_endpoint: str,
) -> dict[str, tuple[str, dict[str, Any]]]:
    index_name = SHARED_RESOURCES.generated_index
    data_source_name = f"{index_name}-blob-source"
    skillset_name = f"{index_name}-content-understanding"
    indexer_name = f"{index_name}-blob-indexer"
    data_source = {
        "name": data_source_name,
        "type": "azureblob",
        "credentials": {"connectionString": f"ResourceId={storage_resource_id};"},
        "container": {"name": CORPUS_CONTAINER},
    }
    skillset = {
        "name": skillset_name,
        "description": "Semantic PDF chunking, image extraction, and vectorization.",
        "skills": [
            {
                "@odata.type": "#Microsoft.Skills.Util.ContentUnderstandingSkill",
                "name": "content-understanding",
                "context": "/document",
                "modelName": settings.content_understanding_model,
                "modelDeployment": settings.content_understanding_deployment,
                "chunkingProperties": {
                    "method": "semantic",
                    "unit": "tokens",
                    "maximumLength": 700,
                },
                "extractionOptions": ["images", "locationMetadata"],
                "inputs": [{"name": "file_data", "source": "/document/file_data"}],
                "outputs": [
                    {"name": "text_sections", "targetName": "text_sections"},
                    {"name": "normalized_images", "targetName": "normalized_images"},
                ],
            },
            {
                "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
                "name": "azure-openai-embedding",
                "context": "/document/text_sections/*",
                "resourceUri": settings.openai_endpoint,
                "deploymentId": settings.embedding_deployment,
                "modelName": settings.embedding_model,
                "dimensions": EMBEDDING_DIMENSIONS,
                "inputs": [{"name": "text", "source": "/document/text_sections/*/content"}],
                "outputs": [{"name": "embedding", "targetName": "text_vector"}],
            },
        ],
        "cognitiveServices": {
            "@odata.type": "#Microsoft.Azure.Search.AIServicesByIdentity",
            "subdomainUrl": foundry_endpoint,
            "identity": None,
        },
        "knowledgeStore": {
            "storageConnectionString": f"ResourceId={storage_resource_id}/;",
            "projections": [
                {
                    "tables": [],
                    "objects": [],
                    "files": [
                        {
                            "storageContainer": EXTRACTED_IMAGES_CONTAINER,
                            "source": "/document/normalized_images/*",
                        }
                    ],
                }
            ],
        },
        "indexProjections": {
            "selectors": [
                {
                    "targetIndexName": index_name,
                    "parentKeyFieldName": "parent_id",
                    "sourceContext": "/document/text_sections/*",
                    "mappings": [
                        {"name": "chunk", "source": "/document/text_sections/*/content"},
                        {"name": "text_vector", "source": "/document/text_sections/*/text_vector"},
                        {
                            "name": "page_number_from",
                            "source": "/document/text_sections/*/locationMetadata/pageNumberFrom",
                        },
                        {
                            "name": "page_number_to",
                            "source": "/document/text_sections/*/locationMetadata/pageNumberTo",
                        },
                        {"name": "image_path", "source": "/document/text_sections/*/imagePath"},
                        {"name": "title", "source": "/document/metadata_storage_name"},
                        {"name": "blob_path", "source": "/document/metadata_storage_path"},
                    ],
                }
            ],
            "parameters": {"projectionMode": "skipIndexingParentDocuments"},
        },
    }
    indexer = {
        "name": indexer_name,
        "dataSourceName": data_source_name,
        "targetIndexName": index_name,
        "skillsetName": skillset_name,
        "parameters": {
            "batchSize": 1,
            "configuration": {
                "dataToExtract": "contentAndMetadata",
                "parsingMode": "default",
                "allowSkillsetToReadFileData": True,
                "indexedFileNameExtensions": ".pdf",
            },
        },
        "fieldMappings": [],
        "outputFieldMappings": [],
    }
    return {
        "datasources": (data_source_name, data_source),
        "skillsets": (skillset_name, skillset),
        "indexers": (indexer_name, indexer),
    }


def sync_blob_corpus(container: ContainerClient, corpus_dir: Path) -> dict[str, list[str]]:
    pdfs = {pdf.name: pdf for pdf in sorted(corpus_dir.glob("*.pdf"))}
    if not pdfs:
        raise RuntimeError(f"No PDFs found in {corpus_dir}.")

    existing = {blob.name: blob for blob in container.list_blobs(include=["metadata"])}
    deleted = sorted(set(existing) - set(pdfs))
    for name in deleted:
        container.delete_blob(name)

    uploaded: list[str] = []
    skipped: list[str] = []
    for name, pdf_path in pdfs.items():
        content = pdf_path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if name in existing and (existing[name].metadata or {}).get("sha256") == digest:
            skipped.append(name)
            continue
        container.upload_blob(name=name, data=content, overwrite=True, metadata={"sha256": digest})
        uploaded.append(name)
    return {"uploaded": uploaded, "skipped": skipped, "deleted": deleted}


def clear_index_documents(service: FoundryIqService) -> int:
    client = SearchClient(
        service.settings.search_endpoint,
        SHARED_RESOURCES.generated_index,
        service.credential,
    )
    try:
        try:
            documents = [
                {"chunk_id": result["chunk_id"]}
                for result in client.search("*", select=["chunk_id"], top=1000)
            ]
        except ResourceNotFoundError:
            return 0
        for offset in range(0, len(documents), 1000):
            client.delete_documents(documents=documents[offset : offset + 1000])
        return len(documents)
    finally:
        client.close()


def put_preview_resource(
    client: SearchIndexerClient,
    endpoint: str,
    collection: str,
    name: str,
    payload: dict[str, Any],
) -> None:
    url = f"{endpoint.rstrip('/')}/{collection}/{quote(name, safe='')}?api-version={SEARCH_API_VERSION}"
    response = client.send_request(
        HttpRequest("PUT", url, headers={"Content-Type": "application/json"}, json=payload)
    )
    response.raise_for_status()


def wait_for_indexer(client: SearchIndexerClient, indexer_name: str, started_after: datetime) -> int:
    deadline = datetime.now(UTC) + INDEXER_TIMEOUT
    while datetime.now(UTC) < deadline:
        result = client.get_indexer_status(indexer_name).last_result
        if result is None or result.start_time is None or result.start_time < started_after:
            time.sleep(INDEXER_POLL_SECONDS)
            continue
        status = getattr(result.status, "value", result.status)
        if status == "success":
            if result.failed_item_count:
                raise RuntimeError(f"Indexer completed with {result.failed_item_count} failed items.")
            return result.item_count
        if status not in {"inProgress", "reset"}:
            raise RuntimeError(f"Indexer ended with status '{status}': {result.error_message}")
        time.sleep(INDEXER_POLL_SECONDS)
    raise TimeoutError(f"Indexer '{indexer_name}' did not finish within {INDEXER_TIMEOUT}.")


def ingest_corpus(
    service: FoundryIqService,
    container: ContainerClient,
    storage_resource_id: str,
    foundry_endpoint: str,
    corpus_dir: Path = CORPUS_DIR,
) -> dict[str, Any]:
    files = sync_blob_corpus(container, corpus_dir)
    service.index_client.create_or_update_index(build_index(service.settings))
    removed_chunks = clear_index_documents(service)
    service.create_document_workspace(SHARED_RESOURCES)

    pipeline = build_indexer_payloads(service.settings, storage_resource_id, foundry_endpoint)
    indexer_client = SearchIndexerClient(service.settings.search_endpoint, service.credential)
    try:
        for collection, (name, payload) in pipeline.items():
            put_preview_resource(indexer_client, service.settings.search_endpoint, collection, name, payload)
        indexer_name = pipeline["indexers"][0]
        indexer_client.reset_indexer(indexer_name)
        started_after = datetime.now(UTC) - timedelta(seconds=5)
        indexer_client.run_indexer(indexer_name)
        indexed_items = wait_for_indexer(indexer_client, indexer_name, started_after)
    finally:
        indexer_client.close()
    service.create_shared_combined_workspace(SHARED_RESOURCES)
    return {**files, "removedChunks": removed_chunks, "indexedItems": indexed_items}


def ingest_with_retry(operation: Any, attempts: int = 12, delay_seconds: int = 10) -> dict[str, Any]:
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except HttpResponseError as error:
            if error.status_code != 403 or attempt == attempts:
                raise
            print(f"Azure RBAC is still propagating; retrying in {delay_seconds} seconds ({attempt}/{attempts}).")
            time.sleep(delay_seconds)
    raise RuntimeError("Ingestion retry loop completed unexpectedly.")


def main() -> None:
    settings = Settings(
        search_endpoint=os.environ["AZURE_SEARCH_ENDPOINT"].rstrip("/"),
        openai_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/"),
        embedding_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"),
        embedding_model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
        chat_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-5.4-mini"),
        chat_model=os.getenv("AZURE_OPENAI_CHAT_MODEL", "gpt-5.4-mini"),
        search_query_key="",
        github_pat=os.environ["GITHUB_LAB_PAT"],
        github_mcp_url=os.getenv("GITHUB_MCP_URL", "https://api.githubcopilot.com/mcp/readonly"),
        github_mcp_tools=tuple(
            tool.strip()
            for tool in os.getenv(
                "GITHUB_MCP_TOOLS",
                "search_code,search_issues,get_file_contents,issue_read,pull_request_read",
            ).split(",")
            if tool.strip()
        ),
        managed_identity_client_id=None,
    )
    credential = AzureDeveloperCliCredential()
    service = FoundryIqService(settings, credential)
    blob_service = BlobServiceClient(
        account_url=f"https://{os.environ['AZURE_STORAGE_ACCOUNT_NAME']}.blob.core.windows.net",
        credential=credential,
    )
    container = blob_service.get_container_client(CORPUS_CONTAINER)
    try:
        result = ingest_with_retry(
            lambda: ingest_corpus(
                service,
                container,
                os.environ["AZURE_STORAGE_ACCOUNT_ID"],
                os.environ["AZURE_AI_FOUNDRY_ENDPOINT"].rstrip("/"),
            )
        )
        print(
            f"Shared corpus ready: {len(result['uploaded'])} uploaded, "
            f"{len(result['skipped'])} unchanged, {result['indexedItems']} documents processed."
        )
    finally:
        blob_service.close()
        service.index_client.close()
        credential.close()


if __name__ == "__main__":
    main()