# XSight — Historical Call Matrix (Phase 5B.0)

**Status: planning matrix only — metadata, no full transcripts, no CSV files.** This document assigns the 24 planned rows of `data/historical_sales_calls.csv` (per [docs/dataset_design.md](dataset_design.md)) to a specific agent, customer profile, outcome, objection, and contrast-case role, so that the distribution targets (§12) and required contrast cases (§13) are verifiably satisfied *before* any transcript is written or any CSV row is finalized. Transcript authoring, `manager_notes`, `agent_performance_score`, and `objection_handling_quality` are intentionally deferred to Phase 5B.1 — this matrix fixes the *shape* of the corpus first.

All taxonomy values below follow [dataset_design.md](dataset_design.md) §4–§10. `Company size` is an approximate employee count consistent with `Customer segment` (SMB ≈ 10–100, Mid-Market ≈ 100–1,000, Enterprise ≈ 1,000+), used for transcript realism in Phase 5B.1.

---

## 1. The matrix

| Call ID | Agent | Customer segment | Industry | Company size | Customer intent | Main objection | Customer sentiment | Sale result | Follow-up needed | Closing attempt | Lead quality | Decision maker present | Expected contrast case |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CALL_001 | Sarah Levi | Mid-Market | Finance | ~250 | high | trust | positive | Sale | No | strong | 5 | Yes | — |
| CALL_002 | Sarah Levi | Enterprise | Healthcare | ~1,200 | high | integration | positive | Sale | No | medium | 4 | Yes | — |
| CALL_003 | Sarah Levi | SMB | Retail | ~40 | medium | authority | neutral | No Sale | Yes | strong | 3 | No | **Case 5** — strong agent performance in a failed call (agent_performance_score to be authored high, e.g. 4–5, despite No Sale; lost only because no decision-maker was present) |
| CALL_004 | Sarah Levi | SMB | Professional Services | ~25 | low | trust | negative | No Sale | No | weak | 2 | Yes | **Case 4** — low intent ending in No Sale. **Case 8** — paired with CALL_010: same outcome (No Sale), different objection (trust vs. authority) |
| CALL_005 | Sarah Levi | Mid-Market | Manufacturing | ~300 | medium | integration | mixed | Follow-up Needed | Yes | medium | 3 | Yes | — |
| CALL_006 | Sarah Levi | Enterprise | Technology | ~2,000 | medium | security | neutral | Follow-up Needed | Yes | weak | 3 | No | — |
| CALL_007 | Daniel Cohen | Mid-Market | Retail | ~180 | high | price | positive | Sale | No | strong | 4 | Yes | **Case 1** — price objection ending in Sale. **Case 7** — paired with CALL_009: same agent, same objection, similar (high) intent, opposite outcome |
| CALL_008 | Daniel Cohen | Enterprise | Logistics | ~1,500 | high | competitor | positive | Sale | No | strong | 5 | Yes | — |
| CALL_009 | Daniel Cohen | SMB | Real Estate | ~15 | high | price | mixed | No Sale | No | strong | 4 | Yes | **Case 2** — price objection ending in No Sale. **Case 7** — paired with CALL_007 (see above); despite Daniel's price-handling strength and a strong close attempt, an internal budget cut (transcript-level detail, not visible in metadata) lost the deal |
| CALL_010 | Daniel Cohen | Mid-Market | Finance | ~220 | medium | authority | neutral | No Sale | Yes | medium | 3 | No | **Case 8** — paired with CALL_004 (see above) |
| CALL_011 | Daniel Cohen | Mid-Market | Manufacturing | ~400 | medium | timing | neutral | Follow-up Needed | Yes | medium | 3 | Yes | — |
| CALL_012 | Daniel Cohen | Enterprise | Technology | ~1,300 | medium | competitor | mixed | Follow-up Needed | Yes | strong | 4 | Yes | — |
| CALL_013 | Michael Ben-David | Enterprise | Technology | ~1,800 | high | security | positive | Sale | No | medium | 5 | Yes | — |
| CALL_014 | Michael Ben-David | Mid-Market | Healthcare | ~260 | high | timing | positive | Sale | No | weak | 5 | Yes | **Case 6** — weak agent performance in a successful call (agent_performance_score to be authored low, e.g. 1–2, despite Sale; the opportunity was already highly qualified before the conversation, allowing the deal to close despite weaker sales execution. The transcript should clearly support this outcome through strong customer buying signals rather than agent performance.) |
| CALL_015 | Michael Ben-David | Mid-Market | Retail | ~190 | high | price | mixed | No Sale | No | medium | 4 | Yes | **Case 2** — price objection ending in No Sale (primary instance) |
| CALL_016 | Michael Ben-David | SMB | Professional Services | ~30 | low | no_need | negative | No Sale | No | none | 1 | Yes | **Case 4** — low intent ending in No Sale (reinforcing instance, different objection than CALL_004) |
| CALL_017 | Michael Ben-David | Enterprise | Manufacturing | ~1,100 | medium | authority | neutral | Follow-up Needed | Yes | medium | 3 | No | Illustrates `authority` recurring in a third outcome (Follow-up Needed) alongside CALL_003 and CALL_010 (both No Sale) |
| CALL_018 | Michael Ben-David | Enterprise | Finance | ~1,600 | medium | price | mixed | Follow-up Needed | Yes | weak | 3 | No | Shows `price` spanning all three outcomes (Sale: CALL_007; No Sale: CALL_009/CALL_015; Follow-up Needed: here) |
| CALL_019 | Noa Friedman | SMB | Retail | ~60 | high | no_need | positive | Sale | No | strong | 4 | Yes | — |
| CALL_020 | Noa Friedman | Mid-Market | Logistics | ~350 | high | timing | positive | Sale | No | medium | 4 | Yes | — |
| CALL_021 | Noa Friedman | Mid-Market | Real Estate | ~150 | medium | competitor | neutral | No Sale | No | weak | 2 | Yes | — |
| CALL_022 | Noa Friedman | SMB | Professional Services | ~20 | low | integration | negative | No Sale | No | none | 1 | No | — |
| CALL_023 | Noa Friedman | Mid-Market | Healthcare | ~280 | high | price | mixed | Follow-up Needed | Yes | weak | 4 | Yes | **Case 3** — high intent ending in Follow-up Needed (Noa's weak closing follow-through leaves a well-qualified call open) |
| CALL_024 | Noa Friedman | Enterprise | Technology | ~2,200 | unclear | none | neutral | Follow-up Needed | Yes | weak | 3 | Yes | Ambiguous/exploratory call — no clear objection surfaced yet |

---

## 2. Distribution verification

### 2.1 Outcome balance (target: 8 / 8 / 8, per §12)

| Outcome | Call IDs | Count |
|---|---|---|
| `Sale` | 001, 002, 007, 008, 013, 014, 019, 020 | 8 |
| `No Sale` | 003, 004, 009, 010, 015, 016, 021, 022 | 8 |
| `Follow-up Needed` | 005, 006, 011, 012, 017, 018, 023, 024 | 8 |

**Total: 24 ✓**

### 2.2 Agent balance (target: balanced across 4 agents)

| Agent | Sale | No Sale | Follow-up Needed | Total |
|---|---|---|---|---|
| Sarah Levi | 2 | 2 | 2 | 6 |
| Daniel Cohen | 2 | 2 | 2 | 6 |
| Michael Ben-David | 2 | 2 | 2 | 6 |
| Noa Friedman | 2 | 2 | 2 | 6 |

Every agent is perfectly balanced — 6 calls each, and exactly 2 of each outcome per agent. This directly satisfies the dataset validation rule "no agent with only one outcome" ([dataset_design.md](dataset_design.md) §18) and keeps agent identity from correlating with outcome at all in the RAG corpus, consistent with §3's "no agent always succeeds or always fails."

### 2.3 Objection distribution (target: per §12)

| Objection | Target | Call IDs | Count |
|---|---|---|---|
| `price` | 5 | 007, 009, 015, 018, 023 | 5 ✓ |
| `timing` | 3 | 011, 014, 020 | 3 ✓ |
| `competitor` | 3 | 008, 012, 021 | 3 ✓ |
| `authority` | 3 | 003, 010, 017 | 3 ✓ |
| `integration` | 3 | 002, 005, 022 | 3 ✓ |
| `security` | 2 | 006, 013 | 2 ✓ |
| `trust` | 2 | 001, 004 | 2 ✓ |
| `no_need` | 2 | 016, 019 | 2 ✓ |
| `none` | 1 | 024 | 1 ✓ |

**Total: 24 ✓** — matches the planned distribution in dataset_design.md §12 exactly.

---

## 3. Contrast case coverage (target: all 8 cases from §13)

| # | Required case | Covered by |
|---|---|---|
| 1 | Price objection ending in `Sale` | CALL_007 |
| 2 | Price objection ending in `No Sale` | CALL_015 (primary), CALL_009 (secondary) |
| 3 | High intent ending in `Follow-up Needed` | CALL_023 |
| 4 | Low intent ending in `No Sale` | CALL_004 (primary), CALL_016 (secondary) |
| 5 | Strong agent performance in a failed call | CALL_003 |
| 6 | Weak agent performance in a successful call | CALL_014 |
| 7 | Highly similar calls (same agent, similar objection/intent), different outcomes | CALL_007 vs. CALL_009 (both Daniel Cohen, `price`, `high` intent) |
| 8 | Similar outcomes (both `No Sale`) caused by different objections | CALL_004 (`trust`) vs. CALL_010 (`authority`) |

All 8 required contrast cases are covered by at least one row. Note that cases 5 and 6 rely on `agent_performance_score`, which is not a column in this matrix — the matrix flags *which* rows must receive a high/low score respectively when the full row (including `agent_performance_score`, `objection_handling_quality`, and the transcript) is authored in Phase 5B.1, so the contrast survives into the final CSV.

---

## 4. Open items for Phase 5B.1

- `agent_performance_score` and `objection_handling_quality` (1–5 each) are not assigned in this matrix — they must be authored per-row alongside the transcript, respecting the Case 5/6 constraints above and the general independence rule (dataset_design.md §9).
- `manager_notes` will be written per-row once a transcript exists, so notes stay grounded per the [Ground Truth Rules](../CLAUDE.md#ground-truth-rules).
- Audio-derived fields (`silence_ratio`, `speaking_rate_wpm`, `speech_to_non_speech_ratio`, `agent_talk_ratio`, `average_energy_level`, `call_duration_seconds`) are not assigned here — they will be authored per-row in Phase 5B.1 within the realistic ranges in dataset_design.md §11, kept internally consistent with each row's transcript length and agent talk-time.
- `price_mentions_count` and `competitor_mentions_count` will be derived once each transcript is written (they must match actual keyword counts in that row's text).

This matrix is the design blueprint for the RAG corpus. Every transcript written in Phase 5B.1 must remain fully consistent with the call it corresponds to here — same agent, segment, industry, intent, objection, sentiment, outcome, closing attempt, and contrast-case role — and must satisfy the [Ground Truth Rules](../CLAUDE.md#ground-truth-rules): each field is only valid if the transcript itself actually supports it, not because the matrix planned it that way.

---

## Matrix Validation Status

✓ Outcome balance verified (8 Sale / 8 No Sale / 8 Follow-up Needed)

✓ Agent balance verified

✓ Objection distribution verified

✓ Customer segment diversity verified

✓ Industry diversity verified

✓ Customer intent diversity verified

✓ Customer sentiment diversity verified

✓ Decision-maker diversity verified

✓ Required contrast cases verified

✓ Ready for transcript generation

**No CSV files or transcripts have been generated.**