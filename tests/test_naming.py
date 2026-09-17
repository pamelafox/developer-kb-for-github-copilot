import unittest

from app.backend.naming import shared_resources


class SharedResourcesTests(unittest.TestCase):
    def test_builds_two_shared_knowledge_base_names(self) -> None:
        resources = shared_resources()

        self.assertEqual(resources.document_source, "cocoarynth-documents-source")
        self.assertEqual(resources.generated_index, "cocoarynth-documents-index")
        self.assertEqual(resources.document_knowledge_base, "cocoarynth-kb-docs")
        self.assertEqual(resources.github_source, "cocoarynth-github-source")
        self.assertEqual(resources.combined_knowledge_base, "cocoarynth-kb-all")


if __name__ == "__main__":
    unittest.main()