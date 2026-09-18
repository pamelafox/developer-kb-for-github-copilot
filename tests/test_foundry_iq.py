import unittest
from unittest.mock import Mock, patch

from app.backend.config import Settings
from app.backend.foundry_iq import FoundryIqService
from app.backend.naming import shared_resources
from azure.search.documents.indexes.models import SearchIndexKnowledgeSource
from azure.search.documents.knowledgebases.models import KnowledgeRetrievalOutputMode


class FoundryIqServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = FoundryIqService.__new__(FoundryIqService)
        self.service.settings = Settings(
            search_endpoint="https://example.search.windows.net",
            openai_endpoint="https://example.openai.azure.com",
            embedding_deployment="text-embedding-3-large",
            embedding_model="text-embedding-3-large",
            chat_deployment="gpt-4.1-mini",
            chat_model="gpt-4.1-mini",
            managed_identity_client_id=None,
        )
        self.service.credential = Mock()
        self.service.index_client = Mock()
        self.resources = shared_resources()

    def test_constructs_document_resources_with_preview_sdk(self) -> None:
        result = self.service.create_document_workspace(self.resources)

        self.assertEqual(result["document_source"], "cocoarynth-documents-source")
        self.service.index_client.create_or_update_knowledge_source.assert_called_once()
        source = self.service.index_client.create_or_update_knowledge_source.call_args.args[0]
        self.assertIsInstance(source, SearchIndexKnowledgeSource)
        self.assertEqual(source.search_index_parameters.search_index_name, "cocoarynth-documents-index")
        self.assertNotIn(
            "chunk",
            [field.name for field in source.search_index_parameters.source_data_fields],
        )
        self.assertEqual(
            [field.name for field in source.search_index_parameters.search_fields],
            ["chunk"],
        )
        self.service.index_client.create_or_update_knowledge_base.assert_called_once()
        knowledge_base = self.service.index_client.create_or_update_knowledge_base.call_args.args[0]
        self.assertEqual(knowledge_base.output_mode, KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA)
        self.assertEqual(knowledge_base.retrieval_reasoning_effort.kind, "minimal")

    def test_constructs_combined_resources_with_preview_sdk(self) -> None:
        result = self.service.create_shared_combined_workspace(self.resources)

        self.assertEqual(result["combined_knowledge_base"], "cocoarynth-kb-all")
        source = self.service.index_client.create_or_update_knowledge_source.call_args.args[0]
        self.assertIsInstance(source, SearchIndexKnowledgeSource)
        self.assertEqual(source.name, "cocoarynth-engineering-practices-source")
        self.assertEqual(source.search_index_parameters.search_index_name, "cocoarynth-engineering-practices-index")
        self.assertNotIn(
            "chunk",
            [field.name for field in source.search_index_parameters.source_data_fields],
        )
        self.assertEqual(
            [field.name for field in source.search_index_parameters.search_fields],
            ["chunk"],
        )
        self.assertEqual(self.service.index_client.create_or_update_knowledge_base.call_count, 2)
        engineering_practice_knowledge_base, knowledge_base = [
            call.args[0]
            for call in self.service.index_client.create_or_update_knowledge_base.call_args_list
        ]
        self.assertEqual(engineering_practice_knowledge_base.name, "cocoarynth-kb-engineering-practices")
        self.assertEqual(engineering_practice_knowledge_base.retrieval_reasoning_effort.kind, "minimal")
        self.assertEqual(
            [reference.name for reference in engineering_practice_knowledge_base.knowledge_sources],
            ["cocoarynth-engineering-practices-source"],
        )
        self.assertEqual(knowledge_base.output_mode, KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA)
        self.assertEqual(knowledge_base.retrieval_reasoning_effort.kind, "low")
        self.assertIn("product requirements", knowledge_base.retrieval_instructions)
        self.assertIn("company engineering practices", knowledge_base.retrieval_instructions)
        self.assertIn("engineering culture", knowledge_base.retrieval_instructions)
        self.assertEqual(
            [reference.name for reference in knowledge_base.knowledge_sources],
            ["cocoarynth-documents-source", "cocoarynth-engineering-practices-source"],
        )

    def test_discovers_only_the_shared_document_index(self) -> None:
        self.assertEqual(self.service._find_document_index(self.resources), "cocoarynth-documents-index")
        self.service.index_client.get_index.assert_called_once_with("cocoarynth-documents-index")

    @patch("app.backend.foundry_iq.SearchClient")
    def test_lists_ordered_chunks_for_one_document(self, search_client_type: Mock) -> None:
        search_client_type.return_value.search.return_value = [{"chunk_id": "chunk-1"}]

        result = self.service.list_chunks(self.resources, "pilot.pdf")

        self.assertEqual(result["chunks"], [{"chunk_id": "chunk-1"}])
        arguments = search_client_type.return_value.search.call_args.kwargs
        self.assertEqual(arguments["filter"], "title eq 'pilot.pdf'")
        self.assertEqual(
            arguments["order_by"],
            ["page_number_from asc", "page_number_to asc", "chunk_id asc"],
        )

    @patch("app.backend.foundry_iq.SearchClient")
    def test_lists_engineering_practice_chunks_from_separate_index(self, search_client_type: Mock) -> None:
        search_client_type.return_value.search.return_value = [{"chunk_id": "style-chunk-1"}]

        result = self.service.list_chunks(
            self.resources,
            "engineering-culture.pdf",
            index_name=self.resources.engineering_practice_index,
        )

        self.assertEqual(result["index"], "cocoarynth-engineering-practices-index")
        search_client_type.assert_called_once_with(
            self.service.settings.search_endpoint,
            "cocoarynth-engineering-practices-index",
            self.service.credential,
        )

    @patch("app.backend.foundry_iq.SearchClient")
    def test_runs_hybrid_semantic_search(self, search_client_type: Mock) -> None:
        caption = Mock()
        caption.as_dict.return_value = {"text": "CSV is required.", "highlights": "<em>CSV</em> is required."}
        search_client_type.return_value.search.return_value = [
            {"chunk_id": "chunk-1", "@search.captions": [caption]}
        ]

        result = self.service.search_documents(self.resources, "CSV export")

        self.assertEqual(
            result["matches"],
            [
                {
                    "chunk_id": "chunk-1",
                    "@search.captions": [{"text": "CSV is required.", "highlights": "<em>CSV</em> is required."}],
                }
            ],
        )
        arguments = search_client_type.return_value.search.call_args.kwargs
        self.assertEqual(arguments["search_text"], "CSV export")
        self.assertEqual(arguments["vector_queries"][0].text, "CSV export")
        self.assertEqual(arguments["semantic_configuration_name"], "semantic-configuration")

    @patch("app.backend.foundry_iq.KnowledgeBaseRetrievalClient")
    def test_retrieval_requests_extractive_data_and_activity(self, retrieval_client_type: Mock) -> None:
        retrieval_client_type.return_value.retrieve.return_value.as_dict.return_value = {"activity": []}

        self.service.retrieve(self.resources, "What changed?", False)

        request = retrieval_client_type.return_value.retrieve.call_args.kwargs["retrieval_request"]
        self.assertEqual(request.output_mode, KnowledgeRetrievalOutputMode.EXTRACTIVE_DATA)
        self.assertTrue(request.include_activity)
        self.assertEqual(request.knowledge_source_params[0].reranker_threshold, 1.7)

        self.service.retrieve(self.resources, "What changed?", True)

        combined_request = retrieval_client_type.return_value.retrieve.call_args.kwargs["retrieval_request"]
        self.assertEqual(
            [source.reranker_threshold for source in combined_request.knowledge_source_params],
            [1.7, 1.7],
        )

    def test_redacts_stored_authentication_from_configuration(self) -> None:
        self.service.index_client.get_knowledge_base.return_value.as_dict.return_value = {
            "name": "kb",
            "knowledge_sources": [{"name": "source"}],
        }
        self.service.index_client.get_knowledge_source.return_value.as_dict.return_value = {
            "name": "source",
            "authentication": {"headers": {"Authorization": "Bearer secret"}},
        }

        result = self.service.get_knowledge_base_configuration(self.resources)

        serialized = str(result)
        self.assertIn("cocoarynth-kb-docs/mcp?api-version=2026-08-01-preview", serialized)
        self.assertIn("cocoarynth-kb-engineering-practices/mcp?api-version=2026-08-01-preview", serialized)
        self.assertIn("cocoarynth-kb-all/mcp?api-version=2026-08-01-preview", serialized)
        self.assertEqual(
            [knowledge_base["rerankerThreshold"] for knowledge_base in result["knowledgeBases"]],
            [1.7, 1.7, 1.7],
        )
        self.assertNotIn("Bearer secret", serialized)
        self.assertNotIn("authentication", serialized)

if __name__ == "__main__":
    unittest.main()