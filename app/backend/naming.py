from dataclasses import asdict, dataclass


SHARED_DOCUMENT_SOURCE = "cocoarynth-documents-source"
SHARED_GENERATED_INDEX = "cocoarynth-documents-index"
SHARED_DOCUMENT_KNOWLEDGE_BASE = "cocoarynth-kb-docs"
SHARED_GITHUB_SOURCE = "cocoarynth-github-source"
SHARED_COMBINED_KNOWLEDGE_BASE = "cocoarynth-kb-all"


@dataclass(frozen=True)
class SharedResources:
    document_source: str
    generated_index: str
    document_knowledge_base: str
    github_source: str
    combined_knowledge_base: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def shared_resources() -> SharedResources:
    return SharedResources(
        document_source=SHARED_DOCUMENT_SOURCE,
        generated_index=SHARED_GENERATED_INDEX,
        document_knowledge_base=SHARED_DOCUMENT_KNOWLEDGE_BASE,
        github_source=SHARED_GITHUB_SOURCE,
        combined_knowledge_base=SHARED_COMBINED_KNOWLEDGE_BASE,
    )