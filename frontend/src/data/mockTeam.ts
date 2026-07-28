import type { TeamPerformanceSummary, TeamInsight } from '../types'

export const mockTeamInsight: TeamInsight = {
  id: 'insight-2026-07',
  headline: 'Closing technique is the team\'s strongest coaching opportunity this month.',
  detail:
    'Across the last 30 days, agents consistently handle objections well but frequently end calls with a soft, open-ended ask ("would next week work?") instead of a specific, confirmed next step — a pattern showing up in 4 of the last 6 reviewed calls.',
  generatedAt: '2026-07-27T07:00:00Z',
}

export const mockTeamPerformanceSummary: TeamPerformanceSummary = {
  periodStart: '2026-06-27',
  periodEnd: '2026-07-27',
  teamAverageAgentPerformance: 4.0,
  teamAverageLeadQuality: 3.4,
  performanceTrend: [
    { date: '2026-06-27', value: 3.6 },
    { date: '2026-07-03', value: 3.7 },
    { date: '2026-07-10', value: 3.9 },
    { date: '2026-07-17', value: 3.8 },
    { date: '2026-07-24', value: 4.0 },
  ],
  agents: [
    {
      agentName: 'Sarah Levi',
      callsAnalyzed: 3,
      averageAgentPerformance: 4.0,
      averageLeadQuality: 3.3,
      strongestSkill: 'Quantifying customer pain points before pitching a solution',
      growthArea: 'Confirming pricing-related commitments before they reach the follow-up email',
    },
    {
      agentName: 'Daniel Cohen',
      callsAnalyzed: 3,
      averageAgentPerformance: 3.7,
      averageLeadQuality: 2.7,
      strongestSkill: 'Staying composed and gathering clean information on losses',
      growthArea: 'Using a firmer, date-specific close instead of open-ended scheduling asks',
    },
    {
      agentName: 'Michael Ben-David',
      callsAnalyzed: 2,
      averageAgentPerformance: 4.0,
      averageLeadQuality: 3.0,
      strongestSkill: 'Clarifying decision-making authority early in the call',
      growthArea: 'Verifying self-reported urgency against independent evidence before forecasting',
    },
    {
      agentName: 'Noa Friedman',
      callsAnalyzed: 2,
      averageAgentPerformance: 5.0,
      averageLeadQuality: 5.0,
      strongestSkill: 'Running structured, efficient technical/compliance review calls',
      growthArea: 'Sample size this period is small — validate the trend over more calls',
    },
  ],
  recurringPatterns: [
    'Price objections are most often resolved by separating platform cost from onboarding/support cost in the follow-up proposal, not by discounting.',
    'Calls that explicitly confirm the decision-maker\'s presence or involvement close at a noticeably higher rate than calls that leave it assumed.',
    'Soft, open-ended scheduling language ("would next week work?") correlates with follow-ups slipping past the committed date.',
  ],
  coachingOpportunities: [
    {
      id: 'coaching-1',
      title: 'Replace open-ended follow-up asks with a specific date and attendee',
      description: 'Several calls end with a vague scheduling ask rather than a confirmed date, time, and named attendee — the single most common closing weakness this period.',
      affectedAgents: ['Daniel Cohen', 'Sarah Levi'],
    },
    {
      id: 'coaching-2',
      title: 'Verify self-reported urgency and authority before forecasting a deal',
      description: 'High-confidence customer language is not always independently corroborated — cross-check against the Call Signal Analyser\'s risk score before treating a deal as near-certain.',
      affectedAgents: ['Michael Ben-David'],
    },
  ],
}
