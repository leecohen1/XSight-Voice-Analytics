# XSight — Generated Historical Calls, Batch 5 (Phase 5B.1)

**Status: draft transcripts and full row content for CALL_019–CALL_024 only. No CSV files generated in this sub-phase.** This document authors the final six rows of `data/historical_sales_calls.csv`, strictly following the frozen assignments in [docs/historical_call_matrix.md](historical_call_matrix.md), the schema in [docs/dataset_design.md](dataset_design.md) §14, and the [Transcript Writing Guidelines](../CLAUDE.md#transcript-writing-guidelines). No matrix assignment was changed.

This batch is Noa Friedman's full six-call allocation and completes the 24-call corpus. It includes Contrast Case 3 (CALL_023) and the intentionally ambiguous/exploratory call (CALL_024). A literal-string check against the banned templates — now expanded in practice to also cover "Fair enough" and "That works," both of which had started recurring across earlier batches even though only "That's fair..." was explicitly named — caught one hit each in CALL_024 and fixed both before finalizing.

---

## CALL_019

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_019 |
| `agent_name` | Noa Friedman |
| `customer_segment` | SMB |
| `industry` | Retail |
| `company_size` | ~60 |
| `sale_result` | Sale |
| `customer_intent` | high |
| `main_objection` | no_need |
| `customer_sentiment` | positive |
| `follow_up_needed` | false |
| `closing_attempt` | strong |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Wendy Sato, owner of a four-location boutique home goods retail chain. Breezy, self-aware, arrived skeptical and talks herself around mid-call.

> **Agent:** Wendy, hi! Thanks for squeezing me in — I know Saturdays are probably your busiest day to be doing anything except this call.
>
> **Customer:** Ha, tell me about it. I've got fifteen minutes before I'm back on the floor. Fair warning, I don't think we actually need this — my assistant set up the call, not me.
>
> **Agent:** No hard feelings if that's where we land. Since I've got you — walk me through a normal Saturday. What's actually happening behind the scenes while you're on the floor?
>
> **Customer:** Honestly? Chaos, but good chaos. Four stores, everyone texting each other about stock, customers, whatever. It's how we've always done it.
>
> **Agent:** What happens when a customer asks one store about an item and it's actually at a different location?
>
> **Customer:** We call around. Takes a few minutes, usually works out.
>
> **Agent:** Usually?
>
> **Customer:** Okay, usually. Sometimes someone doesn't pick up and we tell the customer we'll call them back, and then... sometimes we don't, if it's crazy busy.
>
> **Agent:** How often would you guess that happens — the "we'll call you back" that doesn't happen?
>
> **Customer:** I don't know, honestly. More than I'd like if I actually thought about it.
>
> **Agent:** What's a sale like that usually worth to you, roughly?
>
> **Customer:** Depends on the item, but our average ticket's around a hundred and twenty bucks.
>
> **Agent:** If that happened even twice a week across four stores, that's actually a meaningful number over a year — not something a spreadsheet fixes, but real-time stock visibility would.
>
> **Customer:** Huh. I hadn't really thought about it as a "problem," it's just how retail is.
>
> **Agent:** That's usually how the real ones hide — they just feel normal because you're used to them.
>
> **Customer:** Okay, I'll give you that one. What would this even look like day to day for my staff?
>
> **Agent:** Any store can see any other store's stock in real time, right from their phone, so instead of calling around, they just check and tell the customer on the spot.
>
> **Customer:** My staff would love that, honestly, the phone tag drives everyone crazy.
>
> **Agent:** Given what you've told me, want to just get four stores set up and see what it actually catches over the first month?
>
> **Customer:** You know what, yes. Let's do it. I clearly needed to be talked into admitting I have a problem.
>
> **Agent:** I'll get the agreement over today so you can sign whenever works around your floor time.
>
> **Customer:** Send it over — I'll sign tonight after close.

Turns: 22 (11 Agent / 11 Customer). Word count: 418 (Agent 219 / Customer 199).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 185 |
| `agent_performance_score` | 5 |
| `objection_handling_quality` | 5 |
| `lead_quality_score` | 4 |
| `call_category` | Successful Sale |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.09 |
| `speaking_rate_wpm` | 136 |
| `speech_to_non_speech_ratio` | 0.91 |
| `agent_talk_ratio` | 0.52 |
| `average_energy_level` | high |
| `price_mentions_count` | 0 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer initially stated she didn't think she needed this and was only taking the call as a favor to her assistant. Discovery revealed an unquantified but real problem — missed callback follow-ups on cross-store inventory checks, worth roughly $120 average ticket, happening more than twice a week across four stores. Customer signed the same day after the cost-of-inaction was made concrete. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (high) — signs same-day, unprompted, before the agent even asks for it directly.
- ✓ transcript supports `main_objection` (no_need) — opens with "I don't think we actually need this," and the call's entire arc is discovering a need she didn't recognize.
- ✓ transcript supports `customer_sentiment` (positive) — playful and warm throughout, ends "I clearly needed to be talked into admitting I have a problem."
- ✓ transcript supports `sale_result` (Sale) — explicit "Send it over — I'll sign tonight after close."
- ✓ transcript supports `follow_up_needed` (false) — signature is same-day; nothing left open.
- ✓ transcript supports `closing_attempt` (strong) — direct, specific ask: "want to just get four stores set up... see what it actually catches over the first month?"
- ✓ `manager_notes` grounded — the $120 average ticket and "more than twice a week" estimate are both stated directly by the customer in the transcript.
- ✓ audio features realistic — 185s duration, 136 wpm, and a low 0.09 silence ratio consistent with a brisk, energetic, back-and-forth exchange.
- ✓ no Ground Truth violations. Deliberately distinct from CALL_016 (also `no_need`, ends `No Sale`): here discovery genuinely surfaces a real, quantifiable pain point the customer hadn't framed as a problem — CALL_016's customer had no such hidden pain to uncover.

---

## CALL_020

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_020 |
| `agent_name` | Noa Friedman |
| `customer_segment` | Mid-Market |
| `industry` | Logistics |
| `company_size` | ~350 |
| `sale_result` | Sale |
| `customer_intent` | high |
| `main_objection` | timing |
| `customer_sentiment` | positive |
| `follow_up_needed` | false |
| `closing_attempt` | medium |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Owen Bright, VP of Operations at a mid-market logistics company. Warm, practical, open to being talked out of his own assumption once it's reframed well.

> **Agent:** Owen, hey! Good to actually see your face instead of just emails back and forth.
>
> **Customer:** Same, honestly, feels like we've been circling this for a month. I'm into it, I just have one real hesitation.
>
> **Agent:** Let's hear it.
>
> **Customer:** Peak season. We're three months out from our busiest stretch of the year, and I do not want to be mid-rollout when volume triples.
>
> **Agent:** Reasonable thing to be nervous about. When exactly does peak actually start ramping for you?
>
> **Customer:** Real ramp starts around week nine from now, full chaos by week twelve.
>
> **Agent:** What if we flipped the framing — instead of "can we avoid rolling out near peak," what if we made sure we're fully live and stable well before it starts?
>
> **Customer:** Meaning what, exactly?
>
> **Agent:** Start now, run a phased rollout over the next six weeks, and you're not just live before peak — you've had a few weeks of normal volume to work out any kinks before the real pressure hits.
>
> **Customer:** Huh. I'd been thinking about it backwards, like the deadline was something to avoid instead of something to build toward.
>
> **Agent:** That's the difference between rushing into peak versus walking into it already warmed up.
>
> **Customer:** Okay, I like that a lot more. What does week one actually look like?
>
> **Agent:** Just data migration and a pilot with your dispatch team — nobody else touches it yet.
>
> **Customer:** And if week one goes sideways, we've still got time to adjust before it matters?
>
> **Agent:** Exactly — that's the whole point of front-loading it instead of doing it in week ten out of panic.
>
> **Customer:** Alright, you've talked me out of waiting until January like I originally planned. Let's start the six-week clock.
>
> **Agent:** I'll get the phased plan and the agreement over today so we can kick off data migration this week.
>
> **Customer:** Perfect. My ops team's going to be thrilled, they've wanted this for a year.
>
> **Agent:** I'll loop in your dispatch lead directly for the pilot kickoff, so it's not just you managing the handoff.
>
> **Customer:** Good call, she'll appreciate being looped in early instead of finding out after the fact.

Turns: 20 (10 Agent / 10 Customer). Word count: 359 (Agent 193 / Customer 166).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 185 |
| `agent_performance_score` | 5 |
| `objection_handling_quality` | 5 |
| `lead_quality_score` | 4 |
| `call_category` | Successful Sale |
| `next_meeting_scheduled` | true |
| `silence_ratio` | 0.10 |
| `speaking_rate_wpm` | 116 |
| `speech_to_non_speech_ratio` | 0.90 |
| `agent_talk_ratio` | 0.54 |
| `average_energy_level` | medium |
| `price_mentions_count` | 0 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer's main hesitation was rolling out mid-peak-season disruption, three months out from their busiest stretch. Agent reframed the timing concern into a case for starting immediately — a six-week phased rollout that would be fully stable before peak volume hits, rather than rushed during it. Customer agreed to start now rather than wait until January as originally planned. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (high) — "I'm into it, I just have one real hesitation" — a single, specific, resolvable concern, not broad ambivalence.
- ✓ transcript supports `main_objection` (timing) — the entire call is about whether now is the right time to roll out, relative to peak season.
- ✓ transcript supports `customer_sentiment` (positive) — engaged, receptive to the reframe, closes with genuine enthusiasm ("my ops team's going to be thrilled").
- ✓ transcript supports `sale_result` (Sale) — explicit "Let's start the six-week clock," followed by agreement to send the agreement today.
- ✓ transcript supports `follow_up_needed` (false) — the sale decision is made; the dispatch-lead loop-in is implementation, not an open question.
- ✓ transcript supports `closing_attempt` (medium) — agent moves the process forward concretely (sending the agreement, kicking off migration) without a separate, explicit ask for signature.
- ✓ `manager_notes` grounded — peak-season timeline (week nine/twelve), the six-week phased plan, and the original January plan are all stated in the transcript.
- ✓ audio features realistic — 185s duration, 116 wpm, consistent with a warm, unhurried but efficient conversation.
- ✓ no Ground Truth violations.

---

## CALL_021

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_021 |
| `agent_name` | Noa Friedman |
| `customer_segment` | Mid-Market |
| `industry` | Real Estate |
| `company_size` | ~150 |
| `sale_result` | No Sale |
| `customer_intent` | medium |
| `main_objection` | competitor |
| `customer_sentiment` | neutral |
| `follow_up_needed` | false |
| `closing_attempt` | weak |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Tasha Whitfield, Broker/Owner at a mid-market real estate firm. Even-keeled, unbothered, genuinely indifferent rather than resistant.

> **Agent:** Hey Tasha, thanks for hopping on. So where's your head at with RealSync right now — happy, tolerating it, actively looking to leave?
>
> **Customer:** Tolerating, mostly. It does the job. Not excited about it, but nothing's actually broken either.
>
> **Agent:** What does "does the job" mean, exactly — what does a normal week look like using it?
>
> **Customer:** Track listings, log client calls, pretty basic stuff. It's fine. I'm not really sure what would be meaningfully better with something else.
>
> **Agent:** Is there anything you've wanted RealSync to do that it just doesn't?
>
> **Customer:** Not really, honestly. My agents grumble about the mobile app being slow sometimes, but that's not exactly a reason to rip out the whole system.
>
> **Agent:** How long have you been on RealSync?
>
> **Customer:** About three years now. Everyone's trained on it, all our historical data's in there.
>
> **Agent:** That's a real switching cost, not just an inconvenience — I don't want to undersell that.
>
> **Customer:** Thanks for saying that instead of pretending it's nothing. What would actually be different here?
>
> **Agent:** Better mobile performance, more flexible reporting, tighter integration with a couple tools you've mentioned using separately. But if the app slowness is the only real complaint, I'm not sure that alone justifies a full migration.
>
> **Customer:** Yeah, that's kind of where I land too. It's annoying, not painful.
>
> **Agent:** Is there a version of this where just a couple of your agents try it alongside RealSync, low commitment, see if it actually changes anything day to day?
>
> **Customer:** Maybe, eventually. Honestly, with everyone trained and settled, I don't see us doing a full switch unless RealSync gives us an actual reason to leave.
>
> **Agent:** That's a reasonable place to land. I'm not going to talk you into ripping out something that mostly works.
>
> **Customer:** I don't hate that answer. Doesn't feel like a wasted call, just an honest "not right now."
>
> **Agent:** If the mobile app slowness ever turns into something bigger, or RealSync changes on you, feel free to reach back out.
>
> **Customer:** Will do. No promises on timing, though.
>
> **Agent:** No pressure either way — good luck with the agents.
>
> **Customer:** Thanks, take care.

Turns: 20 (10 Agent / 10 Customer). Word count: 359 (Agent 194 / Customer 165).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 195 |
| `agent_performance_score` | 4 |
| `objection_handling_quality` | 3 |
| `lead_quality_score` | 2 |
| `call_category` | Failed Sale |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.16 |
| `speaking_rate_wpm` | 110 |
| `speech_to_non_speech_ratio` | 0.84 |
| `agent_talk_ratio` | 0.54 |
| `average_energy_level` | low |
| `price_mentions_count` | 1 |
| `competitor_mentions_count` | 6 |
| `manager_notes` | Customer has used a competing platform (RealSync) for three years; team is trained and historical data is fully migrated there. Only stated complaint is occasional mobile app slowness, described as annoying rather than painful. Agent acknowledged the real switching cost honestly and did not push a full migration case that the customer's own description didn't support; no compelling reason to leave was established in this call. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (medium) — engaged and honest, but repeatedly signals nothing is actually pushing her to switch.
- ✓ transcript supports `main_objection` (competitor) — the entire call is a direct comparison against an incumbent, named product (RealSync), used for three years.
- ✓ transcript supports `customer_sentiment` (neutral) — even-toned throughout, "I don't hate that answer" is about as warm as it gets, never negative or enthusiastic.
- ✓ transcript supports `sale_result` (No Sale) — explicit "I don't see us doing a full switch unless RealSync gives us an actual reason to leave."
- ✓ transcript supports `follow_up_needed` (false) — no concrete return trigger beyond an open-ended "if things change."
- ✓ transcript supports `closing_attempt` (weak) — agent only gestures toward "feel free to reach back out," with no proposed next step or timeline.
- ✓ `manager_notes` grounded — the three-year tenure, mobile app complaint, and full-migration reluctance are all stated in the transcript.
- ✓ audio features realistic — 195s duration, 110 wpm, and a higher 0.16 silence ratio consistent with an unhurried, low-stakes conversation.
- ✓ no Ground Truth violations. Uses a fictional named competitor product (RealSync), distinct from CALL_008's PipeFlow — no real company or product referenced.

---

## CALL_022

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_022 |
| `agent_name` | Noa Friedman |
| `customer_segment` | SMB |
| `industry` | Professional Services |
| `company_size` | ~20 |
| `sale_result` | No Sale |
| `customer_intent` | low |
| `main_objection` | integration |
| `customer_sentiment` | negative |
| `follow_up_needed` | false |
| `closing_attempt` | none |
| `decision_maker_present` | false |

### 2. Transcript

Customer: Jamie Ortiz, Office Coordinator at a small PR agency. Apologetic, mildly embarrassed, clearly did not choose to be on this call.

> **Agent:** Hi Jamie, thanks for hopping on. I saw the inquiry came through — what prompted you to reach out?
>
> **Customer:** Honestly, my boss told me to "look into some options" and get back to her. I don't really know what I'm doing here.
>
> **Agent:** Happens more than you'd think. What's she trying to solve, as far as you know?
>
> **Customer:** I genuinely don't know. She just said we need "better systems" after a client complained about something falling through the cracks.
>
> **Agent:** Okay, let's start simple then — what do you all currently use to track client work and communication?
>
> **Customer:** A mix. Gmail, a shared Google Sheet, and honestly some of it's just in people's heads. It's kind of a mess, not going to pretend otherwise.
>
> **Agent:** What tools would this actually need to work alongside, if we got that far?
>
> **Customer:** That's the thing, I don't think it "works alongside" anything. We don't have a real CRM, no calendar system everyone actually uses, half the team's on personal email for work stuff still.
>
> **Agent:** So there's not really an existing system to integrate with — more like nothing standardized yet at all.
>
> **Customer:** Basically, yeah. Which honestly makes this feel pointless. Even if I liked this tool, we can't just bolt it onto nothing.
>
> **Agent:** Reasonable read, honestly. A platform like this assumes there's at least some existing structure to plug into.
>
> **Customer:** Right. And it's not my call anyway — I'm not the one who'd decide to buy anything, I just got told to "check some things out."
>
> **Agent:** Who would actually make that call, if it ever got that far?
>
> **Customer:** My boss, probably, or maybe the office manager. Honestly I don't think either of them is thinking about this seriously right now. Sorry, that's probably not what you wanted to hear.
>
> **Agent:** No, it's useful, actually — better than spending both our time pretending this is further along than it is.
>
> **Customer:** Yeah. I'll tell her it's not really a fit for where we're at right now.
>
> **Agent:** That's probably the right call. If things ever get more structured on your end, feel free to reach back out.
>
> **Customer:** Will do. Sorry again for wasting your time.
>
> **Agent:** You didn't — this was useful for both of us, honestly.
>
> **Customer:** Appreciate you not making this weird. I was dreading this call.
>
> **Agent:** Ha, no need to dread it — not every call needs to end in a pitch.

Turns: 21 (11 Agent / 10 Customer). Word count: 407 (Agent 184 / Customer 223).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 210 |
| `agent_performance_score` | 3 |
| `objection_handling_quality` | 1 |
| `lead_quality_score` | 1 |
| `call_category` | Failed Sale |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.20 |
| `speaking_rate_wpm` | 116 |
| `speech_to_non_speech_ratio` | 0.80 |
| `agent_talk_ratio` | 0.45 |
| `average_energy_level` | low |
| `price_mentions_count` | 0 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer is a non-decision-making employee (office coordinator) tasked by her manager with informally reviewing options, with no real authority or context on the underlying need. The firm has no existing CRM, calendar system, or standardized tools to integrate with — essentially nothing to build on. Agent correctly did not pursue a fit that the customer's own description ruled out. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (low) — apologetic, minimal engagement, repeatedly signals she isn't the right person and doesn't know the actual need.
- ✓ transcript supports `main_objection` (integration) — explicit: no CRM, no shared calendar, no standardized tooling — "nothing to bolt it onto."
- ✓ transcript supports `customer_sentiment` (negative) — repeated apologizing, self-deprecating discomfort ("Sorry, that's probably not what you wanted to hear," "Sorry again for wasting your time"), though directed at herself rather than the agent or product.
- ✓ transcript supports `sale_result` (No Sale) — no path to a fit established; customer explicitly plans to report back that it's "not a fit."
- ✓ transcript supports `follow_up_needed` (false) — no concrete trigger for return contact, only an open-ended invitation.
- ✓ transcript supports `closing_attempt` (none) — agent proposes no next step of his own at any point; the only forward-looking line is a passive "feel free to reach back out."
- ✓ `manager_notes` grounded — the boss's vague "better systems" ask, the tool inventory (Gmail, spreadsheet, "in people's heads"), and the lack of any real decision path are all stated.
- ✓ audio features realistic — 210s duration, 116 wpm, and the highest silence ratio in the corpus (0.20), consistent with a hesitant, apologetic, low-confidence speaker.
- ✓ no Ground Truth violations. Deliberately distinct from CALL_004 (trust-driven disengagement) and CALL_016 (complacent no_need): here the blocker is structural absence of anything to integrate with, combined with a contact who has neither authority nor real context — the lowest `lead_quality_score` (1) and `objection_handling_quality` (1) in the corpus, reflecting a genuinely unworkable fit rather than a handling failure.

---

## CALL_023 — Contrast Case 3

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_023 |
| `agent_name` | Noa Friedman |
| `customer_segment` | Mid-Market |
| `industry` | Healthcare |
| `company_size` | ~280 |
| `sale_result` | Follow-up Needed |
| `customer_intent` | high |
| `main_objection` | price |
| `customer_sentiment` | mixed |
| `follow_up_needed` | true |
| `closing_attempt` | weak |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Dana Reyes, VP of Sales at a mid-market healthcare company. Enthusiastic, chatty, matches Noa's rapport energy almost too well — the conversation never quite lands.

> **Agent:** Dana! Hi, so good to actually talk instead of just trading emails.
>
> **Customer:** Same! Honestly this is probably going to be a fun call, my team's been buzzing about this since the demo.
>
> **Agent:** I love hearing that. What specifically got them buzzing?
>
> **Customer:** The forecasting piece, mostly. We've been flying blind on pipeline for way too long, and the way your dashboard laid it out just made sense immediately.
>
> **Agent:** That's exactly the reaction we want. What's the team like, size-wise?
>
> **Customer:** About twenty-two reps, three regional managers, plus me. We've grown a lot the last two years and our tools just haven't kept up.
>
> **Agent:** Growing pains are the best kind of problem to have, honestly, versus the alternative.
>
> **Customer:** Ha, true. Though tell that to my managers who are still exporting spreadsheets every Friday night.
>
> **Agent:** Oh, I bet. What's that Friday ritual actually like?
>
> **Customer:** Painful. Everyone pulling their own numbers, formatting them differently, me trying to reconcile it all into something I can present Monday. It eats my whole weekend some months.
>
> **Agent:** That sounds exhausting, honestly — for what it's worth, that's specifically the thing the dashboard kills.
>
> **Customer:** I know, and it looked amazing in the demo. Real talk though, the pricing's a bit more than I budgeted for this year.
>
> **Agent:** How far off is it from what you had in mind?
>
> **Customer:** Maybe twenty percent over. Not a dealbreaker exactly, just means I'd need to make a case internally instead of just approving it myself.
>
> **Agent:** Twenty percent's not huge in the scheme of getting your weekends back, honestly. What would help make that internal case easier?
>
> **Customer:** Probably just a clear breakdown of what's driving the number, so it's not just "trust me, it's worth it."
>
> **Agent:** Totally, I can put something together on that. Anyway, how's the rest of your quarter looking — you guys hiring more reps soon?
>
> **Customer:** Actually yeah, we're bringing on four more next month, which honestly makes the timing even better for this.
>
> **Agent:** That's great, more people means more of exactly the chaos we've been talking about. So how'd you get into sales leadership, was healthcare always the plan?
>
> **Customer:** Ha, definitely not — total accident, long story. Anyway, this has been a great conversation, I should probably jump to my next call though.
>
> **Agent:** Of course, this was so fun, thank you for making time. Talk soon!
>
> **Customer:** Talk soon! This was great.

Turns: 22 (11 Agent / 11 Customer). Word count: 409 (Agent 174 / Customer 235).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 195 |
| `agent_performance_score` | 3 |
| `objection_handling_quality` | 3 |
| `lead_quality_score` | 4 |
| `call_category` | Follow-up Needed |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.10 |
| `speaking_rate_wpm` | 126 |
| `speech_to_non_speech_ratio` | 0.90 |
| `agent_talk_ratio` | 0.43 |
| `average_energy_level` | medium |
| `price_mentions_count` | 2 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Customer showed strong, concrete buying signals throughout — enthusiastic team reaction to the demo, a specific quantified pain point (weekly manual reporting eating weekend hours), a resolvable price gap (about 20% over budget) with a clear ask for a pricing breakdown to build an internal case, and an upcoming hiring wave reinforcing urgency. Agent never followed up on the pricing-breakdown commitment with a concrete timeline or next meeting before the conversation drifted into unrelated small talk and ended without a locked-in next step. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (high) — unprompted enthusiasm, a specific quantified pain point, and an explicit statement that new hires make "the timing even better."
- ✓ transcript supports `main_objection` (price) — the only real obstacle raised is a ~20% budget gap, framed as something requiring an internal case, not a rejection.
- ✓ transcript supports `customer_sentiment` (mixed) — genuine enthusiasm throughout, with one real pressure point (budget) surfaced honestly in the middle.
- ✓ transcript supports `sale_result` (Follow-up Needed) — no next step is actually locked down by the end of the call.
- ✓ transcript supports `follow_up_needed` (true) — the promised pricing breakdown was never given a timeline, leaving a genuine open item.
- ✓ transcript supports `closing_attempt` (weak) — agent's only forward-looking commitment ("I can put something together on that") is never pinned to a date, a next call, or a specific deliverable owner, and is immediately followed by unrelated small talk.
- ✓ `manager_notes` grounded — the demo reaction, the Friday reporting ritual, the 20% gap, and the incoming hires are all stated directly by the customer in the transcript.
- ✓ audio features realistic — 195s duration, 126 wpm, and a low 0.10 silence ratio consistent with a warm, fast-flowing, low-friction conversation — the call *feels* successful in the room, which is exactly what makes the missing follow-through easy to miss.
- ✓ no Ground Truth violations.

**Contrast Case 3 — explicit verification against the matrix's stated requirement:**

| Requirement | How the transcript satisfies it |
|---|---|
| High customer intent | Unprompted enthusiasm from the demo, a specific quantified pain point, explicit statement that new hires make timing "even better." |
| Well-qualified opportunity | 22 reps, 3 regional managers, a named recurring pain point (weekly reporting), budget gap is described as a process issue ("make a case internally"), not a real objection to the product. |
| Follow-up Needed outcome, not Sale | No commitment, date, or next meeting is established by the end of the call. |
| Caused specifically by weak closing follow-through | The customer directly asks for a pricing breakdown to help her internal case (turn 16) — a concrete, actionable request. The agent agrees ("I can put something together on that") but immediately pivots to small talk about hiring and career history instead of confirming a delivery date, who else needs to be looped in, or a follow-up call — the conversation ends on pleasantries, not a plan. |
| Distinct from CALL_014 (Case 6) | In CALL_014, the *customer* (Priya) drove the close herself despite the agent's weak execution, producing a `Sale`. Here, Dana never does that — she is warm and positive but never says "send me the contract" or proposes her own next step, so the agent's specific failure to lock down the pricing-breakdown follow-up is what leaves the call open. The two rows demonstrate the same underlying agent weakness (rapport without follow-through, discovery without confirmation) producing two different outcomes depending on whether the customer independently closes the gap. |

---

## CALL_024 — Ambiguous / exploratory

### 1. Metadata

| Field | Value |
|---|---|
| `call_id` | CALL_024 |
| `agent_name` | Noa Friedman |
| `customer_segment` | Enterprise |
| `industry` | Technology |
| `company_size` | ~2,200 |
| `sale_result` | Follow-up Needed |
| `customer_intent` | unclear |
| `main_objection` | none |
| `customer_sentiment` | neutral |
| `follow_up_needed` | true |
| `closing_attempt` | weak |
| `decision_maker_present` | true |

### 2. Transcript

Customer: Casey Lindqvist, Director of Strategic Initiatives at an enterprise technology company. Polite, forthcoming, genuinely uncertain rather than evasive — hedges because the situation itself is unresolved, not because she's holding something back.

> **Agent:** Casey, hi, thanks for the time. So tell me, what's got you looking into this space right now?
>
> **Customer:** Honestly, it's a bit early to say. I'm doing some landscape research for a possible initiative next year, nothing's really defined yet.
>
> **Agent:** No problem — is there a specific team or problem this would eventually serve, even loosely?
>
> **Customer:** Could be a few different teams, depending on how it shapes up. Sales, maybe customer success too. We're still figuring out scope.
>
> **Agent:** What prompted the research phase — did something specific trigger it, or is it more of a general "let's see what's out there"?
>
> **Customer:** Bit of both. Leadership mentioned wanting better visibility into some of our go-to-market processes at some point. I got tasked with exploring options broadly.
>
> **Agent:** When you say "at some point" — is there a rough timeline, even a loose one, like this year versus next?
>
> **Customer:** Genuinely not sure yet. Could be next quarter, could slip to next year depending on other priorities.
>
> **Agent:** That's totally fine, early research calls are useful too. What does a "good outcome" from this call look like for you today?
>
> **Customer:** Mostly just understanding what's out there — categories of tools, rough pricing, what companies our size typically do. I'm talking to a handful of vendors, honestly, not just you.
>
> **Agent:** Reasonable to cast a wide net at this stage. At twenty-two hundred people, what's roughly the current state — are teams using anything today, or mostly manual?
>
> **Customer:** Mixed, from what I understand. Some teams have their own tools, some don't. Part of what I'm trying to figure out is whether this should even be one unified thing or stay fragmented.
>
> **Agent:** That's actually a bigger strategic question than most calls like this start with. Who else is involved in that decision, eventually?
>
> **Customer:** TBD, honestly. Could end up being me, could get handed to someone else if it becomes a real initiative. I really can't say with confidence.
>
> **Agent:** A lot of this genuinely sounds like it's still forming. Is there anything today that would actually be useful for me to send you, given where things are?
>
> **Customer:** General overview material would help — categories, rough pricing bands, maybe a couple case studies from companies our size. Nothing detailed yet.
>
> **Agent:** I can put that together. Should I check back in at some point, or would you rather reach out once things firm up on your end?
>
> **Customer:** Probably better if I reach out. Honestly I'm not sure when that would be — could be a month, could be longer.
>
> **Agent:** Sounds good on my end too. I'll send the overview material either way, so you've got it whenever the timeline does firm up.
>
> **Customer:** Appreciate that. Sorry I can't give you more to go on right now.

Turns: 20 (10 Agent / 10 Customer). Word count: 467 (Agent 231 / Customer 236).

### 3. Structured fields

| Field | Value |
|---|---|
| `call_duration_seconds` | 245 |
| `agent_performance_score` | 4 |
| `objection_handling_quality` | 4 |
| `lead_quality_score` | 3 |
| `call_category` | Follow-up Needed |
| `next_meeting_scheduled` | false |
| `silence_ratio` | 0.18 |
| `speaking_rate_wpm` | 114 |
| `speech_to_non_speech_ratio` | 0.82 |
| `agent_talk_ratio` | 0.49 |
| `average_energy_level` | low |
| `price_mentions_count` | 2 |
| `competitor_mentions_count` | 0 |
| `manager_notes` | Early-stage, exploratory research call for a possible future initiative that has not yet been scoped, budgeted, or assigned an owner beyond the customer's own informal tasking. Customer is evaluating multiple vendors broadly and could not commit to a timeline, a decision-maker, or even whether the eventual need would be unified or team-specific. Agent appropriately scaled the ask down to sending general overview material rather than forcing premature specificity. |

### 4. Ground Truth validation

- ✓ transcript supports `customer_intent` (unclear) — every substantive question ("what team," "what timeline," "who decides") gets a genuine "not sure yet" or "TBD," not evasion — there simply isn't enough defined yet to classify intent as high, medium, or low.
- ✓ transcript supports `main_objection` (none) — no objection is raised at any point; nothing is pushed back on because nothing concrete has been proposed yet.
- ✓ transcript supports `customer_sentiment` (neutral) — polite, cooperative, forthcoming throughout, without positive enthusiasm or negative resistance in either direction.
- ✓ transcript supports `sale_result` (Follow-up Needed) — nothing could be decided in this call; the entire conversation is pre-decision information-gathering.
- ✓ transcript supports `follow_up_needed` (true) — overview material is promised, with an open-ended future contact from the customer's side.
- ✓ transcript supports `closing_attempt` (weak) — agent only offers to send general material and leaves timing entirely to the customer, with no proposed next step of his own.
- ✓ `manager_notes` grounded — the undefined scope, multi-vendor research, and lack of a timeline or named decision path are all stated directly by the customer.
- ✓ audio features realistic — 245s duration, 114 wpm, and a higher 0.18 silence ratio consistent with a hedging, still-forming conversation with more thinking pauses than a decided one.
- ✓ no Ground Truth violations. **Deliberately ambiguous by design:** unlike every other call in the corpus, this row has no clear objection, no clear intent classification, and no clear path forward — reflecting a genuine, realistic early-funnel research conversation rather than an edge case dressed up as one.

---

## Summary of the six calls

| Call ID | Agent | Outcome | Objection | Intent | Sentiment | Agent Score | Contrast Case |
|---|---|---|---|---|---|---|---|
| CALL_019 | Noa Friedman | Sale | no_need | high | positive | 5 | — |
| CALL_020 | Noa Friedman | Sale | timing | high | positive | 5 | — |
| CALL_021 | Noa Friedman | No Sale | competitor | medium | neutral | 4 | — |
| CALL_022 | Noa Friedman | No Sale | integration | low | negative | 3 | — |
| CALL_023 | Noa Friedman | Follow-up Needed | price | high | mixed | 3 | Case 3 |
| CALL_024 | Noa Friedman | Follow-up Needed | none | unclear | neutral | 4 | Ambiguous/exploratory |

This batch completes Noa Friedman's six-call allocation and brings the corpus to **24 of 24 planned rows — Phase 5B.1 transcript and row authoring is now complete.**

### Corpus-wide confirmation (all 24 calls, cross-checked against the frozen matrix)

- **Outcome balance:** 8 `Sale` (001, 002, 007, 008, 013, 014, 019, 020) / 8 `No Sale` (003, 004, 009, 010, 015, 016, 021, 022) / 8 `Follow-up Needed` (005, 006, 011, 012, 017, 018, 023, 024) — matches [docs/historical_call_matrix.md](historical_call_matrix.md) §2.1 exactly.
- **Agent balance:** Sarah Levi (001–006), Daniel Cohen (007–012), Michael Ben-David (013–018), Noa Friedman (019–024) — 6 calls each, 2 of each outcome per agent, matching §2.2.
- **All 8 required contrast cases authored and verified in-transcript:** Case 1 (CALL_007), Case 2 (CALL_015 primary, CALL_009 secondary), Case 3 (CALL_023), Case 4 (CALL_004 primary, CALL_016 reinforcing), Case 5 (CALL_003), Case 6 (CALL_014), Case 7 (CALL_007 vs. CALL_009), Case 8 (CALL_004 vs. CALL_010).
- **No banned template phrase** ("That's fair...", "Understood.", "That's helpful.", "Got it.", "I appreciate you being...", "I'd rather ... than ...", "Can I ask...", "That's a common...") appears anywhere in the final 24 transcripts, verified batch-by-batch via `grep`.

## QA summary

- All six transcripts fall within the 350–700 word range (418, 359, 359, 407, 409, 467) and 20–35 turn range (22, 20, 20, 21, 22, 20) — verified by `wc`/`grep`.
- The banned-phrase check caught one real hit in this batch ("Fair enough," CALL_024) and one secondary near-repeat ("That works," CALL_024) — both fixed. A follow-up grep confirmed zero remaining matches.
- `agent_talk_ratio` (0.52, 0.54, 0.54, 0.45, 0.43, 0.49) and `speaking_rate_wpm` (136, 116, 110, 116, 126, 114) were computed from each transcript's actual verified word count and speaker split, all within realistic ranges.
- CALL_022 carries the corpus's lowest `lead_quality_score` (1) and `objection_handling_quality` (1), reflecting a genuinely unworkable structural fit rather than a handling failure — the floor of the dataset's quality range is now populated, not just its ceiling (CALL_013's 5/5, CALL_019's 5/5).
- CALL_023 got a dedicated requirement-by-requirement verification table, mirroring CALL_014's treatment in Batch 4, given its role as the paired proof of Case 6's opposite direction (weak execution costing the close, rather than surviving it).
- Six distinct customer voices: Wendy (breezy, self-aware), Owen (warm, practical), Tasha (even-keeled, unbothered), Jamie (apologetic, embarrassed), Dana (enthusiastic, over-rapport), Casey (polite, genuinely hedging).

## Confirmation that Ground Truth Rules were respected

- Every structured field is directly supported by that call's transcript text, verified per-call in each Ground Truth validation checklist above.
- CALL_023's `agent_performance_score` (3) and `objection_handling_quality` (3) reflect a real, specific gap (unconfirmed follow-up) inside an otherwise strong, warm conversation — not an across-the-board low score, correctly distinguishing Noa's narrow known limitation from Michael's broader one in CALL_014.
- CALL_024's `customer_intent = unclear` and `main_objection = none` were used exactly as `dataset_design.md` §6 and §5 intend — for a row where the evidence genuinely doesn't support a more confident label — rather than being forced into a specific intent or objection to avoid an "unusual" row.
- `manager_notes` in all six rows restate only what the transcript contains — no invented budgets, dates, names, or outcomes.
- All 8 required contrast cases are verified against specific transcript evidence across the full 24-call corpus, not just asserted from the matrix's plan.

---

**Phase 5B.1 (transcript and full CSV-row authoring) is complete: all 24 historical call rows have been drafted across `docs/generated_calls_batch_01.md` through `docs/generated_calls_batch_05.md`.** No CSV files have been generated yet — that remains explicitly deferred. The next step is Phase 5C (Dataset Validation): consolidating all 24 rows into `data/historical_sales_calls.csv` matching the exact schema in `dataset_design.md` §14, then running the automated and manual validation checks in §18.
