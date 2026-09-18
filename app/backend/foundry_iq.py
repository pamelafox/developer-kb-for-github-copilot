from typing import Any

from azure.core.credentials import TokenCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType, VectorizableTextQuery
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureOpenAIVectorizerParameters,
    KnowledgeBase,
    KnowledgeBaseAzureOpenAIModel,
    KnowledgeSourceReference,
    SearchIndexFieldReference,
    SearchIndexKnowledgeSource,
    SearchIndexKnowledgeSourceParameters,
)
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import (
    KnowledgeBaseMessage,
    KnowledgeBaseMessageTextContent,
    KnowledgeBaseRetrievalRequest,
    KnowledgeRetrievalLowReasoningEffort,
    KnowledgeRetrievalMinimalReasoningEffort,
    KnowledgeRetrievalOutputMode,
    SearchIndexKnowledgeSourceParams,
)
from azure.storage.blob import BlobServiceClient

from .config import Settings
from .naming import SharedResources

CORPUS_CONTAINER = "knowledge"
ENGINEERING_PRACTICE_CONTAINER = "engineering-practices"
RERANKER_THRESHOLD = 1.7
CHUNK_FIELDS = [
    "chunk_id",
    "parent_id",
    "title",
    "blob_path",
    "chunk",
    "page_number_from",
    "page_number_to",
    "image_path",
]
SOURCE_DATA_FIELDS = [field_name for field_name in CHUNK_FIELDS if field_name != "chunk"]


class FoundryIqService:
    def __init__(self, settings: Settings, credential: TokenCredential) -> None:
        self.settings = settings
        self.credential = credential
        self.index_client = SearchIndexClient(settings.search_endpoint, credential)
        self.blob_service = BlobServiceClient(
            account_url=f"https://{settings.storage_account_name}.blob.core.windows.net",
            credential=credential,
        )

    def _model_parameters(self, deployment: str, model: str) -> AzureOpenAIVectorizerParameters:
        return AzureOpenAIVectorizerParameters(
            resource_url=self.settings.openai_endpoint,
            deployment_name=deployment,
            model_name=model,
        )

    def create_document_workspace(self, resources: SharedResources) -> dict[str, Any]:
        document_source = SearchIndexKnowledgeSource(
            name=resources.document_source,
            description="Cocoarynth workshop documents processed with Content Understanding",
            search_index_parameters=SearchIndexKnowledgeSourceParameters(
                search_index_name=resources.document_index,
                source_data_fields=[
                    SearchIndexFieldReference(name=field_name)
                    for field_name in SOURCE_DATA_FIELDS
                ],
                search_fields=[SearchIndexFieldReference(name="chunk")],
                semantic_configuration_name="semantic-configuration",
            ),
        )
        self.index_client.create_or_update_knowledge_source(document_source)

        knowledge_base = KnowledgeBase(
            name=resources.document_knowledge_base,
            description="Shared documents-only knowledge base for the Cocoarynth workshop",
            models=[
                KnowledgeBaseAzureOpenAIModel(
                    azure_open_ai_parameters=self._model_parameters(
                        self.settings.chat_deployment,
                        self.settings.chat_model,
                    )
                )
            ],
            knowledge_sources=[KnowledgeSourceReference(name=resources.document_source)],
            retrieval_reasoning_effort=KnowledgeRetrievalMinimalReasoningEffort(),
            output_mode=KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA,
        )
        self.index_client.create_or_update_knowledge_base(knowledge_base)
        return resources.as_dict()

    def list_documents(
        self,
        container_name: str = CORPUS_CONTAINER,
        content_path: str = "/api/documents/content",
    ) -> dict[str, Any]:
        container = self.blob_service.get_container_client(container_name)
        try:
            documents = [
                {
                    "name": blob.name,
                    "size": blob.size,
                    "lastModified": blob.last_modified.isoformat() if blob.last_modified else None,
                    "url": f"{content_path}/{blob.name}",
                }
                for blob in container.list_blobs()
            ]
        finally:
            container.close()
        return {"container": container_name, "documents": sorted(documents, key=lambda item: item["name"])}

    def download_document(
        self,
        blob_name: str,
        container_name: str = CORPUS_CONTAINER,
    ) -> tuple[bytes, str]:
        blob = self.blob_service.get_blob_client(container_name, blob_name)
        try:
            content = blob.download_blob().readall()
            properties = blob.get_blob_properties()
            content_type = properties.content_settings.content_type or "application/octet-stream"
            return content, content_type
        finally:
            blob.close()

    def list_chunks(
        self,
        resources: SharedResources,
        document: str,
        limit: int = 100,
        index_name: str | None = None,
    ) -> dict[str, Any]:
        index_name = index_name or self._find_document_index(resources)
        client = SearchClient(self.settings.search_endpoint, index_name, self.credential)
        try:
            escaped_document = document.replace("'", "''")
            results = client.search(
                "*",
                filter=f"title eq '{escaped_document}'",
                order_by=["page_number_from asc", "page_number_to asc", "chunk_id asc"],
                top=limit,
                select=CHUNK_FIELDS,
            )
            documents = [dict(result) for result in results]
        finally:
            client.close()
        return {"index": index_name, "document": document, "chunks": documents}

    def search_documents(
        self,
        resources: SharedResources,
        query: str,
        limit: int = 10,
        index_name: str | None = None,
    ) -> dict[str, Any]:
        index_name = index_name or resources.document_index
        client = SearchClient(self.settings.search_endpoint, index_name, self.credential)
        try:
            results = client.search(
                search_text=query,
                vector_queries=[
                    VectorizableTextQuery(
                        text=query,
                        k_nearest_neighbors=50,
                        fields="text_vector",
                    )
                ],
                query_type=QueryType.SEMANTIC,
                semantic_configuration_name="semantic-configuration",
                query_caption="extractive",
                top=limit,
                select=CHUNK_FIELDS,
            )
            matches = [self._serialize_search_value(dict(result)) for result in results]
        finally:
            client.close()
        return {"index": index_name, "query": query, "matches": matches}

    def get_knowledge_base_configuration(self, resources: SharedResources) -> dict[str, Any]:
        knowledge_bases = []
        for name in (
            resources.document_knowledge_base,
            resources.engineering_practice_knowledge_base,
            resources.combined_knowledge_base,
        ):
            knowledge_base = self.index_client.get_knowledge_base(name).as_dict()
            knowledge_base["rerankerThreshold"] = RERANKER_THRESHOLD
            knowledge_base["mcpUrl"] = (
                f"{self.settings.search_endpoint}/knowledgebases/{name}/mcp"
                "?api-version=2026-08-01-preview"
            )
            knowledge_bases.append(self._redact_secrets(knowledge_base))
        knowledge_sources = []
        for name in (resources.document_source, resources.engineering_practice_source):
            source = self.index_client.get_knowledge_source(name).as_dict()
            knowledge_sources.append(self._redact_secrets(source))
        return {"knowledgeBases": knowledge_bases, "knowledgeSources": knowledge_sources}

    def retrieve(self, resources: SharedResources, question: str, combined: bool) -> dict[str, Any]:
        knowledge_base_name = (
            resources.combined_knowledge_base if combined else resources.document_knowledge_base
        )
        source_params = [
            SearchIndexKnowledgeSourceParams(
                knowledge_source_name=resources.document_source,
                include_references=True,
                include_reference_source_data=True,
                reranker_threshold=RERANKER_THRESHOLD,
            )
        ]
        if combined:
            source_params.append(
                SearchIndexKnowledgeSourceParams(
                    knowledge_source_name=resources.engineering_practice_source,
                    include_references=True,
                    include_reference_source_data=True,
                    reranker_threshold=RERANKER_THRESHOLD,
                )
            )
        request = KnowledgeBaseRetrievalRequest(
            messages=[
                KnowledgeBaseMessage(
                    role="user",
                    content=[KnowledgeBaseMessageTextContent(text=question)],
                )
            ],
            knowledge_source_params=source_params,
            include_activity=True,
            output_mode=KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA,
            max_runtime_in_seconds=120,
        )
        client = KnowledgeBaseRetrievalClient(
            endpoint=self.settings.search_endpoint,
            knowledge_base_name=knowledge_base_name,
            credential=self.credential,
        )
        try:
            return client.retrieve(retrieval_request=request).as_dict()
        finally:
            client.close()

    @classmethod
    def _serialize_search_value(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: cls._serialize_search_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._serialize_search_value(item) for item in value]
        if hasattr(value, "as_dict"):
            return cls._serialize_search_value(value.as_dict())
        return value

    @classmethod
    def _redact_secrets(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: cls._redact_secrets(item)
                for key, item in value.items()
                if key.lower() not in {"authentication", "headers", "stored_headers", "api_key", "key"}
            }
        if isinstance(value, list):
            return [cls._redact_secrets(item) for item in value]
        return value

    def create_shared_combined_workspace(self, resources: SharedResources) -> dict[str, Any]:
        engineering_practice_source = SearchIndexKnowledgeSource(
            name=resources.engineering_practice_source,
            description="Cocoarynth engineering, API, frontend, accessibility, and engineering culture guidance",
            search_index_parameters=SearchIndexKnowledgeSourceParameters(
                search_index_name=resources.engineering_practice_index,
                source_data_fields=[
                    SearchIndexFieldReference(name=field_name)
                    for field_name in SOURCE_DATA_FIELDS
                ],
                search_fields=[SearchIndexFieldReference(name="chunk")],
                semantic_configuration_name="semantic-configuration",
            ),
        )
        self.index_client.create_or_update_knowledge_source(engineering_practice_source)

        engineering_practice_knowledge_base = KnowledgeBase(
            name=resources.engineering_practice_knowledge_base,
            description="Shared engineering-practices knowledge base for the Cocoarynth workshop",
            models=[
                KnowledgeBaseAzureOpenAIModel(
                    azure_open_ai_parameters=self._model_parameters(
                        self.settings.chat_deployment,
                        self.settings.chat_model,
                    )
                )
            ],
            knowledge_sources=[KnowledgeSourceReference(name=resources.engineering_practice_source)],
            retrieval_reasoning_effort=KnowledgeRetrievalMinimalReasoningEffort(),
            output_mode=KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA,
        )
        self.index_client.create_or_update_knowledge_base(engineering_practice_knowledge_base)

        knowledge_base = KnowledgeBase(
            name=resources.combined_knowledge_base,
            description="Shared project documents and company engineering practices for the Cocoarynth workshop",
            models=[
                KnowledgeBaseAzureOpenAIModel(
                    azure_open_ai_parameters=self._model_parameters(
                        self.settings.chat_deployment,
                        self.settings.chat_model,
                    )
                )
            ],
            knowledge_sources=[
                KnowledgeSourceReference(name=resources.document_source),
                KnowledgeSourceReference(name=resources.engineering_practice_source),
            ],
            retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort(),
            output_mode=KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA,
            retrieval_instructions=(
                "Use project documents for product requirements, architecture decisions, policies, and support "
                "constraints. Use company engineering practices for React, API, frontend design, accessibility, and engineering culture. "
                "Distinguish product requirements from implementation guidance and cite factual claims."
            ),
        )
        self.index_client.create_or_update_knowledge_base(knowledge_base)
        return resources.as_dict()

    def _find_document_index(self, resources: SharedResources) -> str:
        self.index_client.get_index(resources.document_index)
        return resources.document_index
