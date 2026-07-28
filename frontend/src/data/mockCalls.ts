/**
 * Centralized mock call fixtures — the only place call demo-data literals
 * live. Every page/component reads calls through `services/callsApi.ts`,
 * never from this file directly, so swapping in a real backend later never
 * touches a component.
 *
 * Agent names (Sarah Levi, Daniel Cohen, Michael Ben-David, Noa Friedman)
 * and the historical-call citation IDs (CALL_003, CALL_007, CALL_010,
 * CALL_018, CALL_023) reuse the fictional agents and RAG corpus already
 * established in `docs/dataset_design.md` / `data/historical_sales_calls.csv`,
 * so this demo data reads as part of the same product world rather than an
 * unrelated placeholder universe.
 */
import type { CallRecord } from '../types'

export const mockCalls: CallRecord[] = [
  // 1 — clean Sale, high confidence, guardrail pass.
  {
    callId: 'XS-1001',
    status: 'completed',
    agentName: 'Sarah Levi',
    callDate: '2026-07-24',
    customerName: 'Fielding & Yates Logistics',
    createdAt: '2026-07-24T14:05:00Z',
    callOutcome: 'Sale',
    riskLevel: 'Low',
    confidence: 0.91,
    guardrailStatus: 'pass',
    audioDurationSeconds: 612,
    metadata: { agentName: 'Sarah Levi', callDate: '2026-07-24', customerName: 'Fielding & Yates Logistics', audioFileName: 'call_fielding_yates.mp3', audioDurationSeconds: 612 },
    analysis: {
      transcript:
        "Agent: Hi, this is Sarah from Northwind Solutions — thanks for making time today. Is this still a good time?\nCustomer: Yes, perfect timing actually. We just finished our ops review and the onboarding delays you asked about last time are still our biggest headache.\nAgent: Good to know that's still top of mind. Last call you mentioned it was taking your team about three weeks to get a new warehouse live. Has that changed?\nCustomer: If anything it's worse — closer to four weeks now, we added two new sites.\nAgent: Our automated onboarding flow typically gets that down to five to seven days, and I can show you exactly how during a short pilot. Would your ops lead be able to join a 30-minute walkthrough this week?\nCustomer: I think so. Can you send a couple of times? I want Marcus from ops in the room, he'll ask the hard questions.\nAgent: Absolutely, I'll send three slots by end of day. One more thing — given the four-week number, would it help if I brought a rough ROI estimate based on your site count?\nCustomer: Yes, that would actually help me get budget sign-off faster.\nAgent: I'll have that ready before the walkthrough. Anything else on your end before we wrap?\nCustomer: No, I think we're aligned. Send the invite and we'll take it from there.\nAgent: Will do — talk soon.",
      call_summary:
        'Returning prospect confirmed onboarding delays have worsened (four weeks, two new sites added). The agent secured a 30-minute walkthrough with the customer\'s ops lead and committed to a site-count-based ROI estimate ahead of the meeting, directly addressing the stated blocker.',
      customer_intent: 'Actively evaluating a fix for a worsening onboarding-time problem; ready to bring in a technical stakeholder.',
      main_objection: 'none',
      customer_sentiment: 'positive',
      call_outcome: 'Sale',
      agent_performance_score: 5,
      lead_quality_score: 5,
      similar_calls: [
        { call_id: 'CALL_003', agent_name: 'Daniel Cohen', sale_result: 'Sale', main_objection: 'authority', similarity_score: 0.71, reason: 'CALL_003 also involved bringing in a second technical stakeholder before close; both calls closed after that stakeholder was looped in.' },
      ],
      coaching_feedback: [
        'Strong move quantifying the delay (three weeks to four) instead of letting it stay vague — that number is what justified urgency.',
        'Proactively offering the ROI estimate before being asked shows good anticipation of the internal budget conversation the customer will have.',
      ],
      recommended_next_action: 'Send three walkthrough time slots today, ensure Marcus (ops) is on the invite, and complete the site-count ROI estimate before the meeting.',
      suggested_follow_up_email:
        'Subject: Walkthrough times + ROI estimate\n\nHi there,\n\nGreat catching up today. As discussed, here are three times this week for a 30-minute walkthrough with Marcus:\n\n- [Slot 1]\n- [Slot 2]\n- [Slot 3]\n\nI will also have a rough ROI estimate ready based on your current site count, so you have the numbers for budget sign-off.\n\nTalk soon,\nSarah',
      routing_category: 'expansion_opportunity',
      confidence: 0.91,
      risk_level: 'Low',
      detected_signals: ['returning prospect', 'quantified pain point', 'technical stakeholder engaged', 'budget conversation in progress'],
      limitations: 'None — evidence across the transcript, structured extraction, and RAG comparison is consistent and well above the auto-approve confidence threshold.',
      guardrail_status: 'pass',
    },
    evidence: { ragInsight: 'Closest match is CALL_003 — a similar multi-stakeholder pattern that also closed.', ragCitations: ['CALL_003'], signalDetectedSignals: ['returning prospect', 'quantified pain point', 'technical stakeholder engaged'], signalConfidence: 0.91, langgraphReasoningSteps: ['Reviewed structured extraction', 'Compared against CALL_003', 'No conflicting signals found'], langgraphEvidenceConflicts: [] },
  },

  // 2 — No Sale, competitor objection, guardrail pass.
  {
    callId: 'XS-1002',
    status: 'completed',
    agentName: 'Daniel Cohen',
    callDate: '2026-07-22',
    customerName: 'Harrow Retail Group',
    createdAt: '2026-07-22T10:40:00Z',
    callOutcome: 'No Sale',
    riskLevel: 'Medium',
    confidence: 0.83,
    guardrailStatus: 'pass',
    audioDurationSeconds: 498,
    metadata: { agentName: 'Daniel Cohen', callDate: '2026-07-22', customerName: 'Harrow Retail Group', audioFileName: 'call_harrow_retail.mp3', audioDurationSeconds: 498 },
    analysis: {
      transcript:
        "Agent: Thanks for jumping on, I know you're mid-evaluation. Where did things land with the other vendor?\nCustomer: We actually signed with them last week.\nAgent: Ah — can I ask what tipped it their way?\nCustomer: Honestly, their platform already integrates with our POS system natively. Yours needed a middleware layer, and our IT team didn't want to maintain that.\nAgent: That's fair, and useful for me to know precisely. Was pricing a factor at all, or purely the integration path?\nCustomer: Mostly integration. Price was close enough not to matter.\nAgent: Understood. If it's alright, I'd like to keep you posted when native POS support ships — is that something worth revisiting in a few months?\nCustomer: Sure, no promises, but keep me in the loop.\nAgent: Will do. Appreciate the honest feedback either way.",
      call_summary:
        'Prospect signed with a competitor primarily due to native POS integration; XSight\'s platform required a middleware layer their IT team declined to maintain. Price was explicitly ruled out as the deciding factor. The agent closed the door gracefully and secured permission for a future check-in once native integration ships.',
      customer_intent: 'Already decided — informing the agent of a completed competitor selection, not open to reconsidering now.',
      main_objection: 'competitor',
      customer_sentiment: 'neutral',
      call_outcome: 'No Sale',
      agent_performance_score: 4,
      lead_quality_score: 2,
      similar_calls: [
        { call_id: 'CALL_010', agent_name: 'Michael Ben-David', sale_result: 'No Sale', main_objection: 'competitor', similarity_score: 0.68, reason: 'CALL_010 also lost on a specific integration gap rather than price, with a similar clean loss and future-recontact agreement.' },
      ],
      coaching_feedback: [
        'Good discipline asking directly whether price mattered instead of assuming — that isolates the real objection (integration, not cost) for the loss report.',
        'The re-engagement ask at the end was well placed and low-pressure, appropriate once the decision was already made.',
      ],
      recommended_next_action: 'Log the native-POS-integration gap as a product feedback item and set a check-in reminder for roughly one quarter out.',
      suggested_follow_up_email:
        'Subject: Appreciate the transparency\n\nHi there,\n\nThanks for being upfront about the decision — I know that\'s not always the easy conversation to have. I\'ll flag the native POS integration gap internally, and with your OK, I\'ll check back in once that ships.\n\nBest,\nDaniel',
      routing_category: 'competitive_loss',
      confidence: 0.83,
      risk_level: 'Medium',
      detected_signals: ['deal already lost', 'integration gap named explicitly', 'price ruled out', 'future recontact agreed'],
      limitations: 'None significant — the customer stated the deciding factor directly, so this is a low-ambiguity read.',
      guardrail_status: 'pass',
    },
    evidence: { ragInsight: 'CALL_010 is the closest prior loss with the same competitor-integration pattern.', ragCitations: ['CALL_010'], signalDetectedSignals: ['deal already lost', 'integration gap named explicitly'], signalConfidence: 0.83, langgraphReasoningSteps: ['Reviewed structured extraction', 'Compared against CALL_010', 'No conflicting signals found'], langgraphEvidenceConflicts: [] },
  },

  // 3 — evidence_conflict example: forced into human_review_required by the Router rule.
  {
    callId: 'XS-1003',
    status: 'human_review_required',
    agentName: 'Michael Ben-David',
    callDate: '2026-07-21',
    customerName: 'Corrin Manufacturing',
    createdAt: '2026-07-21T16:20:00Z',
    callOutcome: 'Follow-up Needed',
    riskLevel: 'High',
    confidence: 0.74,
    guardrailStatus: 'human_review_required',
    audioDurationSeconds: 731,
    metadata: { agentName: 'Michael Ben-David', callDate: '2026-07-21', customerName: 'Corrin Manufacturing', audioFileName: 'call_corrin_mfg.mp3', audioDurationSeconds: 731 },
    analysis: {
      transcript:
        "Agent: So to confirm, you'd be the one signing off on this?\nCustomer: For the pilot, yes. Anything past twenty seats needs our VP.\nAgent: Got it. Where does the twenty-seat pilot sit in terms of priority right now?\nCustomer: High, honestly. Our current process is painful enough that I don't need convincing.\nAgent: That's great to hear. What would you need from me to get the pilot moving this month?\nCustomer: A contract I can sign without full procurement, and confirmation you can onboard us in two weeks.\nAgent: Two weeks is realistic for twenty seats. I'll get a pilot agreement over by tomorrow.\nCustomer: Perfect. I'm confident about this one.",
      call_summary:
        'Customer expressed high confidence and urgency for a twenty-seat pilot and asked for a fast-turnaround contract. The Call Signal Analyser scored this as high-risk based on deal-size and authority-scope patterns from similar historical calls, while the customer\'s own language and the RAG comparison both read as strongly positive — a direct conflict between the two evidence sources.',
      customer_intent: 'High urgency, self-reported authority for a bounded pilot scope, requesting an expedited contract.',
      main_objection: 'authority',
      customer_sentiment: 'positive',
      call_outcome: 'Follow-up Needed',
      agent_performance_score: 4,
      lead_quality_score: 3,
      similar_calls: [
        { call_id: 'CALL_003', agent_name: 'Daniel Cohen', sale_result: 'Sale', main_objection: 'authority', similarity_score: 0.69, reason: 'CALL_003 also had a scoped pilot-authority pattern and closed successfully.' },
      ],
      coaching_feedback: [
        'Confirming the authority boundary (pilot vs. VP sign-off) up front was the right move and should be repeated on every multi-seat deal.',
        'Given the Call Signal Analyser flags this deal-size/authority pattern as historically high-risk, it would be worth explicitly asking whether the VP has been informally consulted before sending a contract.',
      ],
      recommended_next_action: 'Send the pilot agreement, but confirm informal VP awareness before treating this as a near-certain close — the signal-analyser risk score and the transcript tone disagree and should be reconciled by a manager before the deal is forecast.',
      suggested_follow_up_email:
        'Subject: Pilot agreement — twenty seats\n\nHi there,\n\nAs promised, attached is the pilot agreement scoped to twenty seats with a two-week onboarding target. Let me know if you would like to loop in your VP proactively before signing, purely so there are no surprises at renewal.\n\nBest,\nMichael',
      routing_category: 'pilot_expansion',
      confidence: 0.74,
      risk_level: 'High',
      detected_signals: ['self-reported authority', 'high urgency language', 'expedited contract request', 'deal-size risk pattern flagged by signal analyser'],
      limitations: 'The Call Signal Analyser\'s risk scoring and the RAG/transcript evidence disagree on how confidently this should be forecast as a win — the customer\'s stated confidence and self-reported authority scope have not been independently verified. Routed for human review specifically because of this evidence conflict, not because of low confidence alone.',
      guardrail_status: 'human_review_required',
    },
    evidence: { ragInsight: 'CALL_003 is a similar scoped-pilot pattern that closed successfully.', ragCitations: ['CALL_003'], signalDetectedSignals: ['deal-size risk pattern', 'self-reported authority'], signalConfidence: 0.74, langgraphReasoningSteps: ['Reviewed structured extraction', 'Compared against CALL_003', 'Detected conflict between RAG-implied outcome and signal-analyser risk score'], langgraphEvidenceConflicts: ['RAG evidence and transcript tone suggest a likely win; Call Signal Analyser scores this deal pattern as High risk based on historical deal-size/authority-scope calls that stalled after this stage.'] },
    routerReasons: [{ code: 'evidence_conflict', label: 'Evidence conflict', detail: 'RAG evidence and Call Signal Analyser risk score disagree on this call\'s likely outcome.' }],
    humanReviewReasons: [{ code: 'evidence_conflict', label: 'Evidence conflict', detail: 'RAG evidence and Call Signal Analyser risk score disagree on this call\'s likely outcome.' }],
  },

  // 4 — the original demo fixture: low confidence, unresolved price objection, human review.
  {
    callId: 'XS-1004',
    status: 'human_review_required',
    agentName: 'Daniel Cohen',
    callDate: '2026-07-20',
    customerName: 'Maya Reyes — Northfield Retail',
    createdAt: '2026-07-20T09:15:00Z',
    callOutcome: 'Follow-up Needed',
    riskLevel: 'Medium',
    confidence: 0.58,
    guardrailStatus: 'human_review_required',
    audioDurationSeconds: 540,
    metadata: { agentName: 'Daniel Cohen', callDate: '2026-07-20', customerName: 'Maya Reyes — Northfield Retail', audioFileName: 'call_maya_reyes.mp3', audioDurationSeconds: 540 },
    analysis: {
      transcript:
        "Agent: Hi, this is Daniel from Northwind Solutions, thanks for hopping on the call. Am I speaking with Maya?\nCustomer: Yes, that's me. I've only got about fifteen minutes, just so you know.\nAgent: Totally fine, I'll keep it tight. Last time we spoke you mentioned the team was evaluating a few options for the onboarding automation piece. Where did that land?\nCustomer: We're still looking. Honestly the main thing holding us back is price. Your quote came in higher than the other vendor we're talking to.\nAgent: Understood — can I ask what they quoted, roughly, so I know what we're up against?\nCustomer: About twenty percent less, but their support model looked thinner. I don't know, we haven't decided.\nAgent: That's useful to know. Our support includes a dedicated onboarding specialist for the first ninety days, which usually cuts implementation time in half compared to self-serve. Would that matter for your team given the timeline you mentioned?\nCustomer: It might. We do need this live before Q4 planning starts. I just need to see the number work for our budget.\nAgent: Let me put together a revised proposal that breaks out the onboarding cost separately so you can compare apples to apples with the other vendor. Would early next week work to walk through it?\nCustomer: Yeah, Tuesday could work. Send something over before then so I can loop in my director.\nAgent: Will do — I'll email the breakdown by Friday so you have time to review before Tuesday.\nCustomer: Okay, sounds good. I do need to jump to another call now.\nAgent: No problem, thanks for the time, Maya — talk Tuesday.",
      call_summary:
        "Returning prospect Maya raised a price objection after comparing a competitor's quote that came in roughly 20% lower. The agent probed for the competitor's offer, positioned the dedicated 90-day onboarding specialist as a differentiator tied to her Q4 timeline, and secured a follow-up call for Tuesday with a proposal to be sent by Friday. The call ended on a scheduled next step rather than a resolved decision.",
      customer_intent: 'Evaluating onboarding automation vendors with an active budget comparison; leaning toward a decision before Q4 planning begins.',
      main_objection: 'price',
      customer_sentiment: 'neutral',
      call_outcome: 'Follow-up Needed',
      agent_performance_score: 4,
      lead_quality_score: 4,
      similar_calls: [
        { call_id: 'CALL_007', agent_name: 'Sarah Levi', sale_result: 'Sale', main_objection: 'price', similarity_score: 0.87, reason: 'CALL_007 also involved a competitor quote roughly 15-20% lower; the deal closed after the agent broke out onboarding/support value separately, mirroring the revised-proposal approach used in this call.' },
        { call_id: 'CALL_018', agent_name: 'Daniel Cohen', sale_result: 'No Sale', main_objection: 'price', similarity_score: 0.74, reason: 'CALL_018 shows a similar price objection but the customer disengaged after the follow-up proposal was sent late, missing the prospect\'s internal decision deadline.' },
        { call_id: 'CALL_023', agent_name: 'Noa Friedman', sale_result: 'Follow-up Needed', main_objection: 'price', similarity_score: 0.61, reason: 'CALL_023 shares the Q4-deadline urgency pattern, cited here only for the timing pressure dynamic, not the objection type.' },
      ],
      coaching_feedback: [
        "Good job probing for the competitor's actual quote instead of guessing — that number directly shaped the follow-up strategy.",
        "Consider quantifying the '90-day specialist' claim with a concrete implementation-time figure from a past customer; right now it's an assertion without a number behind it.",
        "The close was soft — 'Would early next week work' — a more direct ask ('Can we lock Tuesday at 2pm and get your director on the invite?') would reduce the risk of the follow-up slipping.",
      ],
      recommended_next_action: "Send the itemized proposal (base platform cost vs. onboarding/support cost) by Friday as promised, and confirm the Tuesday call includes Maya's director given the budget sign-off appears to sit above her.",
      suggested_follow_up_email:
        "Subject: Your itemized proposal, ahead of Tuesday\n\nHi Maya,\n\nThanks again for the time today. As promised, here is the breakdown so you and your director can compare line items directly against the other quote you're reviewing:\n\n- Platform license (annual)\n- Implementation & onboarding (90-day dedicated specialist)\n- Ongoing support tier\n\nI've kept these separate so it's easy to see where the cost difference actually comes from. Given the Q4 planning timeline you mentioned, the dedicated onboarding support typically cuts go-live time roughly in half versus a self-serve rollout — happy to share a reference customer if useful.\n\nLooking forward to Tuesday — let me know if there's a better time once your director confirms.\n\nBest,\nDaniel",
      routing_category: 'pricing_negotiation',
      confidence: 0.58,
      risk_level: 'Medium',
      detected_signals: ['price objection', 'competitor comparison in progress', 'Q4 deadline pressure', 'follow-up scheduled', 'decision-maker (director) not yet on call'],
      limitations: "Confidence for this analysis (0.58) fell below the 0.65 auto-approve threshold, primarily because the customer never confirmed the competitor's exact quote or whether her director has veto power over the final decision — both are inferred from indirect statements. The RAG comparison to CALL_023 is included only for the timing-pressure pattern, not the price objection, and should not be read as an outcome prediction. This result requires human review before being sent to the sales manager.",
      guardrail_status: 'human_review_required',
    },
    evidence: { ragInsight: 'Found 3 similar historical calls (CALL_007, CALL_018, CALL_023) — see each result\'s reason for the specific match.', ragCitations: ['CALL_007', 'CALL_018', 'CALL_023'], signalDetectedSignals: ['price objection', 'competitor comparison in progress', 'Q4 deadline pressure'], signalConfidence: 0.58, langgraphReasoningSteps: ['Reviewed structured extraction', 'Reviewed historical evidence', 'Reviewed call signal output', 'Synthesized coaching recommendation'], langgraphEvidenceConflicts: [] },
    routerReasons: [{ code: 'low_confidence', label: 'Low confidence', detail: 'Call Signal Analyser confidence (0.58) is below the 0.65 auto-approve threshold.' }],
    humanReviewReasons: [{ code: 'low_confidence', label: 'Low confidence', detail: "Neither the competitor's exact quote nor the director's decision authority was confirmed on the call — both are inferred." }],
  },

  // 5 — high-cost long call, clean Sale.
  {
    callId: 'XS-1005',
    status: 'completed',
    agentName: 'Noa Friedman',
    callDate: '2026-07-18',
    customerName: 'Basalt & Kerr Financial',
    createdAt: '2026-07-18T13:00:00Z',
    callOutcome: 'Sale',
    riskLevel: 'Low',
    confidence: 0.88,
    guardrailStatus: 'pass',
    audioDurationSeconds: 1487,
    metadata: { agentName: 'Noa Friedman', callDate: '2026-07-18', customerName: 'Basalt & Kerr Financial', audioFileName: 'call_basalt_kerr.mp3', audioDurationSeconds: 1487 },
    analysis: {
      transcript:
        "Agent: Thanks for the extended slot today — I know compliance review took a while to schedule.\nCustomer: Yeah, our security team wanted the full hour. They had a long list.\nAgent: Happy to work through it. Want to start with data residency or access controls?\nCustomer: Residency first — everything needs to stay in-region for us.\nAgent: Understood, we can pin your deployment to your region contractually. Next?\nCustomer: SOC 2 report and our audit team's usual sub-processor questionnaire.\nAgent: I'll get both to you today. Anything on the access-control side?\nCustomer: SSO enforcement and audit logging retention — minimum one year.\nAgent: We support both natively, retention is configurable well past a year if needed.\nCustomer: Good. Assuming all that checks out, we're ready to move to contract.\nAgent: I'll have the security packet over within the hour, and we can get the contract moving in parallel so we don't lose time.\nCustomer: Appreciate that. Let's do it.",
      call_summary:
        'Extended (nearly 25-minute) security and compliance review call with a financial-services prospect. The agent addressed data residency, SOC 2, sub-processor questionnaire, SSO, and audit-log retention requirements directly, and the customer confirmed readiness to move to contract pending the security packet.',
      customer_intent: 'Final technical/compliance gate before contracting; decision is effectively made pending documentation.',
      main_objection: 'none',
      customer_sentiment: 'positive',
      call_outcome: 'Sale',
      agent_performance_score: 5,
      lead_quality_score: 5,
      similar_calls: [],
      coaching_feedback: ['Letting the customer set the review order (residency first) rather than following a fixed script kept the call efficient given the long topic list.'],
      recommended_next_action: 'Send the SOC 2 report and sub-processor questionnaire within the hour as promised, and start the contract in parallel per the customer\'s explicit request.',
      suggested_follow_up_email:
        'Subject: Security packet + contract moving in parallel\n\nHi there,\n\nAs discussed, attached is our SOC 2 report and the completed sub-processor questionnaire. Starting the contract in parallel now so we do not lose time — happy to answer any follow-up security questions along the way.\n\nBest,\nNoa',
      routing_category: 'security_compliance_review',
      confidence: 0.88,
      risk_level: 'Low',
      detected_signals: ['extended compliance review', 'explicit readiness to contract', 'no unresolved objections'],
      limitations: 'No similar historical calls cleared the similarity threshold for this specialized compliance-review pattern — the RAG comparison returned no citations, which is expected for a call this specific rather than a grounding gap.',
      guardrail_status: 'pass',
    },
    evidence: { ragInsight: 'Not enough evidence to identify similar historical calls for this transcript.', ragCitations: [], signalDetectedSignals: ['extended compliance review', 'explicit readiness to contract'], signalConfidence: 0.88, langgraphReasoningSteps: ['Reviewed structured extraction', 'No comparable historical calls found', 'No conflicting signals found'], langgraphEvidenceConflicts: [] },
  },

  // 6 — flagged (output guardrail issue), not the same as human_review.
  {
    callId: 'XS-1006',
    status: 'flagged',
    agentName: 'Sarah Levi',
    callDate: '2026-07-17',
    customerName: 'Devani Home Goods',
    createdAt: '2026-07-17T11:30:00Z',
    callOutcome: 'Follow-up Needed',
    riskLevel: 'Medium',
    confidence: 0.79,
    guardrailStatus: 'flagged',
    audioDurationSeconds: 455,
    metadata: { agentName: 'Sarah Levi', callDate: '2026-07-17', customerName: 'Devani Home Goods', audioFileName: 'call_devani_home.mp3', audioDurationSeconds: 455 },
    analysis: {
      transcript:
        "Agent: Where did the timeline land after last week's internal discussion?\nCustomer: We're leaning toward Q1 now, not this quarter — budget cycle reasons.\nAgent: That makes sense. Anything I can do now to make Q1 an easy yes?\nCustomer: Just don't let the quote expire, I guess.\nAgent: Noted, I'll make sure pricing holds. I'll check back in early Q1.\nCustomer: Sounds good.",
      call_summary:
        'Prospect pushed the decision to Q1 for budget-cycle reasons and asked only that the current quote remain valid. Short, low-friction call with a clear timing objection and no new information beyond the deferral itself.',
      customer_intent: 'Interested but budget-cycle constrained; deferring rather than declining.',
      main_objection: 'timing',
      customer_sentiment: 'neutral',
      call_outcome: 'Follow-up Needed',
      agent_performance_score: 3,
      lead_quality_score: 3,
      similar_calls: [
        { call_id: 'CALL_014', agent_name: 'Michael Ben-David', sale_result: 'Sale', main_objection: 'timing', similarity_score: 0.58, reason: 'CALL_014 also involved a budget-cycle deferral pattern.' },
      ],
      coaching_feedback: ['The call was efficient but passive — a specific Q1 date to reconnect (rather than "early Q1") would reduce the chance this slips.'],
      recommended_next_action: 'Confirm the quote validity in writing and schedule a specific early-January check-in rather than leaving "early Q1" open-ended.',
      suggested_follow_up_email: 'Subject: Holding your quote for Q1\n\nHi there,\n\nConfirming your current quote will remain valid through Q1. I will reach back out the first week of January — let me know if a different date works better.\n\nBest,\nSarah',
      routing_category: 'deferred_budget_cycle',
      confidence: 0.79,
      risk_level: 'Medium',
      detected_signals: ['timing objection', 'budget cycle deferral', 'quote-hold request'],
      limitations: 'This result was flagged by output guardrails for review of the price-hold commitment language before it is sent externally, out of caution — not because the underlying analysis is unsupported.',
      guardrail_status: 'flagged',
    },
    evidence: { ragInsight: 'CALL_014 shares the budget-cycle deferral pattern.', ragCitations: ['CALL_014'], signalDetectedSignals: ['timing objection', 'budget cycle deferral'], signalConfidence: 0.79, langgraphReasoningSteps: ['Reviewed structured extraction', 'Compared against CALL_014'], langgraphEvidenceConflicts: [] },
    routerReasons: [{ code: 'guardrail_flag', label: 'Guardrail flag', detail: 'The draft follow-up email\'s pricing-hold commitment was flagged for manager review before sending.' }],
  },

  // 7 — failed processing (transcription failure, no analysis produced).
  {
    callId: 'XS-1007',
    status: 'failed',
    agentName: 'Daniel Cohen',
    callDate: '2026-07-16',
    customerName: undefined,
    createdAt: '2026-07-16T15:50:00Z',
    guardrailStatus: undefined,
    audioDurationSeconds: undefined,
    metadata: { agentName: 'Daniel Cohen', callDate: '2026-07-16', audioFileName: 'call_0716_1550.wav' },
    failureReason: 'Transcription failed: AssemblyAI reported an unsupported audio codec after 3 retries. The uploaded file could not be transcribed.',
  },

  // 8 — in progress (analyzing).
  {
    callId: 'XS-1008',
    status: 'analyzing',
    agentName: 'Michael Ben-David',
    callDate: '2026-07-27',
    customerName: 'Prellwood Industrial',
    createdAt: '2026-07-27T08:12:00Z',
    metadata: { agentName: 'Michael Ben-David', callDate: '2026-07-27', customerName: 'Prellwood Industrial', audioFileName: 'call_prellwood.mp3' },
  },

  // 9 — just uploaded.
  {
    callId: 'XS-1009',
    status: 'uploaded',
    agentName: 'Noa Friedman',
    callDate: '2026-07-27',
    customerName: 'Castellane Retail',
    createdAt: '2026-07-27T09:02:00Z',
    metadata: { agentName: 'Noa Friedman', callDate: '2026-07-27', customerName: 'Castellane Retail', audioFileName: 'call_castellane.mp3' },
  },

  // 10 — clean No Sale, trust objection, pairs with a high-quality RAGAS evaluation in mocks.
  {
    callId: 'XS-1010',
    status: 'completed',
    agentName: 'Sarah Levi',
    callDate: '2026-07-14',
    customerName: 'Amberveil Consulting',
    createdAt: '2026-07-14T12:00:00Z',
    callOutcome: 'No Sale',
    riskLevel: 'Low',
    confidence: 0.93,
    guardrailStatus: 'pass',
    audioDurationSeconds: 389,
    metadata: { agentName: 'Sarah Levi', callDate: '2026-07-14', customerName: 'Amberveil Consulting', audioFileName: 'call_amberveil.mp3', audioDurationSeconds: 389 },
    analysis: {
      transcript:
        "Agent: You mentioned some hesitation last time around data handling — where are you on that?\nCustomer: We looked into it more and honestly, we're not comfortable with a third party touching client records at all right now. It's not about your platform specifically.\nAgent: That's a fair line to hold. Is that a permanent policy or something that could change?\nCustomer: Permanent, for the foreseeable future. Board-level decision.\nAgent: Understood, I won't push on that. I'll close this out on our end — appreciate you telling me directly rather than going quiet.\nCustomer: Of course, wasn't fair to leave you hanging.",
      call_summary: 'Customer confirmed a board-level policy against any third-party handling of client records, unrelated to the product itself. The agent respected the boundary and closed the opportunity cleanly rather than continuing to pursue it.',
      customer_intent: 'Declining for policy reasons unrelated to product fit; not a live prospect.',
      main_objection: 'trust',
      customer_sentiment: 'neutral',
      call_outcome: 'No Sale',
      agent_performance_score: 4,
      lead_quality_score: 1,
      similar_calls: [],
      coaching_feedback: ['Correctly recognized this as a policy-level objection rather than a persuadable one, and did not waste further effort — good judgment on when to close a loss cleanly.'],
      recommended_next_action: 'Close the opportunity as lost (trust/policy) and remove from active pipeline; no further follow-up warranted given the board-level constraint.',
      suggested_follow_up_email: 'Subject: Understood, and thank you\n\nHi there,\n\nThanks for the direct update — completely understand the position given the board policy. I\'ll close this out on my end. Wishing you well, and the door is open if that ever changes.\n\nBest,\nSarah',
      routing_category: 'policy_decline',
      confidence: 0.93,
      risk_level: 'Low',
      detected_signals: ['board-level policy objection', 'clean decline', 'no product-fit concern raised'],
      limitations: 'None — the customer stated the reason for declining explicitly and unambiguously.',
      guardrail_status: 'pass',
    },
    evidence: { ragInsight: 'Not enough evidence to identify similar historical calls for this transcript.', ragCitations: [], signalDetectedSignals: ['board-level policy objection', 'clean decline'], signalConfidence: 0.93, langgraphReasoningSteps: ['Reviewed structured extraction', 'No comparable historical calls found'], langgraphEvidenceConflicts: [] },
  },

  // 11 — borderline-confidence Sale, pairs with a weak-faithfulness RAGAS evaluation in mocks.
  {
    callId: 'XS-1011',
    status: 'completed',
    agentName: 'Daniel Cohen',
    callDate: '2026-07-12',
    customerName: 'Thorncastle Media',
    createdAt: '2026-07-12T17:25:00Z',
    callOutcome: 'Sale',
    riskLevel: 'Medium',
    confidence: 0.68,
    guardrailStatus: 'pass',
    audioDurationSeconds: 603,
    metadata: { agentName: 'Daniel Cohen', callDate: '2026-07-12', customerName: 'Thorncastle Media', audioFileName: 'call_thorncastle.mp3', audioDurationSeconds: 603 },
    analysis: {
      transcript:
        "Agent: So where do things stand after the trial period?\nCustomer: Good enough, I think. The team didn't complain much, which for us is basically a win.\nAgent: I'll take that as a compliment. Ready to move forward on the annual plan?\nCustomer: Sure, let's do it. Send whatever you need signed.\nAgent: Great, I'll get the paperwork over today.",
      call_summary: 'Customer confirmed a successful (if lightly described) trial period and agreed to move forward on the annual plan with minimal further discussion.',
      customer_intent: 'Ready to commit based on a low-friction trial; not much elaboration given.',
      main_objection: 'none',
      customer_sentiment: 'neutral',
      call_outcome: 'Sale',
      agent_performance_score: 3,
      lead_quality_score: 3,
      similar_calls: [{ call_id: 'CALL_018', agent_name: 'Daniel Cohen', sale_result: 'No Sale', main_objection: 'price', similarity_score: 0.52, reason: 'Weak match — cited mainly for the same agent\'s call cadence, not the objection type.' }],
      coaching_feedback: ['The call closed, but very little was actually confirmed about trial outcomes — worth a proper trial-results conversation on future renewals rather than relying on "the team didn\'t complain."'],
      recommended_next_action: 'Send the annual contract today per the customer\'s request, and separately schedule a brief trial-outcomes debrief for better renewal documentation next cycle.',
      suggested_follow_up_email: 'Subject: Annual plan paperwork\n\nHi there,\n\nGreat news — attached is the annual plan agreement we discussed. Let me know if anything needs adjusting before signature.\n\nBest,\nDaniel',
      routing_category: 'trial_conversion',
      confidence: 0.68,
      risk_level: 'Medium',
      detected_signals: ['trial converted', 'thin supporting detail', 'low-friction agreement'],
      limitations: 'The transcript is unusually short and light on specifics about the trial itself, which limits how much the extracted fields can be independently verified beyond the customer\'s brief confirmation.',
      guardrail_status: 'pass',
    },
    evidence: { ragInsight: 'Only a weak match was found; treat as low-confidence supporting context, not a strong precedent.', ragCitations: ['CALL_018'], signalDetectedSignals: ['trial converted', 'thin supporting detail'], signalConfidence: 0.68, langgraphReasoningSteps: ['Reviewed structured extraction', 'Compared against CALL_018 (weak match)'], langgraphEvidenceConflicts: [] },
  },
]
