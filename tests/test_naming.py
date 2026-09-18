import unittest

from app.backend.naming import shared_resources


class SharedResourcesTests(unittest.TestCase):
    def test_builds_three_shared_knowledge_base_names(self) -> None:
        resources = shared_resources()

        self.assertEqual(resources.document_source, "cocoarynth-documents-source")
        self.assertEqual(resources.document_index, "cocoarynth-documents-index")
        self.assertEqual(resources.document_knowledge_base, "cocoarynth-kb-docs")
        self.assertEqual(
            resources.engineering_practice_source,
            "cocoarynth-engineering-practices-source",
        )
        self.assertEqual(
            resources.engineering_practice_index,
            "cocoarynth-engineering-practices-index",
        )
        self.assertEqual(
            resources.engineering_practice_knowledge_base,
            "cocoarynth-kb-engineering-practices",
        )
        self.assertEqual(resources.combined_knowledge_base, "cocoarynth-kb-all")


if __name__ == "__main__":
    unittest.main()