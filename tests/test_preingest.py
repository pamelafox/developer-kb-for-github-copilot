import tempfile
import unittest
import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from azure.core.exceptions import HttpResponseError, ResourceExistsError

from app.backend.config import Settings
from scripts.preingest import (
    ENGINEERING_PRACTICE_CORPUS,
    build_indexer_payloads,
    ingest_corpora,
    ingest_with_retry,
    run_indexer_and_wait,
    sync_blob_corpus,
)


class IngestCorpusTests(unittest.TestCase):
    @patch("scripts.preingest.wait_for_indexer", side_effect=[0, 12])
    def test_waits_for_active_indexer_then_starts_fresh_run(self, wait: Mock) -> None:
        client = Mock()
        client.run_indexer.side_effect = [ResourceExistsError("Already running"), None]

        indexed_items = run_indexer_and_wait(client, "documents-indexer")

        self.assertEqual(indexed_items, 12)
        self.assertEqual(client.reset_indexer.call_count, 2)
        self.assertEqual(client.run_indexer.call_count, 2)
        self.assertEqual(wait.call_count, 2)
        self.assertEqual(wait.call_args_list[0].args, (client, "documents-indexer"))
        self.assertIsNotNone(wait.call_args_list[1].args[2])

    def test_uploads_changed_pdfs_and_removes_stale_blobs(self) -> None:
        container = Mock()
        existing_digest = hashlib.sha256(b"existing").hexdigest()
        container.list_blobs.return_value = [
            SimpleNamespace(name="existing.pdf", metadata={"sha256": existing_digest}),
            SimpleNamespace(name="stale.pdf", metadata={}),
        ]
        with tempfile.TemporaryDirectory() as directory:
            corpus_dir = Path(directory)
            (corpus_dir / "existing.pdf").write_bytes(b"existing")
            (corpus_dir / "new.pdf").write_bytes(b"new")
            (corpus_dir / "notes.txt").write_text("ignored")

            result = sync_blob_corpus(container, corpus_dir)

        container.delete_blob.assert_called_once_with("stale.pdf")
        container.upload_blob.assert_called_once()
        self.assertEqual(container.upload_blob.call_args.kwargs["name"], "new.pdf")
        self.assertEqual(
            result,
            {"uploaded": ["new.pdf"], "skipped": ["existing.pdf"], "deleted": ["stale.pdf"]},
        )

    def test_builds_content_understanding_blob_pipeline(self) -> None:
        settings = Settings(
            search_endpoint="https://example.search.windows.net",
            openai_endpoint="https://example.openai.azure.com",
            embedding_deployment="text-embedding-3-large",
            embedding_model="text-embedding-3-large",
            chat_deployment="gpt-4.1-mini",
            chat_model="gpt-4.1-mini",
            managed_identity_client_id=None,
        )

        pipeline = build_indexer_payloads(
            settings,
            "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/store",
            "https://example.services.ai.azure.com",
        )

        self.assertEqual(pipeline["datasources"][1]["type"], "azureblob")
        skillset = pipeline["skillsets"][1]
        self.assertEqual(
            skillset["skills"][0]["@odata.type"],
            "#Microsoft.Skills.Util.ContentUnderstandingSkill",
        )
        self.assertEqual(skillset["skills"][0]["chunkingProperties"]["maximumLength"], 700)
        self.assertIsInstance(skillset["knowledgeStore"]["projections"], list)
        self.assertEqual(
            skillset["knowledgeStore"]["projections"][0]["files"][0]["storageContainer"],
            "extracted-images",
        )
        self.assertEqual(pipeline["indexers"][1]["targetIndexName"], "cocoarynth-documents-index")

        style_pipeline = build_indexer_payloads(
            settings,
            "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/store",
            "https://example.services.ai.azure.com",
            ENGINEERING_PRACTICE_CORPUS,
        )
        self.assertEqual(style_pipeline["datasources"][1]["container"]["name"], "engineering-practices")
        self.assertEqual(style_pipeline["indexers"][1]["targetIndexName"], "cocoarynth-engineering-practices-index")
        self.assertEqual(
            style_pipeline["skillsets"][1]["knowledgeStore"]["projections"][0]["files"][0][
                "storageContainer"
            ],
            "engineering-practice-images",
        )

    @patch("scripts.preingest.wait_for_indexer", return_value=12)
    @patch("scripts.preingest.put_preview_resource")
    @patch("scripts.preingest.SearchIndexerClient")
    @patch("scripts.preingest.clear_index_documents", return_value=4)
    @patch("scripts.preingest.sync_blob_corpus")
    def test_ingestion_indexes_both_corpora_before_creating_knowledge_bases(
        self,
        sync_corpus: Mock,
        clear_documents: Mock,
        indexer_client_type: Mock,
        put_resource: Mock,
        wait: Mock,
    ) -> None:
        sync_corpus.return_value = {"uploaded": ["one.pdf"], "skipped": [], "deleted": []}
        service = Mock()
        service.settings = Settings(
            search_endpoint="https://example.search.windows.net",
            openai_endpoint="https://example.openai.azure.com",
            embedding_deployment="text-embedding-3-large",
            embedding_model="text-embedding-3-large",
            chat_deployment="gpt-4.1-mini",
            chat_model="gpt-4.1-mini",
            managed_identity_client_id=None,
        )

        blob_service = Mock()
        result = ingest_corpora(
            service,
            blob_service,
            "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/store",
            "https://example.services.ai.azure.com",
        )

        service.create_document_workspace.assert_called_once()
        service.create_shared_combined_workspace.assert_called_once()
        self.assertEqual(result["documents"]["indexedItems"], 12)
        self.assertEqual(result["engineeringPractices"]["removedChunks"], 4)
        self.assertEqual(put_resource.call_count, 6)
        self.assertEqual(indexer_client_type.return_value.run_indexer.call_count, 2)
        self.assertEqual(wait.call_count, 2)
        self.assertEqual(
            [call.args[0] for call in blob_service.get_container_client.call_args_list],
            ["knowledge", "engineering-practices"],
        )
        self.assertEqual(
            [call.args[1] for call in clear_documents.call_args_list],
            ["cocoarynth-documents-index", "cocoarynth-engineering-practices-index"],
        )

    @patch("scripts.preingest.time.sleep")
    def test_retries_while_search_rbac_propagates(self, sleep: Mock) -> None:
        forbidden = HttpResponseError("Forbidden")
        forbidden.status_code = 403
        operation = Mock(side_effect=[forbidden, {"uploaded": [], "skipped": []}])

        result = ingest_with_retry(operation, attempts=2, delay_seconds=1)

        self.assertEqual(result, {"uploaded": [], "skipped": []})
        sleep.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()