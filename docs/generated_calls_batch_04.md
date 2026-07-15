# XSight — Generated Historical Calls, Batch 4 (Phase 5B.1)

**Status: draft transcripts and full row content for CALL_013–CALL_018 only. No CSV files generated in this sub-phase.** This document authors the full historical-call record for the next six rows of `data/historical_sales_calls.csv`, strictly following the frozen assignments in [docs/historical_call_matrix.md](historical_call_matrix.md), the schema in [docs/dataset_design.md](dataset_design.md) §14, and the [Transcript Writing Guidelines](../CLAUDE.md#transcript-writing-guidelines). No matrix assignment was changed.

This batch is Michael Ben-David's full six-call allocation and includes Contrast Case 6 (CALL_014) — the most consequential single row in the corpus, since it's the only row required to prove that `agent_performance_score` and `sale_result` are independent axes in the *successful* direction (Case 5, CALL_003, proved the reverse: strong performance in a failed call). A literal-string check against the eight banned templates caught two real hits on the first pass — "Can I ask" in CALL_016 and "I'd rather ... than ..." in CALL_017 (a customer line this time, not the agent) — both fixed before finalizing, along with five secondary near-repeats ("Makes sense," "Good to know," "That's useful") that weren't on the banned list but were trending toward corpus-wide overuse.

---

## CALL_013

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_013 |
| `agent_name` | Michael Ben-David |
| `customer_segment` | Enterprise |
| `industry` | Technology |
| `company_size` | ~1,800 |
| `sale_result` | Sale |
| `customer_intent` | high |
| `main_objection` | security |
| `customer_sentiment` | positive |
| `follow_up_needed` | false |
| `closing_attempt` | medium |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Sandra Kim, VP of Engineering at an enterprise technology company. Direct, already technically satisfied, seeking executive-level confidence rather than checklist reassurance.

> **Agent:** Sandra, thanks for jumping on. I know your team already ran the technical review — what's actually still open for you personally before this moves forward?
>
> **Customer:** Nothing technical, honestly. My security engineers cleared you two weeks ago — SOC 2, encryption, the works. I just haven't signed off myself yet.
>
> **Agent:** What's holding that back, if it's not the technical side?
>
> **Customer:** Scale, mostly. We'd be rolling this out to our whole sales org — twelve hundred people. If something goes wrong at that scale, it's my name on the recommendation, not just my security team's checklist.
>
> **Agent:** Reasonable, wanting more than a checklist for something this size. What would actually give you that confidence?
>
> **Customer:** Track record, honestly. Have you had a security incident at an account our size? And if so, what actually happened when it did?
>
> **Agent:** We had one two years ago — a misconfigured permission on a customer instance, not a breach, but data was briefly viewable that shouldn't have been. We caught it in four hours, notified the customer within the SLA, and rebuilt our permission-review process because of it.
>
> **Customer:** Rare that a vendor admits that instead of dodging it. What changed afterward, specifically?
>
> **Agent:** Automated permission audits now run daily instead of on request, and every account over five hundred seats gets a dedicated security contact, not a shared support queue. You'd be one of those accounts.
>
> **Customer:** That's the kind of answer that actually helps. What about longer term — is security something that gets real investment, or is it treated as a cost center once the deal's signed?
>
> **Agent:** Roughly a fifth of our engineering headcount sits on security and infrastructure specifically, and that's grown every year, not shrunk. I can get you our last two annual security investment summaries if that helps make the case internally.
>
> **Customer:** It would. My CISO's going to ask, even if I don't.
>
> **Agent:** I'll have both to you today. If something ever did go wrong on our side after you're live, what would you actually need from us in the first hour?
>
> **Customer:** Direct access to a real person, not a ticket number. Somebody who can tell me what happened and what we should tell our own customers.
>
> **Agent:** You'd have a named escalation contact and a direct line, not a support queue, specifically because of the scale of this rollout.
>
> **Customer:** Okay. Honestly, that covers it for me. I was mostly looking for someone who'd tell me the truth instead of a perfect record that doesn't exist anywhere.
>
> **Agent:** Given where we've landed, what's left before you're comfortable signing off?
>
> **Customer:** Nothing. I'll get this to procurement today — twelve hundred seats, effective next quarter.
>
> **Agent:** I'll send the security investment summaries and the named escalation contact details this afternoon so you've got everything for your CISO.
>
> **Customer:** Appreciate it. This was a more honest conversation than I expected going in.

Turns: 20 (10 Agent / 10 Customer). Word count: 485 (Agent 261 / Customer 224).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 245 |
| `agent_performance_score` | 5 |
| `objection_handling_quality` | 5 |
| `lead_quality_score` | 5 |
| `call_category` | High-Value Opportunity |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.12 |
| `speaking_rate_wpm` | 119 |
| `speech_to_non_speech_ratio` | 0.88 |
| `agent_talk_ratio` | 0.54 |
| `average_energy_level` | medium |
| `price_mentions_count` | 1 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer's technical team had already cleared security review two weeks prior; this call was about executive-level confidence given a 1,200-seat rollout, not unresolved technical concerns. Agent disclosed a past minor security incident (misconfigured permission, no breach, four-hour resolution) and the process changes that followed, and committed to a named escalation contact given the account's scale. Customer is submitting to procurement today. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (high) — explicit sign-off and same-day procurement submission for 1,200 seats.
- ✓ transcript supports `main_objection` (security) — the entire call is about security confidence, but framed at an executive/track-record level, not a line-item technical checklist.
- ✓ transcript supports `customer_sentiment` (positive) — closes with "a more honest conversation than I expected going in."
- ✓ transcript supports `sale_result` (Sale) — explicit "I'll get this to procurement today — twelve hundred seats, effective next quarter."
- ✓ transcript supports `follow_up_needed` (false) — the decision is made; remaining items (documents, escalation contact details) are delivery, not an open question.
- ✓ transcript supports `closing_attempt` (medium) — agent asks what's left before sign-off rather than directly asking for a signature, appropriate since the customer was already driving toward a decision.
- ✓ `manager_notes` grounded — the prior incident, its resolution timeline, the process changes, and the named escalation contact are all stated in the transcript.
- ✓ audio features realistic — 245s duration, 119 wpm, consistent with a measured, confident executive conversation.
- ✓ no Ground Truth violations. Deliberately distinct from CALL_006: no line-item compliance checklist, no non-buyer technical vetter — a decision-maker seeking confidence, not clearance.

---

## CALL_014 — Contrast Case 6 (Critical)

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_014 |
| `agent_name` | Michael Ben-David |
| `customer_segment` | Mid-Market |
| `industry` | Healthcare |
| `company_size` | ~260 |
| `sale_result` | Sale |
| `customer_intent` | high |
| `main_objection` | timing |
| `customer_sentiment` | positive |
| `follow_up_needed` | false |
| `closing_attempt` | weak |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Priya Malhotra, VP of Sales at a mid-market healthcare company. Decisive, already sold before the call, visibly steering the conversation back on track when the agent drifts.

> **Agent:** Priya, thanks for hopping on. So, tell me a little about your team and what's got you looking at a platform like this.
>
> **Customer:** I'll be honest, we're past the "looking" stage. My VP of Ops already piloted this with two other vendors last quarter, we picked you, budget's approved. I'm really just here to finalize details.
>
> **Agent:** Great, great. Well, let me walk you through what makes our platform different — we've got a full analytics suite, AI-driven lead scoring, CRM integrations across the major providers, a mobile app for reps in the field —
>
> **Customer:** I've seen the demo, Michael. Twice, actually. What I need to know is start date and contract terms.
>
> **Agent:** Right, of course. The analytics suite is actually one of the pieces I think you'll get the most value from, especially with a team your size —
>
> **Customer:** I'm sure it's great. Start date?
>
> **Agent:** We can typically get an account live within two to three weeks of signature, depending on data migration complexity.
>
> **Customer:** Okay, and can that happen before our open enrollment period starts? That's the actual constraint here — everything needs to be running by the fifteenth.
>
> **Agent:** Sure, migration's usually pretty smooth. We've got a whole onboarding team, dedicated support, training materials, a knowledge base —
>
> **Customer:** Michael. Can it be live by the fifteenth or not?
>
> **Agent:** I believe so, yeah. I mean, it depends a bit on your data, but generally two to three weeks is typical, so it should work out.
>
> **Customer:** "Should" isn't really what I need to hear before I sign something with a hard deadline attached to it.
>
> **Agent:** No, no, you're right. Let me actually check on that instead of guessing — I'll confirm with our onboarding team today and get you a real answer, not just typical timelines.
>
> **Customer:** That would help, thank you. What about pricing at our seat count — is there a discount, or is that a separate conversation?
>
> **Agent:** So at your seat count you'd actually qualify for our mid-market tier, which includes the analytics suite I mentioned, plus priority support, plus —
>
> **Customer:** Is there a discount or not?
>
> **Agent:** Yes — twelve percent off list price for annual commitment at your tier.
>
> **Customer:** Good. Send me the contract with that pricing and I'll get it in front of finance today.
>
> **Agent:** I can do that. I'll also send over some case studies from similar healthcare accounts, just so you have context on how other teams have used the analytics features —
>
> **Customer:** I don't need the case studies, Michael. Just the contract and a real answer on the fifteenth.
>
> **Agent:** Will do — contract today, onboarding timeline confirmed by tomorrow.
>
> **Customer:** Perfect. I already told finance to expect this, so the faster the better.

Turns: 22 (11 Agent / 11 Customer). Word count: 458 (Agent 262 / Customer 196).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 200 |
| `agent_performance_score` | 2 |
| `objection_handling_quality` | 2 |
| `lead_quality_score` | 5 |
| `call_category` | Coaching Required |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.08 |
| `speaking_rate_wpm` | 137 |
| `speech_to_non_speech_ratio` | 0.92 |
| `agent_talk_ratio` | 0.57 |
| `average_energy_level` | medium |
| `price_mentions_count` | 4 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer had already selected this platform internally before the call — budget approved, team piloted competing tools, decision made. Agent repeatedly pitched unrequested features (analytics suite, mobile app, case studies) instead of directly answering the customer's specific questions on start date and pricing, and gave a vague, unverified answer on a hard enrollment deadline before the customer had to push back twice for a real one. The sale closed because the opportunity was already fully qualified, not because of strong execution on this call — flagged for coaching on discovery listening and unprompted feature-dumping. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (high) — states outright in the first response that the decision is already made and budget is approved.
- ✓ transcript supports `main_objection` (timing) — the one real constraint raised is a hard enrollment deadline (the fifteenth), which the agent initially fails to answer with any certainty.
- ✓ transcript supports `customer_sentiment` (positive) — impatient with the agent's pitching, but never negative about the product itself; closes warmly ("Perfect... the faster the better").
- ✓ transcript supports `sale_result` (Sale) — explicit "Send me the contract... I already told finance to expect this."
- ✓ transcript supports `follow_up_needed` (false) — the sale decision itself was never in question; remaining items are delivery of a contract and a timeline confirmation.
- ✓ transcript supports `closing_attempt` (weak) — the agent never once asks for the sale; the customer is the one who says "Send me the contract." This is a *more* passive close than the taxonomy's baseline weak example, not a borderline case.
- ✓ `manager_notes` grounded — the prior pilot, approved budget, the deadline exchange, and the discount percentage are all stated in the transcript, not invented.
- ✓ audio features realistic — 200s duration, 137 wpm, and a low 0.08 silence ratio consistent with a fast-paced call full of interruptions and redirections rather than natural pauses.
- ✓ no Ground Truth violations.

**Contrast Case 6 — explicit verification against every stated requirement:**

| Requirement | How the transcript satisfies it |
|---|---|
| Sale outcome | Customer sends the contract to finance same day. |
| Weak agent performance / low `agent_performance_score` | Score = 2. Agent pitches unrequested features three separate times (turns 3, 5, 9) after the customer has already signaled she doesn't need them. |
| Weak objection handling | On the one real objection (hard deadline), agent's first answer is a hedge ("I believe so... should work out") — customer has to say "'Should' isn't really what I need to hear" before he agrees to actually verify instead of guess. |
| Weak closing | Agent never asks for the sale. The customer initiates "Send me the contract" unprompted. |
| Customer already highly qualified pre-call | Stated in her first line: prior pilot completed, vendor already selected, budget already approved — before Michael says anything substantive. |
| Buying decision existed before the call | Same as above — this call is bureaucratic finalization from the customer's side, not persuasion. |
| Agent misses opportunities | Never asks a single discovery or confirming question of his own; every question in the call is asked *by the customer*, redirecting *him*. |
| Agent over-talks | Three unprompted feature pitches, each interrupted or redirected by the customer before he finishes. |
| Agent explains unnecessary things | Analytics suite, mobile app, and case studies are pitched despite the customer stating upfront she's seen the demo twice and doesn't need them. |
| Agent asks weaker questions | His only real question — "tell me about your team and what's got you looking at a platform like this" — is generic discovery, asked to a customer who just said she's already decided. He never adjusts the question to her actual stated situation. |
| Deal succeeds despite the agent | The lead-quality/opportunity strength (already-approved budget, already-completed pilot, already-selected vendor) is the only reason this closes; nothing in the agent's execution contributed to the outcome. |
| Not incompetent, not a caricature | Agent answers substantive questions correctly when directly pinned down (2–3 week migration is real, 12% discount is a real, specific number, not evasive), stays polite throughout, and does course-correct on the deadline question once challenged — a real but underperforming rep, not a cartoon. |
| Customer doesn't unrealistically "rescue" the call | She simply does what any decisive, busy buyer does — redirects twice, states her actual questions plainly, and finalizes. She never explains the product back to him, never does his job for him, and never expresses forced enthusiasm to compensate. |

---

## CALL_015 — Contrast Case 2 (primary)

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_015 |
| `agent_name` | Michael Ben-David |
| `customer_segment` | Mid-Market |
| `industry` | Retail |
| `company_size` | ~190 |
| `sale_result` | No Sale |
| `customer_intent` | high |
| `main_objection` | price |
| `customer_sentiment` | mixed |
| `follow_up_needed` | false |
| `closing_attempt` | medium |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Greg Alvarez, Director of Retail Operations at a mid-market retail chain. Analytical, transparent about his own team's math, genuinely disappointed rather than defensive.

> **Agent:** Greg, thanks for making time. Last we spoke you seemed pretty into this — what's the latest on your end?
>
> **Customer:** We're still into it, genuinely. My team ran their own numbers though, and I wanted to talk you through where we landed before I give you a final answer.
>
> **Agent:** Before we get into the math — what's actually resonated most for your team in the eval?
>
> **Customer:** The markdown-timing alerts, honestly. We lose more margin to bad markdown timing than almost anything else. That part sold itself.
>
> **Agent:** Glad to hear that landed. So what did the numbers say?
>
> **Customer:** We opened a third location last spring. Still absorbing that cost — new leases, new inventory, new hires. Our finance team modeled the platform's ROI against our current cash position, and the payback period came out to around fourteen months.
>
> **Agent:** What's the threshold your finance team's working with?
>
> **Customer:** Anything past nine months this year gets a hard no. It's not a permanent rule, it's specific to where we are right now with the third store still bleeding cash.
>
> **Agent:** Is fourteen months close to right, or is there room to challenge that model?
>
> **Customer:** Probably close. We were conservative on the upside assumptions on purpose, given everything else going on. I didn't want to walk in here with rosy numbers and get burned later.
>
> **Agent:** Reasonable way to model it, honestly. Is there a version of this — fewer seats, a phased rollout — that gets the payback period under nine months?
>
> **Customer:** We looked at that. Fewer seats doesn't really work, our use case needs the whole retail team using it or the data's incomplete anyway.
>
> **Agent:** What about deferring the start date instead of the seat count — starting once the third store's numbers stabilize?
>
> **Customer:** That's actually more realistic. Problem is I don't have a clean date for "stabilized." Could be six months, could be a year if this quarter's rough.
>
> **Agent:** I don't want to sell you something your own finance team already modeled as a bad bet right now. Would it help if I sent over the ROI model with a note that pricing holds for six months, so you're not renegotiating from zero later?
>
> **Customer:** That would help, actually. I liked this a lot more than the number suggests — it's genuinely not a fit issue, it's a cash-timing issue.
>
> **Agent:** For what it's worth, the product isn't going anywhere, and neither is the price lock if you come back inside that window.
>
> **Customer:** I appreciate that you didn't try to talk me out of my own numbers.
>
> **Agent:** Wouldn't have gotten anywhere anyway — you clearly did the work. I'll send the model and the pricing note today.
>
> **Customer:** Thanks. Genuinely wish the timing on the third store had worked out differently.

Turns: 20 (10 Agent / 10 Customer). Word count: 466 (Agent 207 / Customer 259).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 245 |
| `agent_performance_score` | 5 |
| `objection_handling_quality` | 5 |
| `lead_quality_score` | 4 |
| `call_category` | Failed Sale |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.17 |
| `speaking_rate_wpm` | 114 |
| `speech_to_non_speech_ratio` | 0.83 |
| `agent_talk_ratio` | 0.44 |
| `average_energy_level` | medium |
| `price_mentions_count` | 4 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer's own finance team modeled the platform's ROI at a 14-month payback period against a 9-month internal threshold, driven by cash constraints from a recent third-location opening — a deliberate, well-reasoned internal decision, not price resistance to the product itself. Agent offered a deferred-start option and a six-month price lock rather than pushing against the customer's own financial model. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (high) — proactively walks the agent through internal financial modeling rather than going quiet or ghosting.
- ✓ transcript supports `main_objection` (price) — the entire call is a transparent walkthrough of a payback-period calculation against an internal budget threshold.
- ✓ transcript supports `customer_sentiment` (mixed) — genuine enthusiasm ("that part sold itself," "I liked this a lot more than the number suggests") alongside real disappointment ("genuinely wish the timing... had worked out differently").
- ✓ transcript supports `sale_result` (No Sale) — the customer's own finance-modeled 14-month payback period exceeds their 9-month threshold; no override found in the call.
- ✓ transcript supports `follow_up_needed` (false) — no concrete return date is set, only an open six-month pricing window.
- ✓ transcript supports `closing_attempt` (medium) — agent proposes concrete alternatives (deferred start, price lock) without asking for any commitment now, appropriate given the customer's own math rules it out.
- ✓ `manager_notes` grounded — the third-location cost, the 14-month/9-month figures, and the six-month price lock are all stated in the transcript.
- ✓ audio features realistic — 245s duration, 114 wpm, and a lower 0.44 agent talk ratio consistent with a customer-led, numbers-heavy conversation.
- ✓ no Ground Truth violations. **Contrast Case 2 verified (primary instance):** price objection is the deciding factor in a `No Sale`, driven by the customer's own internal ROI modeling rather than an external freeze (as in CALL_009) — a different, deliberate business reason.

---

## CALL_016 — Contrast Case 4 (reinforcing)

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_016 |
| `agent_name` | Michael Ben-David |
| `customer_segment` | SMB |
| `industry` | Professional Services |
| `company_size` | ~30 |
| `sale_result` | No Sale |
| `customer_intent` | low |
| `main_objection` | no_need |
| `customer_sentiment` | negative |
| `follow_up_needed` | false |
| `closing_attempt` | none |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Frank DeLuca, Managing Partner at a small architecture firm. Gruff, dismissive, taking the call only as a favor — genuinely convinced there's no problem to solve.

> **Agent:** Frank, thanks for taking the call. I know you're busy — what's your team currently using to track new client inquiries and project pipeline?
>
> **Customer:** We use a whiteboard in the conference room. Has for fifteen years. Works fine.
>
> **Agent:** What happens when two people need to update it at the same time, or someone's out of office?
>
> **Customer:** Somebody writes it down and updates the board when they're back. It's not complicated. We're an architecture firm, not a call center.
>
> **Agent:** The scale's obviously different there. Have you ever lost track of a lead because the board wasn't updated in time?
>
> **Customer:** Maybe once or twice in fifteen years. I'm not going to buy software over "once or twice."
>
> **Agent:** That's a reasonable bar. What made you take this call at all, then?
>
> **Customer:** My daughter set it up. She handles our marketing, thinks we need to "modernize." I told her I'd take one call to make her happy.
>
> **Agent:** I appreciate the honesty. Is there anything about how the firm runs day to day that actually frustrates you, even if it's not pipeline-related?
>
> **Customer:** Not really. Thirty people, we all know each other, projects come through referrals mostly. It's not broken.
>
> **Agent:** If nothing's broken, I'm not going to try to convince you it is. What does your daughter think the actual gap is?
>
> **Customer:** Reporting, probably. She wants numbers for some pitch deck she's building. I don't really care about the numbers, honestly, I care about the buildings.
>
> **Agent:** That's a normal split of priorities to have. Is she the one who'd actually use this day to day, or would that fall on you too?
>
> **Customer:** Her, mostly. If she wants a tool for her reporting thing, that's a smaller ask than replacing how the whole firm tracks work.
>
> **Agent:** Worth knowing — sounds like the real conversation might be a lighter reporting tool for her specifically, not a full pipeline platform for the firm.
>
> **Customer:** Maybe. I'm not signing up for anything today either way.
>
> **Agent:** I'm not asking you to. If she wants to look at something smaller and more targeted for her own reporting, have her reach out directly and I'll talk to her about that instead.
>
> **Customer:** Fine, I'll tell her. Wasn't expecting you to just let it go instead of pushing the full pitch.
>
> **Agent:** That's not what this firm needs right now, from what you've described. No hard sell here.
>
> **Customer:** Good. That's more than I expected from one of these calls.

Turns: 20 (10 Agent / 10 Customer). Word count: 420 (Agent 229 / Customer 191).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 200 |
| `agent_performance_score` | 3 |
| `objection_handling_quality` | 2 |
| `lead_quality_score` | 1 |
| `call_category` | Failed Sale |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.14 |
| `speaking_rate_wpm` | 126 |
| `speech_to_non_speech_ratio` | 0.86 |
| `agent_talk_ratio` | 0.55 |
| `average_energy_level` | low |
| `price_mentions_count` | 0 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer's firm runs on a 15-year-old manual whiteboard process and genuinely does not see a problem worth solving; the call was taken as a favor to his daughter, who handles marketing and wanted a lighter reporting tool for her own use, not a full pipeline platform for the firm. Agent correctly avoided pushing a broader sale onto a lead with no genuine need, and redirected toward a smaller, more relevant follow-up (the daughter reaching out about a reporting-focused tool). |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (low) — minimal engagement, took the call "to make her happy," never asks a real question about the product himself.
- ✓ transcript supports `main_objection` (no_need) — explicit, repeated: "it's not complicated," "not broken," "once or twice in fifteen years."
- ✓ transcript supports `customer_sentiment` (negative) — gruff and mildly irritated throughout ("We're an architecture firm, not a call center"), though not hostile.
- ✓ transcript supports `sale_result` (No Sale) — no interest expressed in the product for the firm itself at any point.
- ✓ transcript supports `follow_up_needed` (false) — no concrete follow-up committed on Frank's side; only an open invitation for his daughter to reach out separately.
- ✓ transcript supports `closing_attempt` (none) — agent never proposes any next step for Frank himself, only redirects toward a different person for a different, smaller product fit.
- ✓ `manager_notes` grounded — the whiteboard process, the daughter's role, and the reporting-tool redirect are all stated in the transcript.
- ✓ audio features realistic — 200s duration, 126 wpm, consistent with a short, low-energy, low-engagement call.
- ✓ no Ground Truth violations. **Contrast Case 4 verified (reinforcing instance):** low intent driving `No Sale`, via `no_need` rather than CALL_004's `trust` — a different personality (gruff/dismissive vs. flat/skeptical) and a different underlying reason (genuine complacency with an existing process vs. distrust of vendor claims).

---

## CALL_017

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_017 |
| `agent_name` | Michael Ben-David |
| `customer_segment` | Enterprise |
| `industry` | Manufacturing |
| `company_size` | ~1,100 |
| `sale_result` | Follow-up Needed |
| `customer_intent` | medium |
| `main_objection` | authority |
| `customer_sentiment` | neutral |
| `follow_up_needed` | true |
| `closing_attempt` | medium |
| `decision_maker_present` | false |

### 2. Transcript

Customer: Kenji Watanabe, Sales Enablement Manager at an enterprise manufacturer. Practical, mildly wry about internal bureaucracy, clearly frustrated by the specific blocker rather than the product.

> **Agent:** Kenji, thanks for hopping on. Where are things at since we last talked?
>
> **Customer:** Good news and annoying news. Good news, everyone who'd actually use this loves it. Annoying news, the only person who can approve it is out.
>
> **Agent:** Out how — vacation, or something longer?
>
> **Customer:** Parental leave. Three weeks in, three more to go. She's our VP of Ops and anything over our threshold needs her signature specifically, not a delegate.
>
> **Agent:** No delegate at all while she's out?
>
> **Customer:** None for purchasing, oddly. Delegates cover ops decisions, not spend approval. It's a gap in our policy, honestly, one I've flagged before.
>
> **Agent:** What's actually driving the enthusiasm on your team's side — what problem is this solving for them day to day?
>
> **Customer:** Quote follow-up, mostly. We've got twenty-some reps across three plants and nobody has visibility into who followed up on what. It's costing us renewals we shouldn't be losing.
>
> **Agent:** That's a specific kind of stuck, then — not a process you can work around, just a calendar you have to wait out.
>
> **Customer:** Exactly. I could get five VPs to co-sign a letter saying they want this and it still wouldn't count.
>
> **Agent:** How much runway do we actually have — is three weeks a hard number, or could it slip?
>
> **Customer:** Could slip. First week back is usually chaos for anyone returning from leave, so realistically I'd guess four weeks before she's even looking at anything like this.
>
> **Agent:** What can we get ready in the meantime so the moment she's back, this isn't starting from zero?
>
> **Customer:** Honestly, a short summary would help — she won't want to sit through a full pitch on day one back. Just the essentials and why my team's already bought in.
>
> **Agent:** I can put together a one-page brief — problem, solution, team sign-off, pricing — something she can read in five minutes.
>
> **Customer:** That's exactly what I need. I'll also give her a heads up before she's back so it's not a total surprise.
>
> **Agent:** Should I check in with you around the four-week mark, or wait for you to reach out once she's settled?
>
> **Customer:** Check in with me. I want to drive the timing, not have this go quiet for a month.
>
> **Agent:** I'll follow up in four weeks then, and have the one-pager to you well before that.
>
> **Customer:** Appreciate it. For what it's worth, this is the easiest "yes, but" I've had to deliver — everyone actually wants this.

Turns: 20 (10 Agent / 10 Customer). Word count: 412 (Agent 167 / Customer 245).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 215 |
| `agent_performance_score` | 4 |
| `objection_handling_quality` | 3 |
| `lead_quality_score` | 3 |
| `call_category` | Follow-up Needed |
| `next_meeting_scheduled` | true |
| `silence_ratio` | 0.15 |
| `speaking_rate_wpm` | 115 |
| `speech_to_non_speech_ratio` | 0.85 |
| `agent_talk_ratio` | 0.41 |
| `average_energy_level` | medium |
| `price_mentions_count` | 2 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Purchases above the customer's internal threshold require sign-off specifically from their VP of Operations, who is roughly three weeks into a six-week parental leave with no delegate authorized for spend approval — a personnel-availability gap, not a multi-stakeholder committee process. Team-level enthusiasm is high (quote-follow-up visibility across three plants). Agent is preparing a one-page brief for the VP's return and will check in at the four-week mark. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (medium) — team-level enthusiasm is clearly real, but Kenji himself has no purchasing authority, so intent reads as organizational rather than personal buying signal.
- ✓ transcript supports `main_objection` (authority) — a single named approver, out on leave, with explicitly no delegate for spend decisions.
- ✓ transcript supports `customer_sentiment` (neutral) — practical and cooperative, with dry frustration directed at the policy gap, not at the agent or product.
- ✓ transcript supports `sale_result` (Follow-up Needed) — nothing can be decided until the approver returns; a concrete plan exists but no decision.
- ✓ transcript supports `follow_up_needed` (true) — explicit four-week check-in and one-pager delivery commitment.
- ✓ transcript supports `closing_attempt` (medium) — agent moves the process forward (preparing materials, setting a check-in) without any ask for commitment, since none is possible until the approver returns.
- ✓ `manager_notes` grounded — the parental leave timeline, the delegate policy gap, and the quote-follow-up pain point are all stated in the transcript.
- ✓ audio features realistic — 215s duration, 115 wpm, and a lower 0.41 agent talk ratio consistent with a customer who does most of the explaining about internal process.
- ✓ no Ground Truth violations. Deliberately distinct from CALL_010 (a recurring quarterly cross-departmental committee) and CALL_003 (an informally hands-off owner): here the blocker is a single named approver's temporary unavailability with a specific return window, a structurally different kind of authority gap.

---

## CALL_018

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_018 |
| `agent_name` | Michael Ben-David |
| `customer_segment` | Enterprise |
| `industry` | Finance |
| `company_size` | ~1,600 |
| `sale_result` | Follow-up Needed |
| `customer_intent` | medium |
| `main_objection` | price |
| `customer_sentiment` | mixed |
| `follow_up_needed` | true |
| `closing_attempt` | weak |
| `decision_maker_present` | false |

### 2. Transcript

Customer: Elena Petrova, Senior Manager of Sales Operations at an enterprise finance company. Practical, a little worn down by procurement process, genuinely rooting for the outcome she can't fully control.

> **Agent:** Elena, thanks for jumping on. Where are we at on your end since the demo?
>
> **Customer:** Team loved it, for what that's worth. Pricing's the sticking point now, and honestly, that part's slower than I'd like.
>
> **Agent:** What's slow about it specifically?
>
> **Customer:** Sixteen hundred people company-wide, but we'd start with maybe four hundred seats in sales and CS. Our procurement policy requires three competitive quotes for anything over a certain contract value, and yours would clear that threshold easily.
>
> **Agent:** So this isn't really a "is the price too high" conversation, it's a "we're required to shop it" conversation?
>
> **Customer:** Pretty much. I already like your number better than what I'm expecting from the other two, honestly, but I can't skip the comparison even if I wanted to.
>
> **Agent:** What do the other two quotes typically look like, roughly, so I know what I'm actually being compared against?
>
> **Customer:** I don't have them yet, that's the annoying part. RFQ just went out this week. Probably three, four weeks before I've got all three numbers side by side.
>
> **Agent:** Is there anything I can do on our end to make that comparison easier once the other quotes land — a breakdown by seat tier, a multi-year discount structure, anything like that?
>
> **Customer:** A multi-year option would actually help. If you're meaningfully cheaper over three years than year-to-year, that's a real argument I can bring to the comparison.
>
> **Agent:** I can put together year-to-year and a three-year locked rate, side by side, so you've got both numbers ready when the others come in.
>
> **Customer:** That would help a lot, genuinely. I want this to win the comparison, I just can't rig it in your favor even if I could.
>
> **Agent:** I wouldn't want you to — that's not a comparison anyone trusts afterward. When do you expect to actually make the call, once all three quotes are in?
>
> **Customer:** Depends how close they are. If it's a landslide either way, fast. If it's close, it could sit with finance for a couple more weeks after that.
>
> **Agent:** Tracks with how these things usually go — the close calls tend to sit longer than the ones that aren't. I'll get you both pricing structures this week so they're ready whenever the comparison happens.
>
> **Customer:** Perfect. I'll loop you in as soon as I've got the other two numbers, or if finance asks me anything I can't answer myself.
>
> **Agent:** Sounds good. Anything else that typically trips up a pricing comparison like this, that I should get ahead of now instead of later?
>
> **Customer:** Implementation cost, sometimes. Make sure whatever you send includes onboarding fees up front, not as a footnote — last vendor buried it and it became a whole thing internally.
>
> **Agent:** Good catch, I'll make sure it's broken out clearly, not buried. I'll have both pricing structures to you by end of week.
>
> **Customer:** Appreciate it. Fingers crossed the comparison goes the way I'm hoping.

Turns: 20 (10 Agent / 10 Customer). Word count: 492 (Agent 229 / Customer 263).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 225 |
| `agent_performance_score` | 4 |
| `objection_handling_quality` | 4 |
| `lead_quality_score` | 3 |
| `call_category` | Follow-up Needed |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.13 |
| `speaking_rate_wpm` | 131 |
| `speech_to_non_speech_ratio` | 0.87 |
| `agent_talk_ratio` | 0.47 |
| `average_energy_level` | medium |
| `price_mentions_count` | 6 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Enterprise account requires three competitive quotes for any contract at this size per internal procurement policy; customer favors this platform but cannot skip the formal comparison. RFQ went out this week, with the other two quotes expected in three to four weeks. Agent is preparing year-to-year and three-year pricing structures and proactively flagged implementation-cost transparency, based on a prior vendor experience the customer described where onboarding fees were buried. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (medium) — favors this vendor personally but is explicit that her preference alone can't decide it.
- ✓ transcript supports `main_objection` (price) — the entire call is a formal, procurement-mandated price comparison, unresolved because the other two quotes don't exist yet.
- ✓ transcript supports `customer_sentiment` (mixed) — genuine enthusiasm ("Team loved it," "I want this to win") mixed with procedural weariness ("that part's slower than I'd like," "I can't rig it").
- ✓ transcript supports `sale_result` (Follow-up Needed) — literally cannot be decided until the RFQ comparison completes in three to four weeks.
- ✓ transcript supports `follow_up_needed` (true) — explicit pricing-structure deliverable this week and an open loop pending the other quotes.
- ✓ transcript supports `closing_attempt` (weak) — agent never asks for any commitment or signature; the entire call is preparatory material-gathering for a decision that isn't his to close.
- ✓ `manager_notes` grounded — the RFQ timeline, seat count, multi-year request, and the buried-fee complaint about a prior vendor are all stated in the transcript.
- ✓ audio features realistic — 225s duration, 131 wpm, consistent with a brisk, professional working conversation.
- ✓ no Ground Truth violations. Completes the price-objection set across all three outcomes (Sale: CALL_007; No Sale: CALL_009, CALL_015; Follow-up Needed: here) with a third distinct narrative — a mandated competitive-bid process, not a quantified reframe (CALL_007), an external freeze (CALL_009), or an internal ROI model (CALL_015).

---

## Summary of the six calls

| Call ID | Agent | Outcome | Objection | Intent | Sentiment | Agent Score | Contrast Case |
|---|---|---|---|---|---|---|---|
| CALL_013 | Michael Ben-David | Sale | security | high | positive | 5 | — |
| CALL_014 | Michael Ben-David | Sale | timing | high | positive | **2** | **Case 6 (critical)** |
| CALL_015 | Michael Ben-David | No Sale | price | high | mixed | 5 | Case 2 (primary) |
| CALL_016 | Michael Ben-David | No Sale | no_need | low | negative | 3 | Case 4 (reinforcing) |
| CALL_017 | Michael Ben-David | Follow-up Needed | authority | medium | neutral | 4 | — |
| CALL_018 | Michael Ben-David | Follow-up Needed | price | medium | mixed | 4 | — |

This batch completes Michael Ben-David's six-call allocation and brings the total corpus to 18 of 24 planned rows. Only Noa Friedman's six calls (CALL_019–CALL_024, including Contrast Case 3 and the ambiguous CALL_024) remain.

## QA summary

- All six transcripts fall within the 350–700 word range (485, 458, 466, 420, 412, 492) and 20–35 turn range (20, 22, 20, 20, 20, 20) — verified by `wc`/`grep`.
- The banned-phrase grep caught two real hits before finalizing: "Can I ask" (CALL_016, agent) and "I'd rather ... than ..." (CALL_017, a *customer* line — the guideline doesn't exempt customer dialogue, so it was rewritten too). A follow-up grep confirmed zero remaining matches across all six transcripts.
- Five secondary near-repeats ("Makes sense" ×3, "Good to know," "That's useful") were caught in a second pass and varied, even though none were on the explicit banned list — the corpus is now large enough (18 calls) that even non-banned acknowledgment phrases were starting to recur.
- `agent_talk_ratio` (0.54, 0.57, 0.44, 0.55, 0.41, 0.47) and `speaking_rate_wpm` (119, 137, 114, 126, 115, 131) were computed from each transcript's actual verified word count and speaker split. CALL_014's ratio (0.57, second-highest in the batch) and pace (137 wpm, fastest in the batch) are consistent with an agent who talks over the customer rather than listening.
- CALL_014 got a dedicated requirement-by-requirement verification table (see above) given its designation as the most consequential row in the corpus — every element of Contrast Case 6's specification was checked against a specific line in the transcript, not just asserted.
- Six distinct customer voices, none overlapping in register with each other or with prior batches: Sandra (direct, executive), Priya (decisive, redirecting), Greg (analytical, transparent about his own math), Frank (gruff, dismissive), Kenji (practical, wry), Elena (practical, procedurally weary but rooting for the outcome).

## Confirmation that Ground Truth Rules were respected

- Every structured field is directly supported by that call's transcript text, verified per-call in each Ground Truth validation checklist above.
- CALL_014's low `agent_performance_score` (2) and `objection_handling_quality` (2) coexist with `sale_result = Sale` and `lead_quality_score = 5`, correctly keeping these axes independent per `dataset_design.md` §9 — the row was not softened toward a "nicer" agent score to make the call feel less critical of Michael.
- CALL_015 and CALL_016 both stay at `No Sale` with high (`5`) and moderate (`3`) `agent_performance_score` respectively, for two different reasons (a well-reasoned customer-side financial decision vs. a genuinely low-need lead) — neither forced toward a uniform explanation.
- `manager_notes` in all six rows restate only what the transcript contains — no invented budgets, dates, names, or outcomes.
- Contrast Cases 2 (primary), 4 (reinforcing), and 6 (critical) are each verified explicitly against their specific transcript evidence, not just the matrix's plan — CALL_014 in particular against every individual requirement stated in this batch's instructions.

---

**Batch 5 (Noa Friedman's calls — CALL_019 through CALL_024, including Contrast Case 3 and the ambiguous/exploratory CALL_024) has not been started.** No CSV files have been generated in this sub-phase.
