# XSight — Dataset Validation Report (Phase 5C)

**Validation date:** 2026-07-15
**Validated file:** `data/historical_sales_calls.csv`
**Validation command:** `python scripts/validate_historical_dataset.py`
**Final status: READY WITH WARNINGS**

This report is generated entirely by `scripts/validate_historical_dataset.py` — every number below is computed directly from the CSV at validation time, not carried over from prior manual review. Re-run the script any time the CSV changes to regenerate this report.

> **Normalization note (Phase 5C refinement):** an earlier validation pass found `speaking_rate_wpm` (all 24 rows, by 3–6 wpm) and `price_mentions_count` (5 rows: CALL_003, 014, 017, 018, 023) computed with the original Phase 5B.1 hand-counting method instead of this script's canonical algorithms (`compute_word_counts` / `PRICE_KEYWORDS` in `validate_historical_dataset.py`). `scripts/normalize_dataset_fields.py` was run once to overwrite those two fields in `data/historical_sales_calls.csv` with the canonical recomputed values — 29 field values changed across 24 rows. No other column (transcript, metadata, Ground Truth fields, outcomes, intent, objections, sentiment, scores, `manager_notes`, `competitor_mentions_count`, `call_duration_seconds`, `silence_ratio`, `speech_to_non_speech_ratio`, `agent_talk_ratio`) was touched. This validation run confirms the result: those 25 warnings no longer appear below.

---

## 1. Schema

- Total rows: **24** (expected 24)
- Total columns: **26** (expected 26)
- Column order matches `dataset_design.md` §14 exactly: **YES**

| # | Column |
|---|---|
| 1 | `call_id` |
| 2 | `agent_name` |
| 3 | `customer_segment` |
| 4 | `industry` |
| 5 | `transcript` |
| 6 | `call_duration_seconds` |
| 7 | `sale_result` |
| 8 | `customer_intent` |
| 9 | `main_objection` |
| 10 | `customer_sentiment` |
| 11 | `agent_performance_score` |
| 12 | `objection_handling_quality` |
| 13 | `closing_attempt` |
| 14 | `follow_up_needed` |
| 15 | `lead_quality_score` |
| 16 | `call_category` |
| 17 | `next_meeting_scheduled` |
| 18 | `decision_maker_present` |
| 19 | `silence_ratio` |
| 20 | `speaking_rate_wpm` |
| 21 | `speech_to_non_speech_ratio` |
| 22 | `agent_talk_ratio` |
| 23 | `average_energy_level` |
| 24 | `price_mentions_count` |
| 25 | `competitor_mentions_count` |
| 26 | `manager_notes` |

---

## 2. Enum validation

All enum-typed columns checked against the taxonomies in `dataset_design.md` §4–§10:

- `customer_segment`: ['Enterprise', 'Mid-Market', 'SMB']
- `sale_result`: ['Follow-up Needed', 'No Sale', 'Sale']
- `customer_intent`: ['high', 'low', 'medium', 'unclear']
- `main_objection`: ['authority', 'competitor', 'integration', 'no_need', 'none', 'other', 'price', 'security', 'timing', 'trust']
- `customer_sentiment`: ['mixed', 'negative', 'neutral', 'positive']
- `closing_attempt`: ['medium', 'none', 'strong', 'weak']
- `call_category`: ['Coaching Required', 'Failed Sale', 'Follow-up Needed', 'High-Value Opportunity', 'Human Review Required', 'Successful Sale']
- `average_energy_level`: ['high', 'low', 'medium']

**Note on `call_category`:** this is a routing/business category (dataset_design.md §10), not a restatement of `sale_result`. A `Sale` can legitimately be `Successful Sale` or `High-Value Opportunity`; a `No Sale` can be `Failed Sale`; any outcome can be `Coaching Required` or `Human Review Required` depending on execution quality, not just result. Only the literal pairs `(Successful Sale, sale_result≠Sale)` and `(Failed Sale, sale_result≠No Sale)` are treated as contradictions — the taxonomy is intentionally not 1:1 with `sale_result`.

---

## 3. Numeric range validation

| Field | Realistic range |
|---|---|
| `call_duration_seconds` | 180–900 |
| `silence_ratio` | 0.05–0.35 |
| `speaking_rate_wpm` | 100–190 |
| `speech_to_non_speech_ratio` | 0.65–0.95 |
| `agent_talk_ratio` | 0.35–0.75 |
| `agent_performance_score`, `objection_handling_quality`, `lead_quality_score` | 1–5 (integer) |
| `price_mentions_count`, `competitor_mentions_count` | ≥ 0 (integer) |

---

## 4. Duplicate checks

- Unique `call_id` values: checked against exact set `CALL_001`–`CALL_024`.
- Transcript uniqueness: checked by exact-text comparison across all rows.

---

## 5. Corpus-wide distributions

### Outcome balance

| Outcome | Count | Expected |
|---|---|---|
| Sale | 8 | 8 |
| No Sale | 8 | 8 |
| Follow-up Needed | 8 | 8 |

### Agent balance

| Agent | Total | Sale | No Sale | Follow-up Needed |
|---|---|---|---|---|
| Daniel Cohen | 6 | 2 | 2 | 2 |
| Michael Ben-David | 6 | 2 | 2 | 2 |
| Noa Friedman | 6 | 2 | 2 | 2 |
| Sarah Levi | 6 | 2 | 2 | 2 |

### Objection distribution

| Objection | Count | Expected |
|---|---|---|
| price | 5 | 5 |
| timing | 3 | 3 |
| competitor | 3 | 3 |
| authority | 3 | 3 |
| integration | 3 | 3 |
| security | 2 | 2 |
| trust | 2 | 2 |
| no_need | 2 | 2 |
| none | 1 | 1 |

---

## 6. Audio-feature consistency

`speaking_rate_wpm` was recomputed as `total transcript word count ÷ (call_duration_seconds/60)`, and `agent_talk_ratio` as `agent word count ÷ total word count`, both directly from the `transcript` column — then compared to the stored values. `silence_ratio + speech_to_non_speech_ratio` was checked for closeness to 1.0 (their definitions are complementary per dataset_design.md §11). Differences are reported as warnings, not auto-corrected — see the Warnings section below for any that exceeded tolerance (wpm ±3, ratio ±0.02, complement ±0.03).



---

## 7. Mention-count recomputation

`price_mentions_count` and `competitor_mentions_count` were recomputed independently using a documented, word-boundary keyword list (not the original ad-hoc counting method used during authoring):

- **Price keywords:** `\bprice\b, \bpricing\b, \bpriced\b, \bcost\b, \bcosts\b, \bbudget\b, \bbudgets\b, \bfee\b, \bfees\b, \bdiscount\b, \$\d`
- **Competitor keywords:** `\bcompetitor\b, \bcompetitors\b, \bRealSync\b, \bPipeFlow\b`

No mismatches found — all stored mention counts match this script's independent recomputation exactly.

---

## 8. Transcript style warnings

- **Documented exception:** ['CALL_001', 'CALL_002', 'CALL_003', 'CALL_004'] (Batch 1) contain banned template phrases from `CLAUDE.md`'s Transcript Writing Guidelines. This is expected and pre-approved — the guidelines were added *after* Batch 1 was authored and explicitly state they apply "starting from Batch 2 onward," with Batch 1 "not rewritten retroactively."
- No banned template phrases found in CALL_005–CALL_024 (Batches 2–5).
- Repeated-opener and verbal-tic frequency were checked corpus-wide; see Warnings section for specifics (e.g. "thanks for" as a literal opener, "honestly" as a filler word) — these are style signals, not rule violations, since neither is on the explicit banned-phrase list.

---

## 9. Ground Truth consistency findings

Automated heuristics checked: every transcript contains both `Agent:` and `Customer:` tags; transcript length stays in the approved 350–700 word range; `manager_notes` is never empty; `main_objection` has at least one plausibility keyword hit in the transcript (heuristic only — full semantic grounding was verified manually per-call during Phase 5B.1 authoring, documented in each batch file's Ground Truth Validation section); `sale_result`/`call_category` are not literally contradictory; `decision_maker_present=true` rows were scanned for strong authority-absent language as a contradiction heuristic; and `sale_result=Sale` was checked against `decision_maker_present` and `closing_attempt` for two specific impossible combinations.

---

## Errors

None.

## Warnings

- ⚠️ Batch 1 calls (['CALL_001', 'CALL_002', 'CALL_003', 'CALL_004']) contain banned template phrases — documented, pre-existing exception per CLAUDE.md's Transcript Writing Guidelines (guidelines apply 'starting from Batch 2 onward'; Batch 1 explicitly not rewritten retroactively).
- ⚠️ Repeated opening pattern: 20/24 calls open the agent's first line with literal 'thanks for' — not a banned template, but a corpus-wide structural repetition worth noting.
- ⚠️ Verbal tic 'honestly' appears 47 times across 21/24 calls — the most repeated filler word in the corpus.

## Fixes applied

None — no objective formatting errors (stray whitespace, boolean casing) were found; the CSV was already clean.

---

## Final readiness decision

**Status: READY WITH WARNINGS**

Zero schema, Ground Truth, corpus-math, or hard-consistency errors were found (0 errors). 3 warning(s) were surfaced — style/consistency signals (documented Batch 1 exception, mention-count methodology differences, corpus-wide opener/filler-word patterns, or minor audio-consistency drift) that do not violate any explicit rule in `dataset_design.md` or `CLAUDE.md`. The dataset is ready to freeze; the warnings are recommended reading for anyone doing further RAG-quality tuning, not blockers.
