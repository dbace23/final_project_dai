import json

from term_deposit_advisor.domain.models import RetrievedSource


def serialize_retrieved_sources(sources: list[RetrievedSource]) -> str:
    return json.dumps(
        [
            {
                "document_id": source.document_id,
                "document_name": source.document_name,
                "page": source.page,
                "chunk_id": source.chunk_id,
                "content": source.content,
                "distance": source.distance,
            }
            for source in sources
        ],
        ensure_ascii=False,
    )
