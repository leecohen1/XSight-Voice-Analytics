#!/usr/bin/env bash
# Smoke-tests all four Phase 6 mock FastAPI services: health, one valid
# request per main endpoint, and at least one intentionally invalid request
# per service. Assumes the services are already running, either via
#   docker compose up -d
# or locally per-service (see each service's README).
#
# Usage: bash scripts/test_mock_services.sh [base_host]
#   base_host defaults to http://localhost

set -uo pipefail

HOST="${1:-http://localhost}"
RAG_URL="${HOST}:8001"
CSA_URL="${HOST}:8002"
GRD_URL="${HOST}:8003"
LGA_URL="${HOST}:8004"

PASS=0
FAIL=0

check() {
  local description="$1"
  local expected_status="$2"
  local actual_status="$3"
  if [ "$actual_status" = "$expected_status" ]; then
    echo "  PASS  $description (HTTP $actual_status)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL  $description (expected HTTP $expected_status, got $actual_status)"
    FAIL=$((FAIL + 1))
  fi
}

status_of() {
  curl -s -o /dev/null -w "%{http_code}" "$@"
}

echo "=== 1. Health checks ==="
check "rag_service /health"           200 "$(status_of "$RAG_URL/health")"
check "call_signal_analyser /health"  200 "$(status_of "$CSA_URL/health")"
check "guardrails_service /health"    200 "$(status_of "$GRD_URL/health")"
check "langgraph_agent /health"       200 "$(status_of "$LGA_URL/health")"

echo
echo "=== 2. Successful requests ==="

check "rag_service POST /query (valid)" 200 "$(status_of -X POST "$RAG_URL/query" \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing.", "top_k": 2}')"

check "call_signal_analyser POST /analyse-call (valid)" 200 "$(status_of -X POST "$CSA_URL/analyse-call" \
  -H "Content-Type: application/json" \
  -d '{"transcript": "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing.", "audio_features": {"call_duration_seconds": 420, "silence_ratio": 0.18, "speaking_rate_wpm": 145, "speech_to_non_speech_ratio": 0.82, "agent_talk_ratio": 0.62, "average_energy_level": "medium"}, "structured_fields": {"customer_intent": "high", "main_objection": "price", "customer_sentiment": "mixed", "closing_attempt": "weak", "decision_maker_present": true}}')"

check "guardrails_service POST /check/input pre_transcription (valid)" 200 "$(status_of -X POST "$GRD_URL/check/input" \
  -H "Content-Type: application/json" \
  -d '{"stage": "pre_transcription", "file_metadata": {"filename": "call.mp3", "mime_type": "audio/mpeg", "size_bytes": 1000000, "duration_seconds": 300}, "submission_metadata": {"agent_name": "Sarah Levi", "call_date": "2026-07-15"}}')"

check "guardrails_service POST /check/output (valid)" 200 "$(status_of -X POST "$GRD_URL/check/output" \
  -H "Content-Type: application/json" \
  -d '{"final_analysis": {"call_summary": "Price objection raised."}, "citations": ["CALL_007"], "historical_claims_present": true, "confidence": 0.82}')"

check "langgraph_agent POST /agent/run (valid)" 200 "$(status_of -X POST "$LGA_URL/agent/run" \
  -H "Content-Type: application/json" \
  -d '{"question": "Why did this call fail?", "transcript": "Agent: Hi there, thanks for the call. Customer: Sure, happy to talk about pricing.", "structured_extraction": {"closing_attempt": "weak"}, "rag_results": {"similar_calls": [{"call_id": "CALL_007"}], "citations": ["CALL_007"]}, "signal_analysis": {"predicted_outcome": "Follow-up Needed", "confidence": 0.72}}')"

echo
echo "=== 3. Intentionally invalid requests (expect 422) ==="

check "rag_service POST /query (empty transcript)" 422 "$(status_of -X POST "$RAG_URL/query" \
  -H "Content-Type: application/json" -d '{"transcript": ""}')"

check "rag_service POST /query (top_k out of range)" 422 "$(status_of -X POST "$RAG_URL/query" \
  -H "Content-Type: application/json" -d '{"transcript": "Agent: hi. Customer: hello there.", "top_k": 99}')"

check "call_signal_analyser POST /analyse-call (missing fields)" 422 "$(status_of -X POST "$CSA_URL/analyse-call" \
  -H "Content-Type: application/json" -d '{"transcript": "too short"}')"

check "guardrails_service POST /check/input (invalid stage)" 422 "$(status_of -X POST "$GRD_URL/check/input" \
  -H "Content-Type: application/json" -d '{"stage": "bogus_stage"}')"

check "guardrails_service POST /check/output (missing confidence)" 422 "$(status_of -X POST "$GRD_URL/check/output" \
  -H "Content-Type: application/json" -d '{"final_analysis": {}, "citations": []}')"

check "langgraph_agent POST /agent/run (missing question)" 422 "$(status_of -X POST "$LGA_URL/agent/run" \
  -H "Content-Type: application/json" -d '{"transcript": "Agent: hi. Customer: hello there, happy to chat."}')"

echo
echo "=== Summary: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
exit 0
