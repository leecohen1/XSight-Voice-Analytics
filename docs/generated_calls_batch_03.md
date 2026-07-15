# XSight — Generated Historical Calls, Batch 3 (Phase 5B.1)

**Status: draft transcripts and full row content for CALL_009–CALL_012 only. No CSV files generated in this sub-phase.** This document authors the full historical-call record for the next four rows of `data/historical_sales_calls.csv`, strictly following the frozen assignments in [docs/historical_call_matrix.md](historical_call_matrix.md), the schema in [docs/dataset_design.md](dataset_design.md) §14, and the [Transcript Writing Guidelines](../CLAUDE.md#transcript-writing-guidelines). No matrix assignment was changed.

This batch completes Daniel Cohen's six-call allocation (CALL_007–CALL_012) and covers three of the eight required contrast cases: Case 2 and Case 7 (CALL_009) and Case 8 (CALL_010, paired with CALL_004 from Batch 1). A literal-string check against the eight banned templates from `CLAUDE.md` returned zero matches across all four transcripts — an earlier draft of CALL_009, CALL_010, and CALL_011 each independently used the banned "I'd rather ... than ..." construction as Daniel Cohen's closing-empathy line; caught by the same grep check used in Batch 2 and rewritten before finalizing.

---

## CALL_009 — Contrast Case 2 and Contrast Case 7

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_009 |
| `agent_name` | Daniel Cohen |
| `customer_segment` | SMB |
| `industry` | Real Estate |
| `company_size` | ~15 |
| `sale_result` | No Sale |
| `customer_intent` | high |
| `main_objection` | price |
| `customer_sentiment` | mixed |
| `follow_up_needed` | false |
| `closing_attempt` | strong |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Renee Castillo, owner/broker of a small real estate brokerage. Warm, self-deprecating, emotionally open — genuinely torn rather than guarded.

> **Agent:** Renee, hey, thanks for hopping on — I know you've been going back and forth on this for a couple weeks. Where's your head at?
>
> **Customer:** Honestly? I love it. My office manager's been begging me to get something like this for our listing pipeline. I just keep choking on the price.
>
> **Agent:** What's the number doing that's making you choke?
>
> **Customer:** We're fifteen people, mostly commission-based agents. Every dollar I spend on software comes straight out of my own margin before anyone else sees a cent of it.
>
> **Agent:** That's a different math than a company with a fixed sales-ops budget. What does losing a listing actually cost you right now, when a referral falls through the cracks?
>
> **Customer:** More than I'd like to admit. Probably two or three deals a year where a referral just — goes cold because nobody followed up in time. Each one's worth eight, ten thousand in commission to me personally.
>
> **Agent:** So we're not really weighing the subscription against nothing. We're weighing it against two or three lost deals a year — call it twenty-five grand combined.
>
> **Customer:** When you put it that way, yeah, it's not close. I already knew that, honestly, I just needed to hear it out loud.
>
> **Agent:** Then let's get this moving. I can have the agreement over to you today — is there anything standing between us and a signature?
>
> **Customer:** Actually — yeah, there is, and I feel dumb bringing it up now. Our franchise group sent a notice this morning. Corporate's freezing all new software budgets for every office through end of quarter. Market's been slow, they're tightening everything.
>
> **Agent:** That's not something you control at the office level, I take it?
>
> **Customer:** Not even a little. It came from the top, applies to every franchisee, no exceptions listed. I called my regional director already hoping there was wiggle room. There isn't.
>
> **Agent:** That's rare, most people just go quiet on me instead of telling me why.
>
> **Customer:** I wanted this. I still want this. I just can't sign something corporate would flag two weeks from now.
>
> **Agent:** Makes sense. Better to know now than to chase a signature that was never going to happen. When does the freeze lift?
>
> **Customer:** End of quarter, supposedly. Could get extended if the market doesn't turn around — corporate's been vague about that part.
>
> **Agent:** I won't pretend I love hearing that, but I'm not going to push against a real budget freeze. Want me to check back once it lifts, or would you rather reach out when you're ready?
>
> **Customer:** Let me reach out. I don't want a countdown clock hanging over this, given how this quarter's already gone.
>
> **Agent:** No hard feelings on this end. It's still a good fit whenever the timing works for you.
>
> **Customer:** It is. Bad timing, not a bad answer — for what it's worth.

Turns: 20 (10 Agent / 10 Customer). Word count: 478 (Agent 219 / Customer 259).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 230 |
| `agent_performance_score` | 5 |
| `objection_handling_quality` | 5 |
| `lead_quality_score` | 4 |
| `call_category` | Failed Sale |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.12 |
| `speaking_rate_wpm` | 125 |
| `speech_to_non_speech_ratio` | 0.88 |
| `agent_talk_ratio` | 0.46 |
| `average_energy_level` | medium |
| `price_mentions_count` | 5 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer was fully persuaded by a quantified reframe (roughly $25K/year in lost referral commissions against the subscription cost) and was ready to sign today. Deal lost only because the customer's franchise corporate office issued a company-wide software spending freeze the same morning, unrelated to the agent's execution. Customer will reach out once the freeze lifts; no follow-up commitment was made on either side. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (high) — "is there anything standing between us and a signature?" is answered with a genuine blocker, not hesitation; the customer explicitly says "I wanted this. I still want this."
- ✓ transcript supports `main_objection` (price) — the call opens on price resistance ("I just keep choking on the price") and is resolved entirely on its own terms before the freeze is revealed.
- ✓ transcript supports `customer_sentiment` (mixed) — moves from guarded ("choking on the price") to relieved agreement ("it's not close") to genuine disappointment ("I feel dumb bringing it up now," "Bad timing, not a bad answer").
- ✓ transcript supports `sale_result` (No Sale) — explicit, external, non-negotiable blocker: a corporate-mandated spending freeze with "no exceptions listed."
- ✓ transcript supports `follow_up_needed` (false) — customer explicitly declines a scheduled check-in ("Let me reach out... I don't want a countdown clock").
- ✓ transcript supports `closing_attempt` (strong) — direct, specific ask: "I can have the agreement over to you today — is there anything standing between us and a signature?"
- ✓ `manager_notes` grounded — the $25K estimate is built directly from the customer's own numbers (two-to-three deals, $8–10K each) stated in the transcript; the freeze and its terms are stated verbatim.
- ✓ audio features realistic — 230s duration, 125 wpm, and a lower 0.46 agent talk ratio consistent with a customer who does most of the explaining once the real story comes out.
- ✓ no Ground Truth violations. **Contrast Case 2 verified:** price objection raised and resolved in-call, still ending in `No Sale` for a reason unrelated to price. **Contrast Case 7 verified:** same agent (Daniel Cohen), same objection (price), similarly high intent as CALL_007 — but here the deal is lost to an external budget freeze the agent could not have prevented, not to weaker execution; `agent_performance_score = 5` in both calls confirms the outcome divergence isn't about selling skill.

---

## CALL_010 — Contrast Case 8

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_010 |
| `agent_name` | Daniel Cohen |
| `customer_segment` | Mid-Market |
| `industry` | Finance |
| `company_size` | ~220 |
| `sale_result` | No Sale |
| `customer_intent` | medium |
| `main_objection` | authority |
| `customer_sentiment` | neutral |
| `follow_up_needed` | true |
| `closing_attempt` | medium |
| `decision_maker_present` | false |

### 2. Transcript

Customer: David Okonkwo, Director of Sales Operations at a mid-market finance company. Energetic internal champion, over-explains the committee politics, mildly frustrated by process rather than by the product.

> **Agent:** David, good to connect. Sounds like you've already got buy-in on your end — what's the actual path from here to a signed deal?
>
> **Customer:** That's the complicated part, honestly. I'm sold, my team's sold, but anything over fifteen thousand a year has to go through our vendor review committee. They meet quarterly.
>
> **Agent:** When's the next one?
>
> **Customer:** Six weeks out. I know, it's not the answer you want to hear.
>
> **Agent:** Walk me through who's actually on that committee — is it just finance, or does it pull from other departments too?
>
> **Customer:** Finance, IT security, and our COO's office. Three different agendas in one room, honestly it's a whole thing.
>
> **Agent:** What usually kills a proposal in that room, in your experience?
>
> **Customer:** IT security asking questions nobody prepped for, mostly. Or finance deciding the ROI story wasn't tight enough.
>
> **Agent:** Then let's build you a package that survives all three questions before you're even in the room — ROI numbers, a security one-pager, and something that shows this isn't just a nice-to-have for your team specifically.
>
> **Customer:** That would actually help a lot. I've walked into that room underprepared before and watched a good tool get tabled for two quarters.
>
> **Agent:** I don't want that happening here. Can you get me fifteen minutes with whoever leads the ROI conversation on the finance side, before the committee meets?
>
> **Customer:** I can try. Marguerite usually runs that piece. She's not easy to get on a call, though — everyone wants her time.
>
> **Agent:** I'll take whatever slot she has. In the meantime I'll build the ROI model off your numbers, so it's ready before you ever ask her for anything.
>
> **Customer:** That helps a lot, actually. If it were just up to me we'd have signed already.
>
> **Agent:** I believe that. Six weeks getting you properly armed for that room beats me pretending I can shortcut a process that isn't mine to shortcut.
>
> **Customer:** A couple vendors have tried going around the committee straight to our COO. Backfired every time.
>
> **Agent:** That's a pattern worth knowing before we're anywhere near your COO. I'll get you the ROI model and a security one-pager within two weeks, so you've got time to build support before the meeting.
>
> **Customer:** I'll flag it internally too, so it's actually on the agenda and not just floating around.
>
> **Agent:** Let's regroup the week before the committee meets and make sure everything's tight.
>
> **Customer:** Sounds right to me. Fingers crossed on the IT security piece — that's usually where things get stuck.

Turns: 20 (10 Agent / 10 Customer). Word count: 423 (Agent 228 / Customer 195).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 230 |
| `agent_performance_score` | 4 |
| `objection_handling_quality` | 3 |
| `lead_quality_score` | 3 |
| `call_category` | Follow-up Needed |
| `next_meeting_scheduled` | true |
| `silence_ratio` | 0.13 |
| `speaking_rate_wpm` | 110 |
| `speech_to_non_speech_ratio` | 0.87 |
| `agent_talk_ratio` | 0.54 |
| `average_energy_level` | medium |
| `price_mentions_count` | 0 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer is a strong internal champion, but purchases above $15K require a quarterly vendor review committee spanning finance, IT security, and the COO's office; the next meeting is six weeks out. Agent is preparing an ROI model and a security one-pager and requesting time with the finance stakeholder (Marguerite) ahead of the committee meeting. Customer warned that other vendors who tried bypassing the committee directly to the COO were unsuccessful. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (medium) — genuinely engaged and self-identified as sold ("I'm sold, my team's sold"), but intent alone can't move the deal, so it doesn't read as `high`.
- ✓ transcript supports `main_objection` (authority) — "anything over fifteen thousand a year has to go through our vendor review committee," and David repeatedly confirms he isn't the final decision-maker.
- ✓ transcript supports `customer_sentiment` (neutral) — professional and cooperative throughout, frustration is directed at the committee process in the abstract, not expressed as personal negativity toward the call.
- ✓ transcript supports `sale_result` (No Sale) — no commitment possible in this call; the actual decision sits with a committee that hasn't met yet.
- ✓ transcript supports `follow_up_needed` (true) — explicit plan to deliver materials within two weeks and regroup the week before the six-week-out committee meeting.
- ✓ transcript supports `closing_attempt` (medium) — agent moves the process forward (materials, stakeholder access, a regroup date) without any ask for signature or commitment, since none is possible.
- ✓ `manager_notes` grounded — the $15K threshold, committee composition, Marguerite, the two-week materials commitment, and the bypass-backfire warning are all stated in the transcript.
- ✓ audio features realistic — 230s duration, 110 wpm, and a higher 0.54 agent talk ratio consistent with Daniel driving a structured account-planning conversation.
- ✓ no Ground Truth violations. **Contrast Case 8 verified:** paired with CALL_004 (Batch 1) — both end in `No Sale`, but CALL_004's cause is `trust` (a genuinely disengaged, skeptical SMB owner) while CALL_010's is `authority` (an enthusiastic mid-market champion blocked by a formal committee process) — the same outcome, driven by two structurally different objections.

---

## CALL_011

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_011 |
| `agent_name` | Daniel Cohen |
| `customer_segment` | Mid-Market |
| `industry` | Manufacturing |
| `company_size` | ~400 |
| `sale_result` | Follow-up Needed |
| `customer_intent` | medium |
| `main_objection` | timing |
| `customer_sentiment` | neutral |
| `follow_up_needed` | true |
| `closing_attempt` | medium |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Carla Jensen, VP of Sales at a mid-market manufacturer. Calm, practical, dryly funny — brief when the answer is simple, direct when it isn't.

> **Agent:** Carla, thanks for jumping on. Last time we talked you seemed genuinely into this — has anything changed since then?
>
> **Customer:** Not with my opinion of the product, no. Timing's just brutal right now.
>
> **Agent:** Before we get into what's going on — remind me what got you interested in the first place?
>
> **Customer:** Our quote turnaround time, mostly. We're losing bids to competitors who just move faster, and some of that's on us, not just the market.
>
> **Agent:** Okay, so what's going on now?
>
> **Customer:** We went live on a new ERP six weeks ago. It's been rough. My reps are still relearning how to log a basic quote.
>
> **Agent:** How rough are we talking — day-to-day-annoying, or actually blocking people from doing their jobs?
>
> **Customer:** Somewhere in between. Nobody's stuck, but everyone's slower, and morale's a little fried. Adding a second new system on top of that would be a mistake, and I think you'd agree if you saw the Slack channel right now.
>
> **Agent:** I would agree. Rolling out two platforms on top of each other usually guarantees neither one sticks. When do you expect the ERP dust to settle?
>
> **Customer:** Realistically? Sixteen weeks. Maybe twelve if we're lucky.
>
> **Agent:** Is the interest still there for after that, or did the ERP pain sour the whole idea of adding tools?
>
> **Customer:** Still there. If anything the ERP mess made it clearer we need something that actually works when we do add it.
>
> **Agent:** Glad it's not soured, just delayed. Would it help to lock in pricing now so you're not renegotiating from scratch in four months?
>
> **Customer:** Maybe. I don't want to commit to a timeline I can't hit, though. ERP rollouts have a way of eating every projection I make.
>
> **Agent:** No argument there — let's not pin you to a date you'll regret. What if I check back in ten weeks instead of holding you to twelve or sixteen?
>
> **Customer:** That's better. Less pressure, and by then I'll actually know where we stand.
>
> **Agent:** I'll put a note to reach out then. In the meantime, want me to send anything, or is your inbox better left alone during all this?
>
> **Customer:** Leave it alone, honestly. I'll remember you when I'm ready — this wasn't a hard no, just bad timing.
>
> **Agent:** That tracks. Better to come back ready than half-checked-out right now anyway.
>
> **Customer:** Appreciate that. Talk in ten weeks.

Turns: 20 (10 Agent / 10 Customer). Word count: 401 (Agent 201 / Customer 200).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 210 |
| `agent_performance_score` | 4 |
| `objection_handling_quality` | 4 |
| `lead_quality_score` | 3 |
| `call_category` | Follow-up Needed |
| `next_meeting_scheduled` | true |
| `silence_ratio` | 0.16 |
| `speaking_rate_wpm` | 115 |
| `speech_to_non_speech_ratio` | 0.84 |
| `agent_talk_ratio` | 0.50 |
| `average_energy_level` | low |
| `price_mentions_count` | 1 |
| `competitor_mentions_count` | 1 |
| `manager_notes` | Customer remains genuinely interested but is mid-rollout on a new ERP system that has strained team capacity; adding a second new tool now was judged too high-risk for adoption. Agent agreed to a ten-week check-in instead of pressing for a shorter timeline, and the customer asked not to be contacted in the interim. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (medium) — engaged and explicit that interest hasn't soured, but not signaling readiness to move now.
- ✓ transcript supports `main_objection` (timing) — the entire blocker is a six-week-old ERP rollout that has "strained team capacity," not any doubt about the product itself.
- ✓ transcript supports `customer_sentiment` (neutral) — even-keeled and businesslike throughout, including the dry "I think you'd agree if you saw the Slack channel right now."
- ✓ transcript supports `sale_result` (Follow-up Needed) — no decision made; a specific ten-week check-in is agreed instead.
- ✓ transcript supports `follow_up_needed` (true) — explicit ten-week check-in commitment from the agent.
- ✓ transcript supports `closing_attempt` (medium) — agent proposes locking in pricing and a check-in cadence, but makes no direct ask for a signature, appropriately given the stated timing constraint.
- ✓ `manager_notes` grounded — the ERP rollout, six-week timeframe, and ten-week check-in are all stated in the transcript.
- ✓ audio features realistic — 210s duration, 115 wpm, and an even 0.50 agent talk ratio consistent with a calm, balanced, unhurried exchange.
- ✓ no Ground Truth violations.

---

## CALL_012

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_012 |
| `agent_name` | Daniel Cohen |
| `customer_segment` | Enterprise |
| `industry` | Technology |
| `company_size` | ~1,300 |
| `sale_result` | Follow-up Needed |
| `customer_intent` | medium |
| `main_objection` | competitor |
| `customer_sentiment` | mixed |
| `follow_up_needed` | true |
| `closing_attempt` | strong |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Diane Kowalski, Head of Revenue Operations at an enterprise tech company. Measured, procedurally fair, quietly candid about her personal preference when it's safe to be.

> **Agent:** Diane, thanks for making time. I know you're running this as a formal evaluation — where are things at with the other vendors?
>
> **Customer:** Two others in the mix besides you. We're scoring all three against the same rubric before anyone on my team is allowed to have a favorite, at least officially.
>
> **Agent:** Unofficially?
>
> **Customer:** Unofficially, you're ahead. The workflow automation piece is exactly what my ops team's been asking for. I just can't say that in the steering committee meeting.
>
> **Agent:** I'll take unofficially-ahead. What does the rubric actually weigh?
>
> **Customer:** Implementation timeline, integration depth, total cost of ownership over three years, and vendor stability. Pretty standard enterprise stuff.
>
> **Agent:** Where do you think we're weakest on that list, honestly?
>
> **Customer:** Vendor stability, maybe. You're smaller than the other two, and someone on the committee always asks "what if they get acquired or go under."
>
> **Agent:** Is that the biggest thing holding the committee back, or is there something else lurking under the surface?
>
> **Customer:** Honestly, some of it's just switching-cost anxiety in general. We've been burned before rolling out a platform that promised the world and underdelivered. Nobody wants to be the one who championed the next disappointment.
>
> **Agent:** Worth taking seriously, both of those. We can get you customer references at your scale, our financials summary, and roadmap commitments in writing, if that helps.
>
> **Customer:** That would help. Can you get me the references by next week? The committee meets in three weeks and I want ammunition before then, not after.
>
> **Agent:** I'll have three reference contacts to you by Wednesday. Given everything else you've said, is there anything blocking a strong recommendation from you specifically, or is it purely the process now?
>
> **Customer:** Purely the process, mostly. Between us, if it were just my call, we'd already be moving forward.
>
> **Agent:** Then let's make sure the committee sees what you're seeing. Can I get fifteen minutes with them directly, even briefly, before the final scoring?
>
> **Customer:** I can push for that. No guarantees, but I'll try to get you on the agenda for the pre-read session.
>
> **Agent:** That's the ask — get me in the room before the decision's made, not after.
>
> **Customer:** I hear you. I want this to land too, for what it's worth. I just can't shortcut a process I helped design.
>
> **Agent:** I wouldn't ask you to. I'll have the references and roadmap doc to you by Wednesday, and follow up once you know if I've got that fifteen minutes.
>
> **Customer:** Sounds good. I'll know more after our internal sync Thursday.

Turns: 20 (10 Agent / 10 Customer). Word count: 429 (Agent 193 / Customer 236).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 235 |
| `agent_performance_score` | 5 |
| `objection_handling_quality` | 4 |
| `lead_quality_score` | 4 |
| `call_category` | High-Value Opportunity |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.15 |
| `speaking_rate_wpm` | 110 |
| `speech_to_non_speech_ratio` | 0.85 |
| `agent_talk_ratio` | 0.45 |
| `average_energy_level` | medium |
| `price_mentions_count` | 2 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Enterprise account running a formal three-vendor evaluation against a scoring rubric (implementation timeline, integration depth, three-year TCO, vendor stability). Customer champion is unofficially favorable but bound by the committee process; vendor stability and general switching-cost anxiety were raised as the main concerns. Agent is providing references, financials, and a roadmap document by Wednesday, and requested time with the steering committee before final scoring — not yet confirmed. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (medium) — clearly favorable ("if it were just my call, we'd already be moving forward") but bound by a process she can't personally override.
- ✓ transcript supports `main_objection` (competitor) — the entire call is framed around a three-vendor bake-off with a shared scoring rubric, explicitly a comparison-stage evaluation rather than a replacement of a broken incumbent.
- ✓ transcript supports `customer_sentiment` (mixed) — genuine enthusiasm ("unofficially, you're ahead") mixed with real caution (vendor-stability worry, "switching-cost anxiety," "nobody wants to be the one who championed the next disappointment").
- ✓ transcript supports `sale_result` (Follow-up Needed) — no decision is possible until the committee scores all three vendors in three weeks.
- ✓ transcript supports `follow_up_needed` (true) — explicit Wednesday deliverable and a pending request for committee access before final scoring.
- ✓ transcript supports `closing_attempt` (strong) — direct, specific ask: "Can I get fifteen minutes with them directly... before the final scoring?" even though the process constrains what it can achieve.
- ✓ `manager_notes` grounded — the rubric categories, three-week committee timeline, Wednesday deliverable, and pending pre-read-session request are all stated in the transcript.
- ✓ audio features realistic — 235s duration, 110 wpm, and a lower 0.45 agent talk ratio consistent with a customer doing much of the explaining about her internal process.
- ✓ no Ground Truth violations.

---

## Summary of the four calls

| Call ID | Agent | Outcome | Objection | Intent | Sentiment | Agent Score | Contrast Case |
|---|---|---|---|---|---|---|---|
| CALL_009 | Daniel Cohen | No Sale | price | high | mixed | 5 | Case 2 + Case 7 (vs. CALL_007) |
| CALL_010 | Daniel Cohen | No Sale | authority | medium | neutral | 4 | Case 8 (vs. CALL_004) |
| CALL_011 | Daniel Cohen | Follow-up Needed | timing | medium | neutral | 4 | — |
| CALL_012 | Daniel Cohen | Follow-up Needed | competitor | medium | mixed | 5 | — |

This batch completes Daniel Cohen's six-call allocation (CALL_007–CALL_012) and brings the total corpus to 12 of 24 planned rows — exactly halfway, with all four Sarah Levi and Daniel Cohen calls now drafted.

## QA summary

- All four transcripts land at exactly 20 turns (10 Agent / 10 Customer) and within the 350–700 word range (478, 423, 401, 429) — verified by `wc`/`grep`, not estimated.
- A literal-string banned-phrase check caught and fixed a real issue: an earlier draft reused "I'd rather ... than ..." as Daniel Cohen's closing-empathy line in three of the four calls (CALL_009, CALL_010, CALL_011). All three were rewritten to distinct phrasing before finalizing; a follow-up grep confirmed zero remaining matches against all eight banned templates.
- Two secondary near-repeats ("Makes sense," "That works") surfaced across CALL_009–CALL_011 in a second pass and were varied further, even though neither was on the explicit banned list — consistent with the guideline's broader intent, not just its letter.
- `agent_talk_ratio` (0.46, 0.54, 0.50, 0.45) and `speaking_rate_wpm` (125, 110, 115, 110) were computed from each transcript's actual verified word count and speaker split, all within dataset_design.md §11's realistic ranges.
- `price_mentions_count` (5, 0, 1, 2) and `competitor_mentions_count` (0, 0, 1, 0) were counted directly from final transcript text — highest in CALL_009 (the price-objection call), zero in CALL_010 (a pure authority/committee-process call with no price discussion).
- Four distinct customer voices: Renee (CALL_009) is warm and emotionally transparent; David (CALL_010) is an energetic internal champion who over-explains committee politics; Carla (CALL_011) is calm, brief, and dryly funny; Diane (CALL_012) is measured and procedurally careful. None share sentence rhythm, acknowledgment words, or closing style.
- CALL_012 deliberately avoids CALL_008's "replacement" narrative (a painful incumbent with a known technical failure) in favor of an "evaluation" narrative (a formal multi-vendor rubric-scored bake-off with no incumbent pain described) — per this batch's explicit instruction.

## Confirmation that Ground Truth Rules were respected

- Every structured field is directly supported by that call's transcript text, verified per-call in each Ground Truth validation checklist above.
- `manager_notes` in all four rows restate only what the transcript contains — no invented budgets, dates, names, or outcomes beyond what's stated (e.g. CALL_009's $25K figure is arithmetic on numbers the customer herself gives, not an invented one).
- CALL_009 and CALL_010 correctly stay at `No Sale` despite high agent performance, consistent with the independence of `agent_performance_score` from `sale_result` established in `dataset_design.md` §9 — neither is forced toward a softer label to make the agent "look better."
- Contrast Cases 2, 7, and 8 are each verified explicitly in their respective Ground Truth checklists above, referencing the specific transcript evidence that satisfies them, not just the matrix's plan.

---

**Batch 4 (Michael Ben-David's calls — CALL_013 through CALL_018, including Contrast Cases 3 and 6) has not been started.** No CSV files have been generated in this sub-phase.
