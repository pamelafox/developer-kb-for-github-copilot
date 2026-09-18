import hashlib
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote

from azure.core.exceptions import HttpResponseError, ResourceExistsError, ResourceNotFoundError
from azure.core.rest import HttpRequest
from azure.identity import AzureDeveloperCliCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import SearchIndex
from azure.storage.blob import BlobServiceClient, ContainerClient

from app.backend.config import Settings
from app.backend.foundry_iq import FoundryIqService
from app.backend.naming import shared_resources


DOCUMENT_CORPUS_DIR = Path(__file__).parents[1] / "documents"
ENGINEERING_PRACTICE_CORPUS_DIR = DOCUMENT_CORPUS_DIR / "engineering-practices"
SHARED_RESOURCES = shared_resources()
SEARCH_API_VERSION = "2026-05-01-preview"
SEMANTIC_CONFIGURATION = "semantic-configuration"
VECTOR_PROFILE = "vector-search-profile"
EMBEDDING_DIMENSIONS = 3072
INDEXER_POLL_SECONDS = 10
INDEXER_TIMEOUT = timedelta(minutes=30)


@dataclass(frozen=True)
class CorpusSpec:
    key: str
    directory: Path
    index_name: str
    container_name: str
    extracted_images_container_name: str
    description: str


DOCUMENT_CORPUS = CorpusSpec(
    key="documents",
    directory=DOCUMENT_CORPUS_DIR,
    index_name=SHARED_RESOURCES.document_index,
    container_name="knowledge",
    extracted_images_container_name="extracted-images",
    description="Project requirements, architecture decisions, policies, and support documents.",
)
ENGINEERING_PRACTICE_CORPUS = CorpusSpec(
    key="engineeringPractices",
    directory=ENGINEERING_PRACTICE_CORPUS_DIR,
    index_name=SHARED_RESOURCES.engineering_practice_index,
    container_name="engineering-practices",
    extracted_images_container_name="engineering-practice-images",
    description="Cocoarynth engineering, API, frontend, accessibility, and engineering culture guidance.",
)
CORPORA = (DOCUMENT_CORPUS, ENGINEERING_PRACTICE_CORPUS)


def build_index(settings: Settings, index_name: str = DOCUMENT_CORPUS.index_name) -> SearchIndex:
    return SearchIndex(
        {
            "name": index_name,
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
    corpus: CorpusSpec = DOCUMENT_CORPUS,
) -> dict[str, tuple[str, dict[str, Any]]]:
    index_name = corpus.index_name
    data_source_name = f"{index_name}-blob-source"
    skillset_name = f"{index_name}-content-understanding"
    indexer_name = f"{index_name}-blob-indexer"
    data_source = {
        "name": data_source_name,
        "type": "azureblob",
        "credentials": {"connectionString": f"ResourceId={storage_resource_id};"},
        "container": {"name": corpus.container_name},
    }
    skillset = {
        "name": skillset_name,
        "description": f"Semantic PDF chunking, image extraction, and vectorization. {corpus.description}",
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
                            "storageContainer": corpus.extracted_images_container_name,
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


def clear_index_documents(
    service: FoundryIqService,
    index_name: str = DOCUMENT_CORPUS.index_name,
) -> int:
    client = SearchClient(
        service.settings.search_endpoint,
        index_name,
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


def wait_for_indexer(
    client: SearchIndexerClient,
    indexer_name: str,
    started_after: datetime | None = None,
) -> int:
    deadline = datetime.now(UTC) + INDEXER_TIMEOUT
    while datetime.now(UTC) < deadline:
        result = client.get_indexer_status(indexer_name).last_result
        if (
            result is None
            or result.start_time is None
            or (started_after is not None and result.start_time < started_after)
        ):
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


def run_indexer_and_wait(client: SearchIndexerClient, indexer_name: str) -> int:
    client.reset_indexer(indexer_name)
    started_after = datetime.now(UTC) - timedelta(seconds=5)
    try:
        client.run_indexer(indexer_name)
    except ResourceExistsError:
        print(f"Indexer '{indexer_name}' is already running; waiting before starting a fresh run.")
        wait_for_indexer(client, indexer_name)
        client.reset_indexer(indexer_name)
        started_after = datetime.now(UTC) - timedelta(seconds=5)
        client.run_indexer(indexer_name)
    return wait_for_indexer(client, indexer_name, started_after)


def ingest_corpus(
    service: FoundryIqService,
    container: ContainerClient,
    storage_resource_id: str,
    foundry_endpoint: str,
    corpus: CorpusSpec = DOCUMENT_CORPUS,
) -> dict[str, Any]:
    files = sync_blob_corpus(container, corpus.directory)
    service.index_client.create_or_update_index(build_index(service.settings, corpus.index_name))
    removed_chunks = clear_index_documents(service, corpus.index_name)

    pipeline = build_indexer_payloads(service.settings, storage_resource_id, foundry_endpoint, corpus)
    indexer_client = SearchIndexerClient(service.settings.search_endpoint, service.credential)
    try:
        for collection, (name, payload) in pipeline.items():
            put_preview_resource(indexer_client, service.settings.search_endpoint, collection, name, payload)
        indexer_name = pipeline["indexers"][0]
        indexed_items = run_indexer_and_wait(indexer_client, indexer_name)
    finally:
        indexer_client.close()
    return {**files, "removedChunks": removed_chunks, "indexedItems": indexed_items}


def ingest_corpora(
    service: FoundryIqService,
    blob_service: BlobServiceClient,
    storage_resource_id: str,
    foundry_endpoint: str,
) -> dict[str, dict[str, Any]]:
    results = {
        corpus.key: ingest_corpus(
            service,
            blob_service.get_container_client(corpus.container_name),
            storage_resource_id,
            foundry_endpoint,
            corpus,
        )
        for corpus in CORPORA
    }
    service.create_document_workspace(SHARED_RESOURCES)
    service.create_shared_combined_workspace(SHARED_RESOURCES)
    return results


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
        managed_identity_client_id=None,
    )
    credential = AzureDeveloperCliCredential()
    service = FoundryIqService(settings, credential)
    blob_service = BlobServiceClient(
        account_url=f"https://{os.environ['AZURE_STORAGE_ACCOUNT_NAME']}.blob.core.windows.net",
        credential=credential,
    )
    try:
        result = ingest_with_retry(
            lambda: ingest_corpora(
                service,
                blob_service,
                os.environ["AZURE_STORAGE_ACCOUNT_ID"],
                os.environ["AZURE_AI_FOUNDRY_ENDPOINT"].rstrip("/"),
            )
        )
        for corpus in CORPORA:
            corpus_result = result[corpus.key]
            print(
                f"{corpus.key}: {len(corpus_result['uploaded'])} uploaded, "
                f"{len(corpus_result['skipped'])} unchanged, "
                f"{corpus_result['indexedItems']} documents processed."
            )
    finally:
        blob_service.close()
        service.index_client.close()
        credential.close()


if __name__ == "__main__":
    main()