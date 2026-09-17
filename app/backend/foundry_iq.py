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
    McpServerAutoOutputParsing,
    McpServerKnowledgeSource,
    McpServerKnowledgeSourceParameters,
    McpServerStoredHeadersAuthentication,
    McpServerStoredHeadersParameters,
    McpServerTool,
    SearchIndexFieldReference,
    SearchIndexKnowledgeSource,
    SearchIndexKnowledgeSourceParameters,
)
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.search.documents.knowledgebases.models import (
    KnowledgeBaseMessage,
    KnowledgeBaseMessageTextContent,
    KnowledgeBaseRetrievalRequest,
    KnowledgeRetrievalMediumReasoningEffort,
    KnowledgeRetrievalOutputMode,
    KnowledgeSourceParams,
    SearchIndexKnowledgeSourceParams,
)
from azure.storage.blob import BlobServiceClient

from .config import Settings
from .naming import SharedResources

CORPUS_CONTAINER = "knowledge"
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
                search_index_name=resources.generated_index,
                source_data_fields=[
                    SearchIndexFieldReference(name=field_name)
                    for field_name in (
                        "chunk_id",
                        "parent_id",
                        "title",
                        "blob_path",
                        "chunk",
                        "page_number_from",
                        "page_number_to",
                        "image_path",
                    )
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
            output_mode=KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA,
        )
        self.index_client.create_or_update_knowledge_base(knowledge_base)
        return resources.as_dict()

    def list_documents(self) -> dict[str, Any]:
        container = self.blob_service.get_container_client(CORPUS_CONTAINER)
        try:
            documents = [
                {
                    "name": blob.name,
                    "size": blob.size,
                    "lastModified": blob.last_modified.isoformat() if blob.last_modified else None,
                    "url": f"/api/documents/content/{blob.name}",
                }
                for blob in container.list_blobs()
            ]
        finally:
            container.close()
        return {"container": CORPUS_CONTAINER, "documents": sorted(documents, key=lambda item: item["name"])}

    def download_document(self, blob_name: str) -> tuple[bytes, str]:
        blob = self.blob_service.get_blob_client(CORPUS_CONTAINER, blob_name)
        try:
            content = blob.download_blob().readall()
            properties = blob.get_blob_properties()
            content_type = properties.content_settings.content_type or "application/octet-stream"
            return content, content_type
        finally:
            blob.close()

    def list_chunks(self, resources: SharedResources, document: str, limit: int = 100) -> dict[str, Any]:
        index_name = self._find_generated_index(resources)
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

    def search_documents(self, resources: SharedResources, query: str, limit: int = 10) -> dict[str, Any]:
        client = SearchClient(self.settings.search_endpoint, resources.generated_index, self.credential)
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
        return {"index": resources.generated_index, "query": query, "matches": matches}

    def get_knowledge_base_configuration(self, resources: SharedResources) -> dict[str, Any]:
        knowledge_bases = []
        for name in (resources.document_knowledge_base, resources.combined_knowledge_base):
            knowledge_base = self.index_client.get_knowledge_base(name).as_dict()
            knowledge_bases.append(self._redact_secrets(knowledge_base))
        knowledge_sources = []
        for name in (resources.document_source, resources.github_source):
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
            )
        ]
        if combined:
            source_params.append(
                KnowledgeSourceParams(
                    knowledge_source_name=resources.github_source,
                    include_references=True,
                    include_reference_source_data=True,
                    kind="mcpServer",
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
        if not self.settings.github_pat:
            raise ValueError("The instructor has not configured GITHUB_LAB_PAT.")

        github_source = McpServerKnowledgeSource(
            name=resources.github_source,
            description="Read-only live evidence from the pamelafox/cocoarynth-trace GitHub repository",
            mcp_server_parameters=McpServerKnowledgeSourceParameters(
                server_url=self.settings.github_mcp_url,
                authentication=McpServerStoredHeadersAuthentication(
                    stored_headers_parameters=McpServerStoredHeadersParameters(
                        {"headers": {"Authorization": f"Bearer {self.settings.github_pat}"}}
                    )
                ),
                tools=[
                    McpServerTool(
                        name=tool,
                        output_parsing=McpServerAutoOutputParsing(),
                        **({"inclusion_mode": "always"} if tool in {"search_code", "search_issues"} else {}),
                    )
                    for tool in self.settings.github_mcp_tools
                ],
            ),
        )
        self.index_client.create_or_update_knowledge_source(github_source)

        knowledge_base = KnowledgeBase(
            name=resources.combined_knowledge_base,
            description="Shared indexed documents and live GitHub evidence for the Cocoarynth workshop",
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
                KnowledgeSourceReference(name=resources.github_source),
            ],
            retrieval_reasoning_effort=KnowledgeRetrievalMediumReasoningEffort(),
            output_mode=KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA,
            retrieval_instructions=(
                "Use indexed documents for policies and requirements. Use GitHub tools for live repository files, "
                "issues, and pull requests only in pamelafox/cocoarynth-trace. For search_code, put the repository "
                "qualifier inside the query string, for example: "
                "{'query': 'pilot requirements repo:pamelafox/cocoarynth-trace'}. search_code does not accept "
                "separate owner or repo arguments. For search_issues, always set owner to 'pamelafox' and repo to "
                "'cocoarynth-trace', for example: {'query': 'pilot requirements', 'owner': 'pamelafox', "
                "'repo': 'cocoarynth-trace'}. For get_file_contents, issue_read, and pull_request_read, also set "
                "owner to 'pamelafox' and repo to 'cocoarynth-trace'. Do not search or read any other repository. "
                "Use search_issues to find relevant issue numbers and search_code to find relevant file paths before "
                "reading them. Cite the source of factual claims."
            ),
        )
        self.index_client.create_or_update_knowledge_base(knowledge_base)
        return resources.as_dict()

    def _find_generated_index(self, resources: SharedResources) -> str:
        self.index_client.get_index(resources.generated_index)
        return resources.generated_index
