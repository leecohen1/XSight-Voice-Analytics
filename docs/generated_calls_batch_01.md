# XSight — Generated Historical Calls, Batch 1 (Phase 5B.1)

**Status: draft transcripts and full row content for CALL_001–CALL_004 only. No CSV files generated in this sub-phase.** This document authors the full historical-call record — metadata, transcript, structured fields, and audio-derived features — for the first four rows of `data/historical_sales_calls.csv`, strictly following the frozen assignments in [docs/historical_call_matrix.md](historical_call_matrix.md) and the schema in [docs/dataset_design.md](dataset_design.md) §14. Nothing in the matrix (agent, segment, industry, intent, objection, sentiment, outcome, closing attempt, lead quality, decision-maker presence, or contrast-case role) was changed — only the fields the matrix explicitly deferred to this sub-phase were authored: the transcript itself, `agent_performance_score`, `objection_handling_quality`, `call_category`, `next_meeting_scheduled`, the audio-derived features, `price_mentions_count`, `competitor_mentions_count`, and `manager_notes`.

Word counts, turn counts, speaker-word splits, and keyword counts below were verified against the actual transcript text (not estimated), so `speaking_rate_wpm`, `agent_talk_ratio`, `price_mentions_count`, and `competitor_mentions_count` are internally consistent with each transcript per the [Ground Truth Rules](../CLAUDE.md#ground-truth-rules) and [dataset_design.md](dataset_design.md) §11.

---

## CALL_001

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_001 |
| `agent_name` | Sarah Levi |
| `customer_segment` | Mid-Market |
| `industry` | Finance |
| `company_size` | ~250 |
| `sale_result` | Sale |
| `customer_intent` | high |
| `main_objection` | trust |
| `customer_sentiment` | positive |
| `follow_up_needed` | false |
| `closing_attempt` | strong |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Ronit Aviram, VP Finance Operations at a mid-market asset management firm.

> **Agent:** Hi Ronit, thanks for making time today. I know finance teams are slammed this time of quarter, so I'll keep us focused. Can you tell me a bit about how your team currently tracks the sales pipeline?
>
> **Customer:** Sure. Honestly, we're doing it in shared spreadsheets right now. Every rep updates their own tab, and I spend half my week reconciling numbers before our forecast call. I'll be honest, I've sat through pitches like this before and the tool never lived up to what was promised.
>
> **Agent:** That's fair, and I'd rather earn that trust than ask you to take my word for it. Before we get into the platform, can I ask what specifically fell apart with the last vendor?
>
> **Customer:** The integration with our accounting system was supposed to be automatic. It wasn't. We ended up with duplicate records for three months, and nobody on their side owned the fix.
>
> **Agent:** That's exactly the kind of thing I want to be upfront about instead of glossing over. Our CRM integration is a native connector we maintain ourselves, not a custom build handed to a partner. How many people would actually be using this day to day?
>
> **Customer:** About eighteen reps, plus myself and two analysts who pull reporting for the leadership team.
>
> **Agent:** With a team that size, the analytics dashboard should save your analysts real time, since pipeline data updates automatically instead of being pulled together by hand every week.
>
> **Customer:** That's the pitch every vendor gives me. What happens when it breaks two months in, the way it did last time?
>
> **Agent:** Two things, specifically because of what you described. First, every account gets a named onboarding contact for the first ninety days, not a support ticket queue. Second, we can start with a thirty-day pilot on a subset of your team before any full commitment, so the integration is proven before you're locked into anything.
>
> **Customer:** Given our industry, I also need to know how data security is handled. That's a hard requirement for us, not a nice-to-have.
>
> **Agent:** Understood. We're SOC 2 Type II certified, and all financial data is encrypted both in transit and at rest. I can send the compliance documentation directly to your security team before you sign anything.
>
> **Customer:** Okay, that's more thorough than I expected. What does pricing look like for a team our size?
>
> **Agent:** For eighteen seats it lands in our mid-market pricing tier, and I'll send the exact breakdown after this call. Given the trust issue you ran into last time, I'd also suggest a contract with a sixty-day opt-out clause, so you're not stuck if the integration underperforms.
>
> **Customer:** I'd still want to speak with a reference customer in finance before committing to anything.
>
> **Agent:** Completely reasonable. I can connect you with our contact at a mid-market asset management firm running a similar setup, and another finance team close to your size — both went through this same pilot structure.
>
> **Customer:** That actually helps. I'm feeling more comfortable than I expected going into this call.
>
> **Agent:** One more practical question — how much historical pipeline data would you want migrated out of the spreadsheets?
>
> **Customer:** At minimum the current quarter, since we're mid-forecast. Ideally the last two quarters for trend reporting.
>
> **Agent:** That's within scope for the pilot. Our onboarding team handles the migration directly, so it wouldn't fall on your analysts to re-enter anything.
>
> **Customer:** That's good to hear. I was worried this would create more work before it saved any.
>
> **Agent:** I appreciate you being direct about the history today — it made this a far more useful conversation than a standard pitch. Given where we've landed, can we get the pilot agreement signed this week so onboarding starts before your next forecast cycle?
>
> **Customer:** Yes, let's do that. Send over the pilot agreement, the compliance documentation, and the reference contacts today.
>
> **Agent:** I'll have all three in your inbox by end of day. Thanks again, Ronit.
>
> **Customer:** Thanks, Sarah. Talk soon.

Turns: 24 (12 Agent / 12 Customer). Word count: 667 (Agent 420 / Customer 247).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 320 |
| `agent_performance_score` | 5 |
| `objection_handling_quality` | 5 |
| `lead_quality_score` | 5 |
| `call_category` | Successful Sale |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.16 |
| `speaking_rate_wpm` | 125 |
| `speech_to_non_speech_ratio` | 0.84 |
| `agent_talk_ratio` | 0.63 |
| `average_energy_level` | medium |
| `price_mentions_count` | 2 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer initially skeptical due to a prior vendor's failed accounting-system integration; addressed directly with SOC 2 Type II detail, a 30-day pilot, and a 60-day opt-out clause. Closed with a pilot agreement to be signed this week. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (high) — asks about pricing, migration scope, and asks to sign the pilot agreement this week.
- ✓ transcript supports `main_objection` (trust) — explicit history of a failed prior vendor integration and repeated "what happens when it breaks" pushback.
- ✓ transcript supports `customer_sentiment` (positive) — ends "feeling more comfortable than I expected" and agrees to move forward.
- ✓ transcript supports `sale_result` (Sale) — explicit agreement to sign the pilot agreement this week.
- ✓ transcript supports `follow_up_needed` (false) — the call ends with a concrete signed commitment and document delivery, not an open question.
- ✓ transcript supports `closing_attempt` (strong) — direct ask: "can we get the pilot agreement signed this week."
- ✓ `manager_notes` grounded — every detail (accounting-system integration failure, SOC 2 Type II, 30-day pilot, 60-day opt-out, pilot agreement this week) is stated in the transcript; no invented facts.
- ✓ audio features realistic — 320s duration, 125 wpm, and 0.63 agent talk ratio are internally consistent with the 667-word, agent-heavy (420/667) transcript.
- ✓ no Ground Truth violations.

---

## CALL_002

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_002 |
| `agent_name` | Sarah Levi |
| `customer_segment` | Enterprise |
| `industry` | Healthcare |
| `company_size` | ~1,200 |
| `sale_result` | Sale |
| `customer_intent` | high |
| `main_objection` | integration |
| `customer_sentiment` | positive |
| `follow_up_needed` | false |
| `closing_attempt` | medium |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Avi Katz, Director of Sales Operations at a multi-region healthcare provider network.

> **Agent:** Hi Avi, thanks for joining. I understand you're evaluating tools to support your regional sales team's pipeline visibility — can you walk me through what's driving that right now?
>
> **Customer:** We've grown from three regions to seven in the last two years, and our director-level visibility into deal status is basically nonexistent. Everyone reports differently.
>
> **Agent:** That's a common growing pain at your scale. Before I go further, I want to understand your current stack — what CRM and reporting tools are you running today?
>
> **Customer:** We're on a legacy CRM that's been customized heavily over the years, plus a separate business intelligence tool for reporting. Nothing talks to anything else cleanly.
>
> **Agent:** That heavy customization is actually the piece I want to flag early, because it's usually the real integration risk, not the CRM vendor itself. Can you tell me more about what's been customized?
>
> **Customer:** Custom fields for our compliance workflows, mostly — we're healthcare, so every deal has to track consent and data-handling requirements alongside the normal sales fields.
>
> **Agent:** Got it. Our platform connects through a standard API layer, but with heavily customized instances we typically start with a technical discovery call before quoting a timeline, rather than promising a date up front.
>
> **Customer:** That's actually reassuring — the last vendor promised a six-week integration and it took five months.
>
> **Agent:** I'd rather under-promise here given what you've described. Realistically, for a compliance-customized instance at your scale, I'd expect eight to twelve weeks, with a technical scoping session in the first two weeks to confirm that number.
>
> **Customer:** That's a more honest estimate than I've gotten elsewhere. How does the platform handle the compliance fields specifically?
>
> **Agent:** We can map custom fields during the technical discovery phase, and anything that can't map cleanly gets flagged rather than silently dropped, so your compliance team isn't caught off guard mid-rollout.
>
> **Customer:** Good. Who internally would need to be involved on our side for that scoping call?
>
> **Agent:** Typically someone from your CRM administration team and whoever owns the compliance field structure — sounds like that might be you plus one other person.
>
> **Customer:** That would be me and our compliance lead, yes.
>
> **Agent:** And just to confirm, would you be the one signing off on this if the scoping call goes well, or does that go to someone else?
>
> **Customer:** I have budget authority up to this tier already approved by our VP of Sales Ops, so I can move forward once we're confident in the technical fit.
>
> **Agent:** Good to know, that'll help me structure the proposal to move quickly once scoping wraps. What would the rollout look like across all seven regions once scoping is done?
>
> **Customer:** We'd want a phased rollout — two regions first as a pilot, validate the integration holds up with real deal data, then expand to the remaining five. That matches how we'd want to approach it internally anyway, so that's an easy yes from my side.
>
> **Agent:** Good to hear. Given the technical dependency here, I don't want to push for a signature today — I'd rather schedule the technical discovery call this week and let that shape the actual proposal.
>
> **Customer:** I appreciate that you're not trying to rush it given the complexity. Let's get that scoping call on the calendar — and assuming it confirms what we've discussed, consider this a yes on our end. I'll get the purchase order moving internally in parallel so we're not waiting on procurement once scoping wraps.
>
> **Agent:** One last question — is there a deadline driving this, like a renewal cycle or a budget window?
>
> **Customer:** We'd want this live before our Q3 planning cycle starts, so ideally scoping and rollout wrap inside the next quarter.
>
> **Agent:** That timeline works with the estimate I gave you. I'll send scheduling options today, along with a summary of what we covered so your compliance lead has context before the call.
>
> **Customer:** Sounds good. Looking forward to it.

Turns: 24 (12 Agent / 12 Customer). Word count: 656 (Agent 362 / Customer 294).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 300 |
| `agent_performance_score` | 4 |
| `objection_handling_quality` | 5 |
| `lead_quality_score` | 4 |
| `call_category` | High-Value Opportunity |
| `next_meeting_scheduled` | true |
| `silence_ratio` | 0.14 |
| `speaking_rate_wpm` | 131 |
| `speech_to_non_speech_ratio` | 0.86 |
| `agent_talk_ratio` | 0.55 |
| `average_energy_level` | medium |
| `price_mentions_count` | 2 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Enterprise healthcare account with heavy CRM customization for compliance fields. Agent gave an honest 8–12 week integration estimate instead of over-promising, which resolved the customer's integration concern. Firm verbal commitment obtained, pending a technical scoping call this week; purchase order to move in parallel. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (high) — customer volunteers budget authority, a firm "yes," and a Q3 deadline unprompted.
- ✓ transcript supports `main_objection` (integration) — the entire call centers on heavily customized CRM fields and a prior vendor's failed integration timeline.
- ✓ transcript supports `customer_sentiment` (positive) — "that's actually reassuring," "more honest estimate than I've gotten elsewhere," "easy yes."
- ✓ transcript supports `sale_result` (Sale) — explicit firm commitment: "consider this a yes... I'll get the purchase order moving internally."
- ✓ transcript supports `follow_up_needed` (false) — the sale decision itself is closed; the remaining scoping call is an implementation step, not an open sales question.
- ✓ transcript supports `closing_attempt` (medium) — agent explicitly avoids pushing for a signature today and instead moves the conversation forward by scheduling the scoping call.
- ✓ `manager_notes` grounded — 8–12 week estimate, compliance field mapping, scoping call, and PO detail are all stated in the transcript.
- ✓ audio features realistic — 300s duration, 131 wpm, 0.55 agent talk ratio consistent with a more customer-talkative (294/656 words), collaborative discovery call.
- ✓ no Ground Truth violations.

---

## CALL_003 — Contrast Case 5

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_003 |
| `agent_name` | Sarah Levi |
| `customer_segment` | SMB |
| `industry` | Retail |
| `company_size` | ~40 |
| `sale_result` | No Sale |
| `customer_intent` | medium |
| `main_objection` | authority |
| `customer_sentiment` | neutral |
| `follow_up_needed` | true |
| `closing_attempt` | strong |
| `decision_maker_present` | false |

### 2. Transcript

Customer: Yossi Peretz, Operations Manager at a two-location retail chain.

> **Agent:** Hi Yossi, thanks for hopping on. Tell me about how deals move through your store operations right now — are you tracking leads and customer follow-ups in a structured way, or more ad hoc?
>
> **Customer:** Pretty ad hoc, honestly. We jot down customer info in a notebook near the register and follow up when someone remembers to.
>
> **Agent:** That's a common starting point for a shop your size. How many locations are we talking about?
>
> **Customer:** Two locations, about forty employees between them.
>
> **Agent:** Got it. What's prompting you to look at something more structured now?
>
> **Customer:** We're losing repeat customers we should be following up with — trade-in offers, restock notifications, that kind of thing. It's costing us sales we should be closing easily.
>
> **Agent:** That's a strong reason to fix this now rather than later. If I showed you how the platform could automate those trade-in and restock follow-ups without extra work for your staff, would that solve the core problem you just described?
>
> **Customer:** It would, yeah. That's exactly the gap.
>
> **Agent:** Good. Can I ask — for a decision like this, who typically signs off on new tools for the business?
>
> **Customer:** That would be Dana, she owns both locations. I run day-to-day operations, but purchasing decisions go through her.
>
> **Agent:** Understood. Is Dana someone I could get fifteen minutes with directly, even briefly, so she hears this from the source rather than secondhand?
>
> **Customer:** She's pretty hands-off with software decisions — she usually just asks me if it's worth it and goes with my read.
>
> **Agent:** That's helpful to know. In that case, let's make sure what I send her is something she can approve quickly. Can we walk through pricing and the specific features that solve the follow-up problem, so you have everything you need to make the case?
>
> **Customer:** Sure, that would help.
>
> **Agent:** For two locations and around forty staff, most of whom won't need seats, you'd likely need six to eight licenses for the staff actually managing customer relationships. I'll put together a one-page summary with pricing and the trade-in automation feature specifically, since that's the clearest win for Dana.
>
> **Customer:** That's useful. I think that's the kind of thing she'd actually read.
>
> **Agent:** Given the impact you described, I'd like to propose we get this in front of Dana this week rather than letting it sit — can you get fifteen minutes with her by Friday, even if I'm not on that call?
>
> **Customer:** I can try. She's usually reachable, just busy.
>
> **Agent:** I'll send the one-pager today so you have it before you talk to her, and I'll follow up with you directly on Monday to see how that conversation went.
>
> **Customer:** That works. I do want this, for what it's worth — I just can't sign off on it myself.
>
> **Agent:** I appreciate you being upfront about that from the start — it saves us both time. Let's plan on Monday.
>
> **Customer:** Sounds good, talk then.

Turns: 22 (11 Agent / 11 Customer). Word count: 492 (Agent 334 / Customer 158).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 240 |
| `agent_performance_score` | 5 |
| `objection_handling_quality` | 4 |
| `lead_quality_score` | 3 |
| `call_category` | Follow-up Needed |
| `next_meeting_scheduled` | true |
| `silence_ratio` | 0.13 |
| `speaking_rate_wpm` | 123 |
| `speech_to_non_speech_ratio` | 0.87 |
| `agent_talk_ratio` | 0.68 |
| `average_energy_level` | medium |
| `price_mentions_count` | 3 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Strong discovery and a tailored one-page proposal built specifically for the actual decision-maker, but the contact on the call — Dana, the owner — was not present and does not typically join these calls directly. Deal did not close due to the authority gap, not agent execution; a direct follow-up with Yossi is planned for Monday. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (medium) — engaged, confirms the gap the product solves, wants to make the case internally, but never signals personal buying intent since he can't buy.
- ✓ transcript supports `main_objection` (authority) — "purchasing decisions go through her," "she's pretty hands-off," "I just can't sign off on it myself."
- ✓ transcript supports `customer_sentiment` (neutral) — professional and cooperative throughout, without strong positive or negative tone shifts.
- ✓ transcript supports `sale_result` (No Sale) — no commitment obtained in this call; the actual decision sits with Dana, unresolved.
- ✓ transcript supports `follow_up_needed` (true) — explicit Monday follow-up planned to check on the Dana conversation.
- ✓ transcript supports `closing_attempt` (strong) — direct, specific ask: "can you get fifteen minutes with her by Friday," with a concrete Monday follow-up commitment.
- ✓ `manager_notes` grounded — Dana's ownership, hands-off pattern, one-pager, and Monday follow-up are all stated in the transcript; no invented budget or date beyond what's said.
- ✓ audio features realistic — 240s duration, 123 wpm, and a higher 0.68 agent talk ratio consistent with the agent-led (334/492 words) discovery-and-proposal structure of this call.
- ✓ no Ground Truth violations. **Contrast Case 5 verified:** `agent_performance_score = 5` with `sale_result = No Sale` — the transcript shows excellent discovery, a correctly diagnosed objection, a tailored proposal, and a concrete next step, with the loss attributable solely to the missing decision-maker, not agent execution.

---

## CALL_004 — Contrast Case 4

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_004 |
| `agent_name` | Sarah Levi |
| `customer_segment` | SMB |
| `industry` | Professional Services |
| `company_size` | ~25 |
| `sale_result` | No Sale |
| `customer_intent` | low |
| `main_objection` | trust |
| `customer_sentiment` | negative |
| `follow_up_needed` | false |
| `closing_attempt` | weak |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Michal Regev, Managing Partner at a small referral-based consulting firm.

> **Agent:** Hi Michal, thanks for taking a few minutes. I know consulting firms your size often manage client pipeline informally — can you tell me how your team currently tracks new business opportunities?
>
> **Customer:** We use a shared inbox and a notes doc. It's fine, honestly not sure why we're doing this call.
>
> **Agent:** I appreciate you making time anyway. Is tracking follow-ups or converting new inquiries something that's been a pain point recently?
>
> **Customer:** Not really. We're referral-based, most clients come through word of mouth. I don't think a sales tool changes much for us.
>
> **Agent:** That makes sense for a firm your size. Even referral-based, some teams find value in tracking response times. Has that slipped at all?
>
> **Customer:** Maybe sometimes. Look, I get a lot of these calls. Every vendor says their tool will fix things and half the time it just sits there unused after the trial ends.
>
> **Agent:** That's a fair concern, and I'd rather you say that now than find out three months in. What made past tools sit unused — was it the tool, or that it didn't match how the team works?
>
> **Customer:** Mostly nobody had time to learn something new for what we already manage fine with a notes doc.
>
> **Agent:** Understood. If it helps, I could show you just the parts that require the least change to your existing process, rather than the full platform.
>
> **Customer:** You can send something over. I'm not going to promise I'll look at it closely.
>
> **Agent:** That's fair. Can I ask what would actually change your mind about trying something like this?
>
> **Customer:** Honestly, probably nothing right now. We're not in growth mode this year, so it's not a priority.
>
> **Agent:** That's helpful context, thank you. Is there anyone else on the team who's felt the referral-tracking gap more than you have?
>
> **Customer:** Not that I'm aware of. We're small, everyone just handles their own clients.
>
> **Agent:** Understood. Would it be worth a short follow-up in six months if your priorities shift, or would you rather I not reach back out?
>
> **Customer:** You can check in eventually. I just don't want a bunch of emails between now and then.
>
> **Agent:** Noted, I'll keep it to a single check-in. I'll send a short overview today rather than a long deck, given everything you've said.
>
> **Customer:** Sure, that's fine.
>
> **Agent:** I won't take up more of your time. Thanks for being straightforward about where things stand.
>
> **Customer:** Yeah, no problem. Appreciate the call.

Turns: 20 (10 Agent / 10 Customer). Word count: 415 (Agent 245 / Customer 170).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 210 |
| `agent_performance_score` | 3 |
| `objection_handling_quality` | 2 |
| `lead_quality_score` | 2 |
| `call_category` | Failed Sale |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.22 |
| `speaking_rate_wpm` | 119 |
| `speech_to_non_speech_ratio` | 0.78 |
| `agent_talk_ratio` | 0.59 |
| `average_energy_level` | low |
| `price_mentions_count` | 0 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Referral-based firm with low engagement throughout. Customer expressed general distrust of sales tools based on past unused trials and stated the firm is not in growth mode this year. Agent kept the approach low-pressure, did not push for commitment, and limited follow-up to a single distant check-in at the customer's request. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (low) — minimal, passive engagement, no questions asked back, "probably nothing right now," but never an explicit hard rejection.
- ✓ transcript supports `main_objection` (trust) — "every vendor says their tool will fix things and half the time it just sits there unused" is skepticism about vendor claims specifically, not a stated lack of need.
- ✓ transcript supports `customer_sentiment` (negative) — dismissive tone throughout ("not sure why we're doing this call," short flat answers, "I'm not going to promise I'll look at it closely").
- ✓ transcript supports `sale_result` (No Sale) — no next step beyond an optional distant check-in; no purchase signal at any point.
- ✓ transcript supports `follow_up_needed` (false) — the only follow-up mentioned is an optional, customer-limited six-month check-in, not a required near-term action.
- ✓ transcript supports `closing_attempt` (weak) — agent only gestures toward "I'll send a short overview," never asks for any commitment.
- ✓ `manager_notes` grounded — referral-based structure, past unused trials, "not in growth mode this year," and the single-check-in limit are all stated in the transcript; no invented facts.
- ✓ audio features realistic — 210s duration, 119 wpm, and a higher 0.22 silence ratio consistent with a flatter, more passive, lower-energy exchange with more conversational gaps.
- ✓ no Ground Truth violations. **Contrast Case 4 verified:** genuinely low, passive customer intent — not merely a strong objection — drives the `No Sale` outcome; the agent's execution (respectful, non-pushy, appropriately scaled-back ask) is not the cause of the loss.

---

## Summary of the four calls

| Call ID | Agent | Outcome | Objection | Intent | Sentiment | Agent Score | Contrast Case |
|---|---|---|---|---|---|---|---|
| CALL_001 | Sarah Levi | Sale | trust | high | positive | 5 | — |
| CALL_002 | Sarah Levi | Sale | integration | high | positive | 4 | — |
| CALL_003 | Sarah Levi | No Sale | authority | medium | neutral | 5 | Case 5 (strong performance, failed call) |
| CALL_004 | Sarah Levi | No Sale | trust | low | negative | 3 | Case 4 (low intent, No Sale) |

All four calls use Sarah Levi per the frozen matrix — Batch 1 covers her full six-call allocation minus CALL_005/CALL_006, which belong to a later batch. Each customer was written with a distinct voice: Ronit (guarded but fair, wants proof), Avi (technical, honest-broker energy, decisive once reassured), Yossi (cooperative but structurally powerless), Michal (flat, dismissive, genuinely uninterested). No dialogue structure, opening line, or objection-resolution beat was reused across the four transcripts.

## Assumptions made

- Specific customer names, titles, and company details (e.g. Ronit Aviram/asset management firm, Avi Katz/healthcare provider network, Yossi Peretz/Dana the owner, Michal Regev/consulting firm) were invented to make the transcripts concrete — these are fictional per the project's fictional B2B SaaS product context (CLAUDE.md, dataset_design.md §1) and do not correspond to any real company.
- `call_category` values were assigned by judgment against the 6-value taxonomy (dataset_design.md §10), since the matrix does not fix this field: `Successful Sale` (CALL_001, straightforward close), `High-Value Opportunity` (CALL_002, enterprise-scale multi-region deal), `Follow-up Needed` (CALL_003, matches the still-open path to the real decision-maker), `Failed Sale` (CALL_004, poor-fit lead with no further action).
- CALL_002's `sale_result = Sale` required the transcript to contain an explicit firm purchase commitment even though `closing_attempt = medium` (agent-initiated). Resolved by having the customer volunteer the firm commitment ("consider this a yes... I'll get the purchase order moving") while the agent's own closing behavior stayed at medium strength (scheduling scoping, not asking for a signature) — keeping both matrix fields simultaneously true and transcript-grounded.
- CALL_002's `follow_up_needed = false` (fixed by the matrix) was interpreted as: the sales decision itself is closed (firm commitment obtained), so no further *sales* follow-up is needed, even though a technical scoping call is scheduled next (`next_meeting_scheduled = true`) as an implementation step. This distinguishes "is the deal still undecided" from "is there a subsequent operational meeting."
- `word_count` (Agent/Customer split) is not a column in `historical_sales_calls.csv`'s schema (dataset_design.md §14) and was used only internally to derive `speaking_rate_wpm` and `agent_talk_ratio` consistently — it is not proposed as a new CSV column.

## QA observations

- All four transcripts fall within the required 20–35 turn range (24, 24, 22, 20) and 350–700 word range (667, 656, 492, 415).
- `speaking_rate_wpm` (125, 131, 123, 119) and `call_duration_seconds` (320, 300, 240, 210) were derived directly from each transcript's verified word count, not chosen independently, and both fall within dataset_design.md §11's realistic ranges (100–190 wpm, 180–900s).
- `agent_talk_ratio` (0.63, 0.55, 0.68, 0.59) was computed from actual Agent-line vs. Customer-line word counts per transcript, within the 0.35–0.75 realistic range, and tracks plausibly with each call's dynamic (CALL_003 highest — agent-led proposal-building for an absent decision-maker; CALL_002 lowest — customer does more of the talking in a collaborative technical discussion).
- `price_mentions_count` (2, 2, 3, 0) and `competitor_mentions_count` (0, 0, 0, 0) were counted directly against final transcript text via keyword search (`price`/`pricing`/`cost`/`budget`; `competitor`), not estimated. No competitor was named in any of the four calls, consistent with none of them having `main_objection = competitor`.
- No repeated opening lines, objection-handling beats, or closing phrasing across the four transcripts; each agent-customer exchange follows a different shape (trust-rebuild-then-close, honest-estimate-then-collaborative-commit, discovery-then-blocked-by-absent-authority, respectful-disengagement).

## Confirmation that Ground Truth Rules were respected

- Every structured field (`customer_intent`, `main_objection`, `customer_sentiment`, `sale_result`, `follow_up_needed`, `closing_attempt`) is directly supported by that call's transcript text, verified per-call in each Ground Truth validation checklist above — none were assigned to fit the matrix's plan in a way the transcript doesn't actually back up.
- No structured field contradicts its transcript (e.g. CALL_004's `closing_attempt = weak` matches the agent never asking for commitment; CALL_003's `decision_maker_present = false` matches Dana never being on the call).
- `manager_notes` in all four rows restate only what the transcript contains — no invented budgets, dates, names, or outcomes beyond what each customer or agent actually said.
- CALL_003 and CALL_004 correctly use `No Sale` rather than being forced toward a more "successful-sounding" label, and CALL_003 explicitly decouples `agent_performance_score` from `sale_result` per Contrast Case 5's requirement.
- Audio-derived features are treated as a second, independent source of truth (not derived from transcript content) but were kept internally consistent with each transcript's actual length and speaker balance, per dataset_design.md §11 and the CLAUDE.md Ground Truth Rules — none are fabricated or defaulted, and all fall within the defined realistic ranges.

---

**Batch 2 (CALL_005–CALL_008 or as directed) has not been started.** No CSV files have been generated in this sub-phase.
