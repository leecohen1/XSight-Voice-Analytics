# XSight — Generated Historical Calls, Batch 2 (Phase 5B.1)

**Status: draft transcripts and full row content for CALL_005–CALL_008 only. No CSV files generated in this sub-phase.** This document authors the full historical-call record for the next four rows of `data/historical_sales_calls.csv`, strictly following the frozen assignments in [docs/historical_call_matrix.md](historical_call_matrix.md), the schema in [docs/dataset_design.md](dataset_design.md) §14, and — for the first time — the [Transcript Writing Guidelines](../CLAUDE.md#transcript-writing-guidelines) added to `CLAUDE.md` after the Batch 1 review. No matrix assignment (agent, segment, industry, intent, objection, sentiment, outcome, closing attempt, lead quality, decision-maker presence, contrast-case role) was changed.

This batch closes out Sarah Levi's remaining allocation (CALL_005, CALL_006) and opens Daniel Cohen's (CALL_007, CALL_008), including Contrast Case 1 (CALL_007). Each transcript was written as an independent piece — no wording, sentence rhythm, or acknowledgment pattern was reused from Batch 1 or from the other calls in this batch. A literal-string check against the eight banned templates flagged in `CLAUDE.md` ("That's fair...", "Understood.", "That's helpful.", "Got it.", "I appreciate you being...", "I'd rather ... than ...", "Can I ask...", "That's a common...") returned zero matches across all four transcripts.

---

## CALL_005

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_005 |
| `agent_name` | Sarah Levi |
| `customer_segment` | Mid-Market |
| `industry` | Manufacturing |
| `company_size` | ~300 |
| `sale_result` | Follow-up Needed |
| `customer_intent` | medium |
| `main_objection` | integration |
| `customer_sentiment` | mixed |
| `follow_up_needed` | true |
| `closing_attempt` | medium |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Ilan Barak, Sales Operations Manager at an industrial equipment manufacturer. Analytical, jumps between topics mid-thought, guarded after two failed vendor attempts.

> **Agent:** Hi Ilan, thanks for jumping on. Before anything else — what's actually driving this search right now? Something specific, or just general house-cleaning?
>
> **Customer:** Little of both, I guess. We've got quotes going out of three different systems depending on which rep does it, and half the time nobody knows which version the customer actually saw last.
>
> **Agent:** That gets expensive fast. How many reps are we talking about?
>
> **Customer:** Nine on the sales side, but there's also two people in engineering who pull quote data for scheduling. So really it touches eleven people, not nine.
>
> **Agent:** That engineering dependency matters. What system are they pulling quote data from today?
>
> **Customer:** Our ERP, mostly. It's an older on-prem system, honestly kind of a mess — we've had two failed integration projects with it already. Different vendors, same result. Nothing actually synced.
>
> **Agent:** What broke, specifically? Data-mapping issue, or more of a connectivity problem?
>
> **Customer:** Both, kind of. First vendor couldn't handle our custom part-number format. Second one technically connected, but the sync ran once a day, so by the time anyone looked at it the numbers were already stale.
>
> **Agent:** Real-time sync against a custom on-prem ERP is a harder problem than most vendors are willing to admit up front. I don't want to promise it works until our integrations team actually looks at your setup.
>
> **Customer:** Honestly, that's the first straight answer I've gotten on this. Everyone else just says "yes, we integrate with anything."
>
> **Agent:** Better you hear that from me now than three months into a broken rollout. Can I get someone from our side on a call with whoever manages your ERP?
>
> **Customer:** Sure, that'd be Priya, she handles that side. Actually — wait, before we get into that, does the platform handle forecasting too, or is that a separate thing?
>
> **Agent:** Forecasting's built in — pipeline and revenue both. But let's hold off on that until we know the integration actually works, because none of it matters much if the quote data doesn't sync.
>
> **Customer:** Right, right. Sorry, go back to the ERP call — when could that happen?
>
> **Agent:** I can have someone reach out to Priya this week. I wouldn't expect a real answer on feasibility for another week or two after that, given the part-number issue you described.
>
> **Customer:** Slower than I'd like, but it's more realistic than what we got last time. Fine.
>
> **Agent:** How's the team feeling about switching tools in general? Sometimes the tech's the easy part and getting people to actually use it is the hard part.
>
> **Customer:** Mixed. A couple reps like the idea. A couple are annoyed we're even looking again after two failed attempts already.
>
> **Agent:** Good to know going in. I don't want to sell you something that dies in three months because reps won't touch it.
>
> **Customer:** Yeah. Look — I want this to work. I just don't have a lot of trust left after the last two rounds.
>
> **Agent:** Then the ERP call is the actual test, not anything I say on this call. Let's get that scheduled and see what Priya finds.
>
> **Customer:** Okay. Send me what you need from her and I'll loop her in today.

Turns: 22 (11 Agent / 11 Customer). Word count: 531 (Agent 268 / Customer 263).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 270 |
| `agent_performance_score` | 4 |
| `objection_handling_quality` | 4 |
| `lead_quality_score` | 3 |
| `call_category` | Follow-up Needed |
| `next_meeting_scheduled` | true |
| `silence_ratio` | 0.15 |
| `speaking_rate_wpm` | 118 |
| `speech_to_non_speech_ratio` | 0.85 |
| `agent_talk_ratio` | 0.50 |
| `average_energy_level` | medium |
| `price_mentions_count` | 0 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer has been burned by two previous failed ERP integrations (custom part-number format issues, stale daily sync). Agent declined to promise integration success before a technical validation call with the customer's ERP owner, Priya. Team adoption is mixed after two failed prior attempts — worth flagging for rollout planning if the integration proves feasible. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (medium) — engaged, answers in detail, but repeatedly conditions everything on the ERP test rather than signaling readiness to move forward.
- ✓ transcript supports `main_objection` (integration) — entire call centers on two prior failed ERP syncs, a custom part-number format, and stale data.
- ✓ transcript supports `customer_sentiment` (mixed) — shifts from frustration ("kind of a mess") to relief ("first straight answer I've gotten") to renewed caution ("don't have a lot of trust left").
- ✓ transcript supports `sale_result` (Follow-up Needed) — nothing is decided; everything is contingent on the still-unscheduled technical call with Priya.
- ✓ transcript supports `follow_up_needed` (true) — explicit next step: reaching out to Priya this week, with feasibility unknown for another 1–2 weeks after.
- ✓ transcript supports `closing_attempt` (medium) — agent moves the process forward (scheduling the ERP call) without asking for any commitment or signature.
- ✓ `manager_notes` grounded — part-number format issue, stale daily sync, Priya's role, and mixed team sentiment are all stated in the transcript.
- ✓ audio features realistic — 270s duration, 118 wpm, and a roughly even 0.50 agent talk ratio consistent with a genuinely two-directional, topic-jumping discovery call.
- ✓ no Ground Truth violations.

---

## CALL_006

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_006 |
| `agent_name` | Sarah Levi |
| `customer_segment` | Enterprise |
| `industry` | Technology |
| `company_size` | ~2,000 |
| `sale_result` | Follow-up Needed |
| `customer_intent` | medium |
| `main_objection` | security |
| `customer_sentiment` | neutral |
| `follow_up_needed` | true |
| `closing_attempt` | weak |
| `decision_maker_present` | false |

### 2. Transcript

Customer: Tomer Adler, Senior IT Security Analyst, doing technical vetting ahead of the actual buyer's decision. Terse and procedural, but not a checklist robot — reveals a bit of the pressure and history behind the review as the call goes on.

> **Agent:** Hi Tomer, thanks for the time. Before we get into specifics — what's actually driving the evaluation right now? Is this a scheduled renewal cycle, or did something change?
>
> **Customer:** Bit of both, honestly. Our current sales tool's contract is up in the fall, and after two vendors failed our review this quarter already, leadership wants security looped in earlier this time instead of at the end.
>
> **Agent:** Is security the last approval stage for you, or are other teams still evaluating the platform in parallel?
>
> **Customer:** Sales ops is doing the functional side in parallel. If I clear it and they like the product, it goes to procurement. So I'm not the last stop, but I'm usually the one that kills deals.
>
> **Agent:** What usually trips vendors up in your review — a specific gap, or more just incomplete answers?
>
> **Customer:** Mostly incomplete answers, actually. Vendors say "yes we're compliant" without documentation to back it up. Sorry, I'm jumping around a bit — I've got my checklist open. SOC 2 status, data residency, encryption at rest and in transit, breach notification process.
>
> **Agent:** We're SOC 2 Type II. Data residency — where do you need it hosted?
>
> **Customer:** US-East, contractually. No exceptions.
>
> **Agent:** That's standard for us, no issue. Encryption is AES-256 at rest, TLS 1.2 in transit.
>
> **Customer:** Breach notification SLA?
>
> **Agent:** Seventy-two hours, written into the contract.
>
> **Customer:** Sub-processors — do you use any, and is there a list?
>
> **Agent:** Yes, published list, updated whenever it changes. I can send it after this call.
>
> **Customer:** Do you notify customers before adding a new one, or after?
>
> **Agent:** Before. Thirty-day notice, with an option to object.
>
> **Customer:** That's better than most of what I've reviewed this quarter. We've already rejected two vendors this quarter over exactly this kind of thing.
>
> **Agent:** Anything that's failed vetting before that I should know about now instead of later?
>
> **Customer:** One vendor last year didn't support single sign-on. Dealbreaker for us. I'm probably being more picky than usual after this quarter, so bear with me.
>
> **Agent:** No, that context helps me actually answer the right questions instead of guessing. We support SAML-based SSO, standard on the enterprise tier.
>
> **Customer:** Audit logs and data deletion — retention period, export options, and what happens to backups if we terminate.
>
> **Agent:** Twelve months retention, exportable by API or CSV. Full deletion within thirty days of contract end, backups included on the same cycle.
>
> **Customer:** That covers my list. I'll write this up for the security committee.
>
> **Agent:** How long does that review usually take on your end?
>
> **Customer:** Depends on the queue. Two weeks, sometimes four.
>
> **Agent:** I'll get the SOC 2 report and the sub-processor list over today so the committee has everything for a first pass. Once they've reviewed it, would it make sense to put fifteen minutes on the calendar to walk through any open questions together, instead of going back and forth over email?
>
> **Customer:** That's reasonable. I'll reach out once we're through the queue.
>
> **Agent:** Sounds good — I'll be here whenever that is.

Turns: 27 (14 Agent / 13 Customer). Word count: 508 (Agent 259 / Customer 249).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 285 |
| `agent_performance_score` | 4 |
| `objection_handling_quality` | 5 |
| `lead_quality_score` | 3 |
| `call_category` | Follow-up Needed |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.11 |
| `speaking_rate_wpm` | 107 |
| `speech_to_non_speech_ratio` | 0.89 |
| `agent_talk_ratio` | 0.51 |
| `average_energy_level` | low |
| `price_mentions_count` | 0 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Enterprise technical security review conducted by an IT security analyst, not the final buyer. All standard vetting items — SOC 2, encryption, breach SLA, sub-processors, SSO, audit log retention, data deletion — were answered directly and accurately. Review comes after two other vendors were rejected this quarter, which explains the analyst's heightened scrutiny. Security committee review typically takes two to four weeks; SOC 2 report and sub-processor list were sent to support that review, with a follow-up walkthrough offered once the committee has responded. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (medium) — thorough, methodical engagement through the full checklist and openness about internal process, but no personal buying signal since Tomer isn't the buyer.
- ✓ transcript supports `main_objection` (security) — the call is built around a security/compliance checklist: SOC 2, residency, encryption, breach SLA, sub-processors, SSO, audit logs, deletion.
- ✓ transcript supports `customer_sentiment` (neutral) — procedural and businesslike throughout; the few personal asides ("I'm probably being more picky than usual") explain his rigor without turning the tone positive or negative.
- ✓ transcript supports `sale_result` (Follow-up Needed) — nothing is decided on this call; it feeds into a security committee review with its own timeline.
- ✓ transcript supports `follow_up_needed` (true) — explicit two-to-four-week committee review pending, with documents sent to support it.
- ✓ transcript supports `closing_attempt` (weak) — agent offers a follow-up walkthrough only conditionally ("once they've reviewed it, would it make sense to..."), with no specific date or firm commitment — a gesture toward a next step, not a direct ask.
- ✓ `manager_notes` grounded — every item (SOC 2, encryption spec, breach SLA, SSO, audit retention, deletion process, prior-quarter rejections, committee timeline) is stated in the transcript.
- ✓ audio features realistic — 285s duration, 107 wpm, and a low 0.11 silence ratio consistent with a still fairly brisk, professional exchange that now includes a short discovery section and a few natural asides, recomputed from the revised transcript's actual word count.
- ✓ no Ground Truth violations.

---

## CALL_007 — Contrast Case 1

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_007 |
| `agent_name` | Daniel Cohen |
| `customer_segment` | Mid-Market |
| `industry` | Retail |
| `company_size` | ~180 |
| `sale_result` | Sale |
| `customer_intent` | high |
| `main_objection` | price |
| `customer_sentiment` | positive |
| `follow_up_needed` | false |
| `closing_attempt` | strong |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Talia Ben-Ari, owner of a multi-store fashion retail chain. Fast-talking, blunt about price, energetic and a little sarcastic once won over.

> **Agent:** Talia, hey — good to finally get you on the phone. I heard you've been comparing us against a couple other platforms?
>
> **Customer:** Two others, yeah. And honestly the other two are cheaper, so you're gonna have to make this worth it.
>
> **Agent:** Good place to start. What are they quoting you?
>
> **Customer:** One's about sixty percent of your price. The other's even less, but it's basically a glorified spreadsheet with a nicer interface.
>
> **Agent:** What made you even take our call if they're that much cheaper?
>
> **Customer:** Because my ops manager used your platform at her last job and said the automation actually worked, not just looked good in a demo.
>
> **Agent:** That's the part that doesn't show up on a pricing sheet. What's she dealing with day to day right now that made her say that?
>
> **Customer:** Restock timing, mostly. We lose sales constantly because nobody catches low inventory until a customer's standing at the register asking for a size we don't have.
>
> **Agent:** How many times a week would you say that happens, roughly?
>
> **Customer:** Honestly? Probably fifteen, twenty times across our stores. It adds up — I did the math once and just about had a heart attack.
>
> **Agent:** Let's actually do that math together, because that's the real comparison, not sticker price versus sticker price. If the platform catches even half of those before the customer walks, what's an average lost sale worth to you?
>
> **Customer:** Maybe eighty bucks average ticket, sometimes way more.
>
> **Agent:** Half of twenty a week at eighty bucks is eight hundred a week, just from that one thing — not counting everything else the platform does.
>
> **Customer:** Okay, when you put it that way — yeah, that's more than the price gap.
>
> **Agent:** That's the reframe I wanted you to see for yourself, not just hear from me. What's actually stopping you from signing today, if the number works?
>
> **Customer:** Nothing, really. I mean — I do want my ops manager on the onboarding call, she'll actually use this thing day to day.
>
> **Agent:** Done, we'll build onboarding around her schedule, not just yours. Can we get the contract signed this week so we don't lose momentum?
>
> **Customer:** Yes. Send it over, I'll sign today if my ops manager's free to jump on for ten minutes first.
>
> **Agent:** I'll set that up right now. Congrats, by the way — this is going to fix the thing that's actually been bleeding you money.
>
> **Customer:** We'll see! Ask me again in three months.

Turns: 20 (10 Agent / 10 Customer). Word count: 416 (Agent 222 / Customer 194).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 190 |
| `agent_performance_score` | 5 |
| `objection_handling_quality` | 5 |
| `lead_quality_score` | 4 |
| `call_category` | Successful Sale |
| `next_meeting_scheduled` | true |
| `silence_ratio` | 0.08 |
| `speaking_rate_wpm` | 131 |
| `speech_to_non_speech_ratio` | 0.92 |
| `agent_talk_ratio` | 0.53 |
| `average_energy_level` | high |
| `price_mentions_count` | 5 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer was price-comparing against two cheaper competitors going into the call. Agent reframed the comparison around the cost of missed restock-driven sales (roughly $800/week by the customer's own numbers), which closed the price gap in her own math rather than the agent's claims. Contract signed same day, pending a short onboarding call with the customer's operations manager. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (high) — explicit readiness to sign, only conditioned on a ten-minute onboarding call for her ops manager.
- ✓ transcript supports `main_objection` (price) — opens the call stating two competitors are cheaper and the platform will "have to make this worth it."
- ✓ transcript supports `customer_sentiment` (positive) — energetic, appreciative of the honest reframe, closes with a joking "We'll see! Ask me again in three months."
- ✓ transcript supports `sale_result` (Sale) — explicit "Yes. Send it over, I'll sign today."
- ✓ transcript supports `follow_up_needed` (false) — the sale itself is closed; the only remaining item is a short onboarding call, an implementation step.
- ✓ transcript supports `closing_attempt` (strong) — direct, specific ask: "Can we get the contract signed this week."
- ✓ `manager_notes` grounded — the two cheaper competitors, the $800/week estimate (derived directly from the customer's own numbers in the transcript), and the onboarding call are all stated.
- ✓ audio features realistic — 190s duration, 131 wpm, and a low 0.08 silence ratio consistent with a fast, energetic, back-and-forth exchange.
- ✓ no Ground Truth violations. **Contrast Case 1 verified:** price objection raised explicitly at the top of the call, resolved through a quantified reframe, ending in `Sale`.

---

## CALL_008

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_008 |
| `agent_name` | Daniel Cohen |
| `customer_segment` | Enterprise |
| `industry` | Logistics |
| `company_size` | ~1,500 |
| `sale_result` | Sale |
| `customer_intent` | high |
| `main_objection` | competitor |
| `customer_sentiment` | positive |
| `follow_up_needed` | false |
| `closing_attempt` | strong |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Marcus Webb, VP of Sales at an enterprise logistics company. Analytical, methodical, over-explains operational pain in detail before getting to the point.

> **Agent:** Marcus, thanks for making time — I know you're mid-evaluation with PipeFlow already, so I'll get straight to it. What's not working with them?
>
> **Customer:** It's not that it's broken, exactly. It's more that we've outgrown it. We've got fourteen hundred people using different parts of the platform for freight quoting, and PipeFlow's reporting just — it doesn't scale past a certain data volume. Reports time out. Support says it's a "known limitation," which is a nice way of saying they're not fixing it.
>
> **Agent:** How long have you been dealing with the timeout issue?
>
> **Customer:** Eight months, on and off. We've built workarounds — exporting to spreadsheets, running reports overnight — but that's not a platform, that's a patch job.
>
> **Agent:** What's the actual cost of that, in your team's time?
>
> **Customer:** I had someone estimate it. About twelve hours a week across the reporting team, just babysitting exports and reconciling numbers that should just be live.
>
> **Agent:** Twelve hours a week is basically a third of a full-time role, doing nothing but working around a limitation. Have you told PipeFlow that number?
>
> **Customer:** We have. Their answer was an upgrade to their enterprise tier, which — I looked at it — barely raises the data ceiling and costs almost the same as what you're proposing anyway.
>
> **Agent:** So you're not actually comparing our price to their current price. You're comparing us to what they'd charge you to sort of fix this, maybe.
>
> **Customer:** When you put it like that, yeah. That's actually a fair way to frame it.
>
> **Agent:** What's your data volume look like at peak, roughly?
>
> **Customer:** We're pushing close to two million records a month across freight and warehousing combined.
>
> **Agent:** We've got customers at that scale and above running live reporting without the timeout issue you're describing. I can get you two reference calls with logistics customers specifically, not just any enterprise account.
>
> **Customer:** I'd take that. My CFO's going to ask for proof, not just a promise.
>
> **Agent:** Makes sense. What would your CFO need to see to sign off, beyond the references?
>
> **Customer:** Migration plan, mostly. We can't have reporting go dark during a transition — that's non-negotiable given how we operate.
>
> **Agent:** We'll build a parallel-run period, both systems live for thirty days before PipeFlow gets switched off, so there's zero gap. I'll have that migration plan drafted by end of week, references included.
>
> **Customer:** If that plan looks solid, we're moving forward. I don't need to drag this out — we've known for months PipeFlow isn't going to fix this.
>
> **Agent:** Then let's not drag it out either. I'll get the plan and references to you and your CFO by Friday, and we can target a contract signature the following week.
>
> **Customer:** Works for me.

Turns: 20 (10 Agent / 10 Customer). Word count: 458 (Agent 222 / Customer 236).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 240 |
| `agent_performance_score` | 5 |
| `objection_handling_quality` | 5 |
| `lead_quality_score` | 5 |
| `call_category` | High-Value Opportunity |
| `next_meeting_scheduled` | true |
| `silence_ratio` | 0.18 |
| `speaking_rate_wpm` | 115 |
| `speech_to_non_speech_ratio` | 0.82 |
| `agent_talk_ratio` | 0.48 |
| `average_energy_level` | medium |
| `price_mentions_count` | 4 |
| `competitor_mentions_count` | 5 |
| `manager_notes` | Customer has dealt with eight months of reporting timeouts on their current platform (PipeFlow) at scale, costing an estimated 12 hours/week in manual workaround time. Agent reframed the price comparison against the cost of the competitor's own proposed fix rather than list price, and committed to a 30-day parallel-run migration plus logistics-specific reference calls to satisfy the customer's CFO ahead of signature. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (high) — states plainly "we're moving forward" and "we've known for months," with only a migration plan and references as remaining steps.
- ✓ transcript supports `main_objection` (competitor) — the whole call is framed around limitations of the customer's current platform, PipeFlow, named repeatedly.
- ✓ transcript supports `customer_sentiment` (positive) — receptive throughout, explicitly agrees with the agent's reframing ("That's actually a fair way to frame it").
- ✓ transcript supports `sale_result` (Sale) — explicit firm commitment: "If that plan looks solid, we're moving forward," confirmed with "Works for me" against a specific signature timeline.
- ✓ transcript supports `follow_up_needed` (false) — the sale decision itself is made; remaining steps (migration plan, references, signature) are implementation and paperwork, not an open sales question.
- ✓ transcript supports `closing_attempt` (strong) — agent proposes a concrete migration plan, reference calls, and a specific signature timeline ("the following week").
- ✓ `manager_notes` grounded — the 8-month timeout issue, 12 hours/week cost estimate, PipeFlow's proposed fix, and the 30-day parallel-run plan are all stated in the transcript.
- ✓ audio features realistic — 240s duration, 115 wpm, and a higher 0.18 silence ratio consistent with a more deliberate, detail-heavy, analytical exchange with longer explanatory pauses.
- ✓ no Ground Truth violations.

---

## Summary of the four calls

| Call ID | Agent | Outcome | Objection | Intent | Sentiment | Agent Score | Contrast Case |
|---|---|---|---|---|---|---|---|
| CALL_005 | Sarah Levi | Follow-up Needed | integration | medium | mixed | 4 | — |
| CALL_006 | Sarah Levi | Follow-up Needed | security | medium | neutral | 4 | — |
| CALL_007 | Daniel Cohen | Sale | price | high | positive | 5 | Case 1 (price → Sale) |
| CALL_008 | Daniel Cohen | Sale | competitor | high | positive | 5 | — |

This batch completes Sarah Levi's six-call allocation (CALL_001, 002, 003, 004, 005, 006) and opens Daniel Cohen's with two of his six (CALL_007, 008 — the remaining four, including Contrast Cases 2 and 7 opposite CALL_007, belong to a later batch).

## Style-diversity self-audit (per the new Transcript Writing Guidelines)

This is the check the Batch 1 review specifically asked for, applied before submitting this batch:

- **Banned templates:** a literal-string search for all eight banned phrases across all four transcripts returned zero matches (verified via `grep`, not by eye).
- **Distinct customer registers:** Ilan (CALL_005) is analytical but scattered, jumping topics mid-thought and correcting himself ("Actually — wait," "Right, right. Sorry, go back to..."). Tomer (CALL_006) is terse and procedural by default, but not a checklist robot — he volunteers context unprompted ("two vendors failed our review this quarter," "I'm probably being more picky than usual") between his short, clipped answers. Talia (CALL_007) is fast, blunt, and a little sarcastic ("gonna have to make this worth it," "just about had a heart attack," "We'll see!"). Marcus (CALL_008) over-explains in long, detail-dense sentences before landing on his point. None of the four share a sentence rhythm, and none use the same acknowledgment word for agreement (Ilan: "Fine." / "Right, right." — Tomer: "Correct." / "That's reasonable." — Talia: "Yes." / "Okay, when you put it that way—" — Marcus: "Works for me." / "When you put it like that, yeah.").
- **Agent variation within a consistent style:** Sarah Levi's two calls here (CALL_005, CALL_006) read differently from each other in pacing and register — expansive and exploratory with Ilan, tighter and more checklist-anchored with Tomer but still opening with genuine discovery questions rather than diving straight into vetting — while both still show her trust-building discovery strength from `dataset_design.md` §3. Daniel Cohen's two calls (CALL_007, CALL_008) both show his price/competitor-reframing strength, but CALL_007 is fast and conversational while CALL_008 is measured and numbers-driven, matching each customer's own register rather than repeating a fixed "Daniel voice."
- **No shared closing pattern:** the four calls end four different ways — an open, unresolved "send me what you need" (CALL_005), a conditional, undated offer to walk through open questions once the committee responds (CALL_006), a joking deflection "We'll see! Ask me again in three months" (CALL_007), and a plain confirmation "Works for me" (CALL_008) — deliberately avoiding the uniform "thank you / talk soon" close pattern flagged in the Batch 1 review.
- **Natural imperfections present:** self-corrections ("So really it touches eleven people, not nine"), mid-sentence topic changes (Ilan asking about forecasting mid-objection-discussion), trailing em-dash cutoffs (Marcus: "it doesn't scale past a certain data volume. Reports time out."), an explicit self-aware aside about jumping around a checklist (Tomer, CALL_006), and fragment-style short answers throughout CALL_006's core vetting section — none of the four transcripts is uniformly "clean," structured prose.
- **CALL_006 revision note:** the first draft of this call read too much like a compliance questionnaire — pure Q&A with no discovery, no personality, and an abrupt ending. It was revised in place (metadata, outcome, objection, sentiment, and all structured-field judgments unchanged) to add a short discovery opening (why the evaluation is happening now, where security sits in the approval chain), two grounded human asides from Tomer, two consultative questions from Sarah, and a softer, conditional close proposing a future walkthrough instead of stopping cold after sending documents.

## Assumptions made

- Customer names, titles, and company specifics (Ilan Barak, Tomer Adler, Talia Ben-Ari, Marcus Webb) are fictional, consistent with the project's fictional B2B SaaS product context.
- The fictional competing product name **"PipeFlow"** was invented for CALL_008's competitor objection, since `main_objection = competitor` requires the transcript to reference a specific rival product, not a generic "another vendor" — no real company or product name is used.
- As in Batch 1, CALL_007 and CALL_008 both carry `follow_up_needed = false` (fixed by the matrix) despite each having a concrete next step (a short onboarding call; a Friday migration-plan delivery and following-week signature). Interpreted consistently with the Batch 1 precedent: `follow_up_needed` tracks whether the *sale decision* is still open, not whether any subsequent operational step exists — both calls end with an explicit, firm purchase commitment, so the sale itself is closed.
- `call_category` values were assigned by judgment against the 6-value taxonomy: `Follow-up Needed` for CALL_005 and CALL_006 (matches their still-open status), `Successful Sale` for CALL_007 (straightforward mid-market close), `High-Value Opportunity` for CALL_008 (enterprise-scale, CFO-level, 1,400+ seat account) — consistent with how `High-Value Opportunity` was used for CALL_002 in Batch 1.

## QA observations

- All four transcripts fall within the required 20–35 turn range (22, 27, 20, 20) and 350–700 word range (531, 508, 416, 458).
- `speaking_rate_wpm` (118, 107, 131, 115) and `call_duration_seconds` (270, 285, 190, 240) were derived from each transcript's actual verified word count, within dataset_design.md §11's realistic ranges. CALL_006's values were recomputed after the conversational-realism revision (see below) — its word count grew from an initial 376 to 508 once a discovery section and two humanizing exchanges were added, so `call_duration_seconds` and `speaking_rate_wpm` were updated accordingly to stay grounded in the actual text.
- `agent_talk_ratio` (0.50, 0.51, 0.53, 0.48) was computed from real Agent-line vs. Customer-line word counts, and varies plausibly with each call's dynamic — lowest in CALL_008, where Marcus does most of the explaining; CALL_006 shifted from 0.58 to 0.51 after the revision, since Tomer now carries more of the conversation with context and asides rather than one-line answers.
- `price_mentions_count` (0, 0, 5, 4) and `competitor_mentions_count` (0, 0, 0, 5) were counted directly against final transcript text via keyword search, not estimated — zero in the two Follow-up Needed calls (integration and security objections, no price/competitor discussion), concentrated in the two Sale calls where those were the actual objections.
- No sentence pattern, acknowledgment phrase, or closing line was reused across the four transcripts in this batch, nor between this batch and Batch 1.

## Confirmation that Ground Truth Rules were respected

- Every structured field is directly supported by that call's transcript text, verified per-call in each Ground Truth validation checklist above.
- No structured field contradicts its transcript (e.g. CALL_006's `decision_maker_present = false` matches Tomer explicitly deferring to a security committee; CALL_005's `customer_sentiment = mixed` matches the transcript's genuine tonal shift rather than a flat label).
- `manager_notes` in all four rows restate only what the transcript contains — no invented budgets, dates, names, or outcomes.
- Audio-derived features remain a second, independent source of truth, kept internally consistent with each transcript's actual length and speaker balance, within the realistic ranges defined in dataset_design.md §11 — none fabricated or defaulted.
- The new Transcript Writing Guidelines were applied and verified (see the style-diversity self-audit above) without altering any Batch 1 content, any matrix assignment, or any Ground Truth Rule.

---

**Batch 3 (Daniel Cohen's remaining calls — CALL_009 through CALL_012, including Contrast Cases 2, 7, and 8) has not been started.** No CSV files have been generated in this sub-phase.
