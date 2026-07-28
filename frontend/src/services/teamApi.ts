import type { TeamInsight, TeamPerformanceSummary } from '../types'
import { isMockMode, simulateLatency } from './config'
import { mockTeamInsight, mockTeamPerformanceSummary } from '../data/mockTeam'

export interface TeamIntelligenceData {
  insight: TeamInsight
  summary: TeamPerformanceSummary
}

export async function getTeamIntelligence(): Promise<TeamIntelligenceData> {
  if (!isMockMode()) {
    throw new Error('teamApi.getTeamIntelligence: no backend contract exists yet for team-level analytics.')
  }
  await simulateLatency(400)
  return { insight: mockTeamInsight, summary: mockTeamPerformanceSummary }
}
