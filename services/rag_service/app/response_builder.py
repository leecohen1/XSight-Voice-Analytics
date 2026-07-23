"""Builds the QueryResponse from a raw Bedrock RetrievalOutcome.

Deterministic template logic only — no LLM call, per the approved
architecture (services/rag_service/ingestion/README.md, "Retrieval
strategy"). Every field in the response must trace back to something
Bedrock actually returned; nothing here invents a value that wasn't present
in the retrieved metadata.
"""
import logging

from app.bedrock_client import RetrievalOutcome
from app.models import QueryResponse, RetrievalMetadata, SimilarCall

logger = logging.getLogger("rag_service")

# Below this cosine similarity score, a result is evidence but not similar
# enough to cite as a matching historical call. See ingestion README,
# "Retrieval strategy": "the FastAPI wrapper should apply a similarity-score
# floor before building similar_calls[]".
SIMILARITY_SCORE_FLOOR = 0.5

# A retrieved result is only usable if Bedrock's metadata actually contains
# these — they're the fields the documented similar_calls[] contract
# requires (CLAUDE.md Component 3). A result missing any of these is
# dropped, not filled in, per "never invent missing metadata".
REQUIRED_RESULT_FIELDS = ("call_id", "agent_name", "sale_result", "main_objection")


def _build_similar_call(result: dict) -> SimilarCall | None:
    metadata = result.get("metadata") or {}
    missing = [f for f in REQUIRED_RESULT_FIELDS if f not in metadata]
    if missing:
        logger.warning(
            "Dropping a Bedrock retrieval result missing required metadata field(s) %s "
            "(chunk id: %s) — never fabricating a substitute value.",
            missing, metadata.get("x-amz-bedrock-kb-chunk-id", "unknown"),
        )
        return None
    if "score" not in result:
        logger.warning("Dropping a Bedrock retrieval result with no similarity score.")
        return None

    call_id = str(metadata["call_id"])
    main_objection = str(metadata["main_objection"])
    sale_result = str(metadata["sale_result"])
    return SimilarCall(
        call_id=call_id,
        agent_name=str(metadata["agent_name"]),
        sale_result=sale_result,
        main_objection=main_objection,
        similarity_score=float(result["score"]),
        reason=f"Historical call {call_id} with a '{main_objection}' objection; outcome: {sale_result}.",
    )


def build_response(
    outcome: RetrievalOutcome,
    knowledge_base_id: str,
    filter_requested: str | None,
    dropped_filter_keys: list[str],
) -> QueryResponse:
    candidates = [_build_similar_call(r) for r in outcome.results]
    above_floor = [c for c in candidates if c is not None and c.similarity_score >= SIMILARITY_SCORE_FLOOR]

    citations = [c.call_id for c in above_floor]
    if above_floor:
        insight = (
            f"Found {len(above_floor)} similar historical call(s) "
            f"({', '.join(citations)}) - see each result's reason for the specific match."
        )
    else:
        insight = "Not enough evidence to identify similar historical calls for this transcript."

    return QueryResponse(
        similar_calls=above_floor,
        insight=insight,
        citations=citations,
        grounded=bool(citations),
        retrieval_metadata=RetrievalMetadata(
            knowledge_base_id=knowledge_base_id,
            search_type=outcome.search_type,
            filter_requested=filter_requested,
            filter_applied=outcome.filter_applied,
            dropped_filter_keys=dropped_filter_keys,
            results_returned=len(outcome.results),
            results_above_threshold=len(above_floor),
        ),
    )
