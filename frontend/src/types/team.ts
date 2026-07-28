/**
 * Team Intelligence domain types — frontend-facing, mock-backed this phase.
 * No backend contract exists yet for team-level aggregation.
 */
import type { TrendPoint } from './aiOperations'

export interface TeamInsight {
  id: string
  headline: string
  detail: string
  generatedAt: string
}

export interface AgentPerformanceSummary {
  agentName: string
  callsAnalyzed: number
  averageAgentPerformance: number
  averageLeadQuality: number
  strongestSkill: string
  growthArea: string
}

export interface CoachingOpportunity {
  id: string
  title: string
  description: string
  affectedAgents: string[]
}

export interface TeamPerformanceSummary {
  periodStart: string
  periodEnd: string
  teamAverageAgentPerformance: number
  teamAverageLeadQuality: number
  performanceTrend: TrendPoint[]
  agents: AgentPerformanceSummary[]
  recurringPatterns: string[]
  coachingOpportunities: CoachingOpportunity[]
}
