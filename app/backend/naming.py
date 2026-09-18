from dataclasses import asdict, dataclass


SHARED_DOCUMENT_SOURCE = "cocoarynth-documents-source"
SHARED_DOCUMENT_INDEX = "cocoarynth-documents-index"
SHARED_DOCUMENT_KNOWLEDGE_BASE = "cocoarynth-kb-docs"
SHARED_ENGINEERING_PRACTICE_SOURCE = "cocoarynth-engineering-practices-source"
SHARED_ENGINEERING_PRACTICE_INDEX = "cocoarynth-engineering-practices-index"
SHARED_ENGINEERING_PRACTICE_KNOWLEDGE_BASE = "cocoarynth-kb-engineering-practices"
SHARED_COMBINED_KNOWLEDGE_BASE = "cocoarynth-kb-all"


@dataclass(frozen=True)
class SharedResources:
    document_source: str
    document_index: str
    document_knowledge_base: str
    engineering_practice_source: str
    engineering_practice_index: str
    engineering_practice_knowledge_base: str
    combined_knowledge_base: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def shared_resources() -> SharedResources:
    return SharedResources(
        document_source=SHARED_DOCUMENT_SOURCE,
        document_index=SHARED_DOCUMENT_INDEX,
        document_knowledge_base=SHARED_DOCUMENT_KNOWLEDGE_BASE,
        engineering_practice_source=SHARED_ENGINEERING_PRACTICE_SOURCE,
        engineering_practice_index=SHARED_ENGINEERING_PRACTICE_INDEX,
        engineering_practice_knowledge_base=SHARED_ENGINEERING_PRACTICE_KNOWLEDGE_BASE,
        combined_knowledge_base=SHARED_COMBINED_KNOWLEDGE_BASE,
    )