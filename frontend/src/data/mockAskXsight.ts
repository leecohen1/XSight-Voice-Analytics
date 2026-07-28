import type { AskXsightQuestion } from '../types'

/**
 * The general suggested-question bank (CLAUDE.md §9.5). `askXsightApi`
 * filters this down per call based on what evidence that call actually has
 * (e.g. the "why is human review required" question only surfaces for calls
 * routed to review), so a call never suggests a question it can't ground an
 * answer to.
 */
export const suggestedQuestionBank: AskXsightQuestion[] = [
  { id: 'q-risk', text: 'Why was this call marked as high risk?' },
  { id: 'q-objection-evidence', text: 'What evidence supports the main objection?' },
  { id: 'q-human-review', text: 'Why is human review required?' },
  { id: 'q-compare-similar', text: 'Compare this call with the most similar successful call.' },
  { id: 'q-coaching', text: 'Explain the coaching recommendation.' },
  { id: 'q-agent-score', text: 'Which transcript moments influenced the agent score?' },
  { id: 'q-limitations', text: 'What limitations should I be aware of?' },
  { id: 'q-ragas-drop', text: 'Why did the RAGAS faithfulness score decrease?' },
  // Deliberately unanswerable from this call's evidence — demos "Not enough
  // evidence" without needing the user to phrase an unusual question.
  { id: 'q-unrelated-crm', text: "What's this customer's total CRM lifetime value?" },
]
