# XSight — Dataset Design (Phase 5A)

This document defines the complete data strategy for XSight's two datasets: the RAG corpus (`data/historical_sales_calls.csv`) and the PyTorch classifier training dataset (`data/call_signal_training.csv`). It covers taxonomy definitions, agent profiles, planned distributions, full column schemas, synthetic-generation rules, and validation rules. **This is a design-only document — no CSV data is generated in this phase.** Dataset generation is Phase 5B; automated and manual validation is Phase 5C.

See [CLAUDE.md §7](../CLAUDE.md#7-data-design) for the original data-design summary this document expands on, and [docs/PROGRESS.md](PROGRESS.md) for phase status.

---

## 1. Business domain and fictional product context

XSight analyzes sales calls for a **fictional B2B SaaS platform** sold to sales teams and business organizations. The product being sold in the historical calls may include:

- lead and customer management
- sales automation
- performance analytics
- CRM integrations
- AI tools for sales teams

Both datasets are built around this single fictional product so that objections, terminology, and customer concerns are internally consistent across all calls (e.g. "integration with our existing CRM" or "does this replace our current sales tooling" are recurring, plausible objections for this specific product category — not generic sales-call filler). Customers span multiple industries and company sizes (see `customer_segment` and `industry` in §14) to keep the corpus realistic without expanding the fictional product itself into multiple unrelated offerings.

---

## 2. Dataset separation rationale

`data/historical_sales_calls.csv` and `data/call_signal_training.csv` are two separate files with a shared, compatible column subset — not one file serving both purposes:

- **Different consumers.** The RAG corpus is consumed by the RAG Service (ChromaDB ingestion + retrieval + citation-based generation). The classifier dataset is consumed by the PyTorch training pipeline (feature vectors + labels only).
- **Different required content.** The RAG corpus must contain a full `transcript` per row — retrieval and grounded generation are meaningless without the actual call text to cite. The classifier dataset explicitly does not require transcripts — a feature-based classifier trains on engineered features and labels, not raw text.
- **Different scale and generation method.** The RAG corpus is small (24 rows) and each row must be individually authored and internally consistent, since every field must plausibly match a real transcript. The classifier dataset is larger (~200 rows) and generated through controlled, logically consistent variation, since a feature-based model needs enough rows per class to learn generalizable patterns, which hand-authoring full transcripts at that scale cannot support.
- **Different failure modes if merged.** If one file served both purposes, either the RAG corpus would need ~200 full transcripts (not feasible for a student-scale project, and unnecessary for retrieval quality), or the classifier would train on only 24 rows (too few for a meaningful train/validation/test split). Keeping them separate lets each dataset be sized correctly for its actual consumer.
- **Shared schema, not shared purpose.** The two files share a compatible column subset (§14 minus `transcript`, `manager_notes`, and a few RAG-only fields ≈ §15's feature columns) so feature-engineering logic — e.g. how `silence_ratio` or `agent_talk_ratio` is computed and validated — can be reused between them. This is a schema-compatibility convenience, not a reason to merge the files.

---

## 3. Historical call agents

The RAG corpus uses four fictional agents, each with a general sales style. **No agent always succeeds or always fails** — every agent appears across at least two of the three `sale_result` outcomes in the 24-call corpus. This is deliberate: if an agent's name alone predicted the outcome, the RAG service (and a human reader) could shortcut to "agent X sells / agent Y doesn't" instead of reasoning from the actual call evidence, which would undermine the grounded-retrieval design goal (§13's contrast cases exist specifically to prevent this). It also has a practical consequence for the classifier dataset: `agent_name` is deliberately **not** a column in `call_signal_training.csv` (§15), so agent identity cannot leak into the classifier at all — see §17.

| Agent | General style | Known limitation |
|---|---|---|
| **Sarah Levi** | Strong discovery and trust-building — asks good qualifying questions, builds rapport early, uncovers real customer pain points. | Sometimes under-invests in closing — a well-qualified call can still end without a clear next step. |
| **Daniel Cohen** | Strong closing and price-objection handling — direct, confident, good at reframing price pushback. | Can come across as pushy with skeptical or trust-objection customers, occasionally accelerating past unresolved concerns. |
| **Michael Ben-David** | Strong technical knowledge — thorough, accurate answers on integrations, security, and product depth. | Sometimes talks too much, reducing customer talk time and occasionally missing buying signals or objections raised in passing. |
| **Noa Friedman** | Strong communication and rapport — engaging, personable conversational style that keeps customers talking. | Sometimes weak closing follow-through — an engaged, positive call can still fail to convert to a next step. |

These are tendencies, not guarantees — the actual `sale_result`, scores, and objection per call must be authored (Phase 5B) to be independently consistent with that specific call's transcript, not auto-derived from the agent's general style.

---

## 4. Sale result labels

`sale_result` (RAG corpus) / `predicted_outcome_label` (classifier dataset) uses exactly three values:

| Label | Meaning |
|---|---|
| `Sale` | The call resulted in a closed deal or firm purchase commitment. |
| `No Sale` | The call ended with the customer declining or the opportunity being lost. |
| `Follow-up Needed` | The call ended without a final decision — more information, another call, or another stakeholder is needed before an outcome is reached. |

**Clarification:** events such as "meeting scheduled" or "escalated to manager" are **not** sale-result classes — they are captured separately via `next_meeting_scheduled` (boolean) and `call_category` (routing categories may include `Human Review Required` etc., see §10). A call can be `Follow-up Needed` with or without `next_meeting_scheduled = true`, and a call can be `Sale` even if no further meeting is scheduled (the deal is already closed).

---

## 5. Main objection taxonomy

`main_objection` uses exactly these ten values:

| Value | Meaning |
|---|---|
| `price` | Cost, budget, or pricing-model concerns. |
| `timing` | Not the right time — internal priorities, budget cycle, or timing mismatch. |
| `trust` | Skepticism about the vendor, product claims, or lack of confidence in the company. |
| `competitor` | Actively comparing to or currently using a competing product. |
| `no_need` | Customer does not see a clear need or use case for the product. |
| `authority` | The person on the call is not the decision-maker and cannot commit. |
| `integration` | Concerns about integrating with existing CRM/tools/workflows. |
| `security` | Data security, compliance, or privacy concerns. |
| `other` | A real objection that doesn't fit the other categories. |
| `none` | No meaningful objection was raised during the call. |

Every row in both datasets must have exactly one `main_objection` value (the most significant objection raised, by author/generation judgment), even if multiple objections appear in the transcript.

---

## 6. Customer intent taxonomy

`customer_intent` uses exactly these four values:

| Value | Definition |
|---|---|
| `high` | Customer shows clear, active buying signals — asks about next steps, pricing detail, implementation timeline, or explicitly states intent to move forward. |
| `medium` | Customer is engaged and asking relevant questions but has not signaled a clear intent to proceed; genuinely evaluating. |
| `low` | Customer is passive, disengaged, or gives minimal signal of interest, but the call did not end in explicit rejection. |
| `unclear` | The transcript does not give enough signal to confidently classify intent (e.g. very short call, off-topic tangents, ambiguous responses). |

---

## 7. Customer sentiment taxonomy

`customer_sentiment` uses exactly these four values:

| Value | Meaning |
|---|---|
| `positive` | Customer tone is friendly, enthusiastic, or receptive throughout most of the call. |
| `neutral` | Customer tone is even, businesslike, neither notably positive nor negative. |
| `negative` | Customer tone is frustrated, dismissive, or resistant. |
| `mixed` | Sentiment shifts meaningfully during the call (e.g. positive opening, negative turn after a pricing discussion). |

---

## 8. Closing attempt taxonomy

`closing_attempt` uses exactly these four values:

| Value | Definition |
|---|---|
| `strong` | Agent makes a direct, specific ask for commitment (e.g. proposes a start date, asks for a signature, proposes next concrete step with a timeline). |
| `medium` | Agent attempts to move the conversation forward (e.g. "should we schedule a follow-up") but without a direct or specific commitment ask. |
| `weak` | Agent gestures vaguely toward next steps ("I'll send some info over") without asking for any commitment. |
| `none` | Agent makes no discernible attempt to close or advance the conversation. |

---

## 9. Numeric score definitions

| Field | Range | Definition |
|---|---|---|
| `agent_performance_score` | 1–5 (integer) | How well the agent executed the call — discovery quality, objection handling, closing technique, communication clarity. Independent of whether the customer was a good fit. |
| `objection_handling_quality` | 1–5 (integer) | How effectively the agent addressed the specific `main_objection` raised — 1 = ignored/mishandled, 5 = fully resolved with a credible response. |
| `lead_quality_score` | 1–5 (integer) | How good a prospect the customer is, independent of how the call went — budget fit, need, authority, timing. Independent of agent performance. |

**Critical clarification — these concepts must remain separate:**

- **`Sale` does not automatically mean a high agent score.** A call can close because the lead was already highly qualified and ready to buy regardless of how the agent handled it (e.g. `agent_performance_score = 2`, `sale_result = Sale`).
- **`No Sale` does not automatically mean poor agent performance.** A call can be lost due to factors outside the agent's control — no budget this quarter, wrong buyer on the call, a genuinely bad fit — while the agent executed well (e.g. `agent_performance_score = 5`, `sale_result = No Sale`).
- **Customer fit (`lead_quality_score`) and agent performance (`agent_performance_score`) are independent axes.** A high-quality lead can be mishandled by the agent, and a low-quality lead can be professionally and correctly disqualified. Both datasets must include rows that decouple these two scores from each other and from `sale_result` — see the required contrast cases in §13.

---

## 10. Routing categories

`call_category` uses exactly these six values in the valid historical-call corpus:

- `Successful Sale`
- `Failed Sale`
- `Follow-up Needed`
- `High-Value Opportunity`
- `Coaching Required`
- `Human Review Required`

**Clarification:** `Invalid Submission` is **not** a valid `call_category` value in either dataset. It belongs to the Guardrails Service's own test data (malformed files, off-topic content, empty transcripts, etc. — see [CLAUDE.md §5](../CLAUDE.md#5-guardrails-service)), not to the valid historical-call corpus, since every row in both `data/historical_sales_calls.csv` and `data/call_signal_training.csv` represents a real, well-formed sales call that passed input validation.

---

## 11. Audio-derived feature definitions and realistic ranges

| Feature | Realistic range | Definition |
|---|---|---|
| `call_duration_seconds` | 180–900 | Total call length in seconds (3–15 minutes). |
| `silence_ratio` | 0.05–0.35 | Fraction of total call duration classified as silence/non-speech. |
| `speaking_rate_wpm` | 100–190 | Words per minute across the call (word count ÷ duration in minutes). |
| `speech_to_non_speech_ratio` | 0.65–0.95 | Fraction of the call that is active speech vs. silence/non-speech. |
| `agent_talk_ratio` | 0.35–0.75 | Agent word count ÷ total word count (requires speaker-tagged transcript). |
| `average_energy_level` | `low` / `medium` / `high` | Coarse categorical proxy for average vocal energy/volume across the call. |

**Clarifications:**

- These features **may correlate with outcomes but do not determine them alone** — e.g. a high `agent_talk_ratio` is loosely associated with Michael Ben-David's "talks too much" tendency, but must not be encoded as a deterministic rule (see §17's leakage rule).
- A feature that is unmeasured or uncomputable for a given row **must be marked missing** (empty value / explicit `unknown`), **never silently fabricated or defaulted** — this applies to both datasets, consistent with [CLAUDE.md's Call Signal Analyser rules](../CLAUDE.md#4-voice--call-signal-analyser) (e.g. `silence_ratio` must never default to `0.0`).
- Where a synthetic row does specify a measured value for these fields, that value must stay within the realistic range above and remain logically consistent with the row's other fields (e.g. a `call_duration_seconds` of 850 paired with a `word_count` implying a `speaking_rate_wpm` outside 100–190 is inconsistent and invalid — see §18).

---

## 12. Planned distribution for 24 RAG calls

**By outcome (`sale_result`):**

| Outcome | Count |
|---|---|
| `Sale` | 8 |
| `No Sale` | 8 |
| `Follow-up Needed` | 8 |
| **Total** | **24** |

**By main objection (`main_objection`):**

| Objection | Count |
|---|---|
| `price` | 5 |
| `timing` | 3 |
| `competitor` | 3 |
| `authority` | 3 |
| `integration` | 3 |
| `security` | 2 |
| `trust` | 2 |
| `no_need` | 2 |
| `none` | 1 |
| **Total** | **24** |

Both totals sum to 24, consistent with the planned corpus size. `other` is intentionally unused in the planned distribution (reserved for an edge case if authoring in Phase 5B surfaces a genuine objection that doesn't fit the nine categories above) — if unused, the taxonomy value remains valid for future/live calls even if no historical row uses it.

---

## 13. Required contrast cases for RAG quality

To make retrieval and citation-based generation meaningful (rather than trivially separable by outcome or agent), the 24-call corpus must include at least one instance of each of the following contrast pairs/cases:

1. **Price objection ending in `Sale`** — price was raised and successfully overcome.
2. **Price objection ending in `No Sale`** — price was raised and was the deciding factor in losing the deal.
3. **High intent ending in `Follow-up Needed`** — a clearly interested customer whose deal still didn't close in-call (e.g. needs another stakeholder).
4. **Low intent ending in `No Sale`** — a genuinely poor-fit or disengaged lead where the outcome matches expectation.
5. **Strong agent performance in a failed call** — `agent_performance_score` ≥ 4 with `sale_result = No Sale`, to decouple performance from outcome (§9).
6. **Weak agent performance in a successful call** — `agent_performance_score` ≤ 2 with `sale_result = Sale`, same purpose.
7. **Highly similar calls with different outcomes** — two calls with the same agent, similar objection and intent, but different `sale_result`, so the RAG service must ground its similarity reasoning in transcript detail rather than superficial metadata match.
8. **Similar outcomes caused by different objections** — e.g. two `No Sale` calls, one driven by `trust` and one by `authority`, so outcome alone doesn't collapse into one retrievable pattern.

These cases are a **minimum requirement**, not an exhaustive list — Phase 5B authoring should satisfy all eight while still meeting the distribution targets in §12.

---

## 14. Final schema for `data/historical_sales_calls.csv`

26 columns. `call_id` is unique per row; `transcript` is required and must be a full, plausible call transcript consistent with every other field in the row.

| Column | Type | Allowed values / range | Required | Description | Example |
|---|---|---|---|---|---|
| `call_id` | string | Unique, format `CALL_0NN` | Yes | Unique identifier for the historical call, used as the citation key by the RAG Service. | `CALL_014` |
| `agent_name` | string | One of the four agents (§3) | Yes | The sales agent on the call. | `Daniel Cohen` |
| `customer_segment` | string | `SMB`, `Mid-Market`, `Enterprise` | Yes | Size/segment of the customer organization. | `Mid-Market` |
| `industry` | string | e.g. `Retail`, `Finance`, `Healthcare`, `Manufacturing`, `Technology`, `Real Estate`, `Logistics`, `Professional Services` | Yes | Customer's industry vertical. | `Retail` |
| `transcript` | string | Full text, speaker-tagged (`Agent:`/`Customer:`) | Yes | Complete call transcript; the primary retrieval and citation content. | `"Agent: Thanks for taking the call today...`" |
| `call_duration_seconds` | integer | 180–900 | Yes | Total call duration in seconds. | `420` |
| `sale_result` | enum | `Sale`, `No Sale`, `Follow-up Needed` | Yes | Final outcome of the call (§4). | `No Sale` |
| `customer_intent` | enum | `high`, `medium`, `low`, `unclear` | Yes | Customer buying-intent level (§6). | `high` |
| `main_objection` | enum | 10-value taxonomy (§5) | Yes | Primary objection raised in the call. | `price` |
| `customer_sentiment` | enum | `positive`, `neutral`, `negative`, `mixed` | Yes | Overall customer tone (§7). | `mixed` |
| `agent_performance_score` | integer | 1–5 | Yes | Agent execution quality, independent of outcome (§9). | `3` |
| `objection_handling_quality` | integer | 1–5 | Yes | How well the agent addressed `main_objection` (§9). | `4` |
| `closing_attempt` | enum | `strong`, `medium`, `weak`, `none` | Yes | Strength of the agent's closing attempt (§8). | `medium` |
| `follow_up_needed` | boolean | `true` / `false` | Yes | Whether a follow-up action is required after this call. | `true` |
| `lead_quality_score` | integer | 1–5 | Yes | Prospect fit quality, independent of agent performance (§9). | `4` |
| `call_category` | enum | 6-value routing taxonomy (§10) | Yes | Routing category assigned to this call. | `Coaching Required` |
| `next_meeting_scheduled` | boolean | `true` / `false` | Yes | Whether a concrete next meeting was scheduled during the call. | `false` |
| `decision_maker_present` | boolean | `true` / `false` | Yes | Whether the person on the call has purchase authority. | `true` |
| `silence_ratio` | float | 0.05–0.35, or missing | Yes (or explicit missing) | Fraction of the call classified as silence (§11). | `0.14` |
| `speaking_rate_wpm` | integer | 100–190, or missing | Yes (or explicit missing) | Words per minute across the call. | `142` |
| `speech_to_non_speech_ratio` | float | 0.65–0.95, or missing | Yes (or explicit missing) | Fraction of the call that is active speech. | `0.88` |
| `agent_talk_ratio` | float | 0.35–0.75, or missing | Yes (or explicit missing) | Agent word count ÷ total word count. | `0.58` |
| `average_energy_level` | enum | `low`, `medium`, `high`, or missing | No | Coarse vocal energy proxy (§11). | `medium` |
| `price_mentions_count` | integer | ≥ 0 | Yes | Count of price/cost/budget keyword mentions in the transcript. | `3` |
| `competitor_mentions_count` | integer | ≥ 0 | Yes | Count of competitor-name/product mentions in the transcript. | `1` |
| `manager_notes` | string | Free text, or empty | No | Optional human-style annotation grounded in the transcript (e.g. coaching context). | `"Good discovery, missed the trial close after price pushback."` |

---

## 15. Final schema for `data/call_signal_training.csv`

20 columns, no `transcript` and no `agent_name` (see §3, §17 for the identity-leakage rationale). 16 feature columns, 4 target columns.

| Column | Type | Allowed values / range | Feature or target | Description | Example |
|---|---|---|---|---|---|
| `record_id` | string | Unique, format `REC_0NNN` | — (identifier) | Unique row identifier for the training dataset. | `REC_0142` |
| `call_duration_seconds` | integer | 180–900 | Feature | Total call duration in seconds. | `510` |
| `silence_ratio` | float | 0.05–0.35, or missing | Feature | Fraction of the call classified as silence. | `0.11` |
| `speaking_rate_wpm` | integer | 100–190, or missing | Feature | Words per minute across the call. | `156` |
| `speech_to_non_speech_ratio` | float | 0.65–0.95, or missing | Feature | Fraction of the call that is active speech. | `0.91` |
| `agent_talk_ratio` | float | 0.35–0.75, or missing | Feature | Agent word count ÷ total word count. | `0.63` |
| `average_energy_level` | enum | `low`, `medium`, `high`, or missing | Feature | Coarse vocal energy proxy. | `high` |
| `word_count` | integer | ≥ 0 | Feature | Total word count across the transcript. | `1180` |
| `question_count` | integer | ≥ 0 | Feature | Total question count across the transcript. | `14` |
| `price_mentions_count` | integer | ≥ 0 | Feature | Count of price/cost/budget keyword mentions. | `2` |
| `competitor_mentions_count` | integer | ≥ 0 | Feature | Count of competitor-name/product mentions. | `0` |
| `customer_intent` | enum | `high`, `medium`, `low`, `unclear` | Feature | Customer buying-intent level (§6), sourced from Gemini's extraction upstream. | `medium` |
| `main_objection` | enum | 10-value taxonomy (§5) | Feature | Primary objection raised. | `integration` |
| `customer_sentiment` | enum | `positive`, `neutral`, `negative`, `mixed` | Feature | Overall customer tone (§7). | `neutral` |
| `closing_attempt` | enum | `strong`, `medium`, `weak`, `none` | Feature | Strength of the agent's closing attempt (§8). | `weak` |
| `decision_maker_present` | boolean | `true` / `false` | Feature | Whether the person on the call has purchase authority. | `false` |
| `lead_quality_score` | integer | 1–5 | Target | Prospect fit quality (§9, §16). | `3` |
| `agent_performance_score` | integer | 1–5 | Target | Agent execution quality (§9, §16). | `4` |
| `risk_level` | enum | `Low`, `Medium`, `High` | Target | Deal-risk classification (§16). | `Medium` |
| `predicted_outcome_label` | enum | `Sale`, `No Sale`, `Follow-up Needed` | Target | Ground-truth outcome label for training (§4, §16). | `Follow-up Needed` |

---

## 16. Classifier targets

The Call Signal Analyser's PyTorch classifier is trained to predict four targets from the 16 feature columns in §15:

- **`predicted_outcome_label`** — one of `Sale` / `No Sale` / `Follow-up Needed` (§4); the primary classification target.
- **`risk_level`** — one of `Low` / `Medium` / `High`; a coarse deal-risk signal derived from the combination of intent, objection severity, closing strength, and engagement features, not from outcome alone.
- **`lead_quality_score`** — 1–5 (§9); prospect fit, predicted independently of agent performance.
- **`agent_performance_score`** — 1–5 (§9); agent execution quality, predicted independently of lead quality.

Consistent with [CLAUDE.md §4](../CLAUDE.md#4-voice--call-signal-analyser), the trained model also produces a `confidence` value at inference time (not a column in the training data itself — it is a property of the model's prediction, not a ground-truth label) and falls back to `"Uncertain"` / human review when confidence is below 0.65.

---

## 17. Synthetic data generation rules

Applies to `data/call_signal_training.csv` generation (Phase 5B):

- **Controlled variation, not random independent values.** Rows are generated by varying a base set of realistic call profiles along plausible dimensions (e.g. shift intent down, adjust closing attempt accordingly, adjust risk level accordingly) — not by sampling every column independently, which would produce logically incoherent rows.
- **Labels must remain logically consistent with features.** E.g. a row with `customer_intent = high`, `closing_attempt = strong`, and `decision_maker_present = true` should skew toward `predicted_outcome_label = Sale` far more often than not — but not deterministically (see below).
- **No exact duplicate rows.** Every row must be distinguishable by at least one feature value.
- **No near-duplicate row leakage across train/validation/test.** Rows generated as controlled variations of the same base profile must be kept together in the same split (§19) — near-identical rows must never straddle train and test.
- **No single feature should deterministically reveal the target.** E.g. `closing_attempt = strong` must not appear in 100% of `Sale` rows and 0% of `No Sale` rows — realistic overlap must exist (some strong-closing calls still lose, per §9's independence rule; some weak-closing calls still convert).
- **No agent identity leakage.** `agent_name` is not a column in this dataset at all (§15) — this is a structural guarantee, not just a generation guideline, since the classifier must learn from call signals, not from which of the four fictional agents ran the call.
- **Balanced enough target classes for student-scale training.** No target class should be so rare that a train/validation/test split (§19) leaves it with too few examples to evaluate meaningfully — exact balance is not required, but severe skew (e.g. one outcome at 5% of rows) should be avoided.
- **Realistic noise and overlap between classes.** Feature distributions for different outcomes should overlap somewhat (as real sales signals do), rather than being cleanly separable — an easy synthetic dataset would not exercise the classifier or its confidence-thresholding behavior meaningfully.

---

## 18. Dataset validation rules

Applies to both datasets, verified in Phase 5C (automated where possible, manual spot-check otherwise):

- **Unique IDs** — `call_id` (RAG corpus) and `record_id` (classifier dataset) must be unique within their file.
- **Required fields present** — every column marked "Required: Yes" in §14 / every feature+target column in §15 must be populated (or explicitly marked missing where §11/§14 allow it).
- **Valid enums** — every enum-typed column must use only its defined taxonomy values (§4–§10); no free-text substitutes.
- **Numeric scores within range** — `agent_performance_score`, `objection_handling_quality`, `lead_quality_score` must be integers 1–5.
- **Ratios between 0 and 1** — `silence_ratio`, `speech_to_non_speech_ratio`, `agent_talk_ratio` must fall within their defined realistic ranges (§11) when present, and never outside [0, 1] structurally.
- **Non-negative counts** — `price_mentions_count`, `competitor_mentions_count`, `word_count`, `question_count` must be ≥ 0 integers.
- **Transcript consistent with objection, sentiment, intent, and result** (RAG corpus only) — a spot-check that the authored transcript actually supports its row's `main_objection`, `customer_sentiment`, `customer_intent`, and `sale_result` values; no row should assign labels contradicted by its own transcript text.
- **Manager notes grounded in transcript** (RAG corpus only, where present) — `manager_notes` must reference something actually present in the transcript, not invented detail.
- **No identical transcripts** — every `transcript` in the RAG corpus must be unique text, not a copy with only metadata changed.
- **No agent with only one outcome** — every agent in the RAG corpus must appear in at least two distinct `sale_result` values across their calls (§3).
- **No invalid citation IDs** — any `call_id` referenced elsewhere (e.g. in future RAG service testing or `manager_notes` cross-references) must exist in `data/historical_sales_calls.csv`.
- **No target leakage** (classifier dataset) — no feature column should be a disguised copy or trivial transform of a target column.
- **Train/validation/test split checks** (classifier dataset) — split assignment respects §19's grouping rule, and class distribution per split is checked for reasonable balance (§17).

---

## 19. Proposed train/validation/test split for classifier data

| Split | Proportion | Approx. rows (of ~200) |
|---|---|---|
| Train | 70% | ~140 |
| Validation | 15% | ~30 |
| Test | 15% | ~30 |

**Leakage-prevention rule:** related synthetic variations — rows generated as controlled variations of the same base call profile (§17) — must be assigned to the **same split group** as a unit, not distributed individually across train/validation/test. Splitting near-identical rows across groups would let the model "see" a near-duplicate of a test row during training, inflating validation/test performance without reflecting real generalization. Split assignment therefore happens at the base-profile level first, then all of that profile's generated variations inherit the same split.

---

## 20. Phase 5B and 5C plan

**Phase 5B — Dataset Generation:**
- Author the 24 full historical call transcripts and their complete metadata rows, satisfying the distribution (§12) and contrast-case requirements (§13).
- Generate the ~200 classifier training rows via controlled variation from a smaller set of base profiles, per the generation rules in §17.
- Produce both files matching the schemas in §14 and §15 exactly.

**Phase 5C — Dataset Validation:**
- Run automated validation against the rules in §18 (uniqueness, required fields, enum values, numeric ranges, ratio bounds, non-negative counts, no exact duplicates, split-group integrity).
- Manually spot-check a sample of RAG corpus rows for transcript/label consistency and grounded `manager_notes`.
- Produce summary statistics and distribution checks: outcome/objection/agent distributions for the RAG corpus, target class balance and feature distributions per split for the classifier dataset — confirming the plans in §12 and §19 were actually achieved, not just intended.

Both sub-phases require explicit user approval before proceeding, per the project's phase-by-phase working convention.