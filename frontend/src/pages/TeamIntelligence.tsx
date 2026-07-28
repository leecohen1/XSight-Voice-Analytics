import { useEffect, useState } from 'react'
import { getTeamIntelligence, type TeamIntelligenceData } from '../services/teamApi'
import PageHeader from '../components/ui/PageHeader'
import SectionCard from '../components/ui/SectionCard'
import MetricCard from '../components/ui/MetricCard'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import StatusBadge from '../components/ui/StatusBadge'
import TrendSparkline from '../components/charts/TrendSparkline'
import styles from './TeamIntelligence.module.css'

function initials(name: string): string {
  return name
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export default function TeamIntelligence() {
  const [data, setData] = useState<TeamIntelligenceData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getTeamIntelligence()
      .then((result) => !cancelled && setData(result))
      .catch((err) => !cancelled && setError(err instanceof Error ? err.message : String(err)))
    return () => {
      cancelled = true
    }
  }, [])

  if (error) {
    return (
      <>
        <PageHeader title="Team Intelligence" />
        <ErrorState description={error} />
      </>
    )
  }

  if (!data) {
    return (
      <>
        <PageHeader title="Team Intelligence" />
        <LoadingSkeleton lines={6} />
      </>
    )
  }

  const { insight, summary } = data

  return (
    <>
      <section className={styles.hero}>
        <div className={styles.heroText}>
          <span className={styles.heroEyebrow}>Coaching & Performance</span>
          <h1 className={styles.heroTitle}>{insight.headline}</h1>
          <p className={styles.heroDetail}>{insight.detail}</p>
        </div>
      </section>

      <div className={styles.summaryGrid}>
        <MetricCard tone="violet" label="Team Avg. Agent Performance" value={summary.teamAverageAgentPerformance.toFixed(1)} helpText="out of 5" />
        <MetricCard tone="secondary" label="Team Avg. Lead Quality" value={summary.teamAverageLeadQuality.toFixed(1)} helpText="out of 5" />
      </div>

      <SectionCard title="Performance Trend" subtitle={`${summary.periodStart} – ${summary.periodEnd}`}>
        <TrendSparkline data={summary.performanceTrend} color="var(--color-status-review)" formatValue={(v) => v.toFixed(1)} />
      </SectionCard>

      <div className={styles.columns}>
        <SectionCard title="Agent Performance Summary" subtitle="Coaching view — not a ranking">
          <div className={styles.agentList}>
            {summary.agents.map((agent) => (
              <div className={styles.agentCard} key={agent.agentName}>
                <span className={styles.agentAvatar} aria-hidden="true">
                  {initials(agent.agentName)}
                </span>
                <div className={styles.agentInfo}>
                  <div className={styles.agentName}>{agent.agentName}</div>
                  <div className={styles.agentSkillRow}>
                    <span className={styles.agentSkillLabel}>Strength</span>
                    <span>{agent.strongestSkill}</span>
                  </div>
                  <div className={styles.agentSkillRow}>
                    <span className={styles.agentGrowthLabel}>Growth</span>
                    <span>{agent.growthArea}</span>
                  </div>
                </div>
                <div className={styles.agentMetrics}>
                  <div className={styles.metricRow}>
                    <span className={styles.metricLabel}>Perf.</span>
                    <span className={styles.metricTrack}>
                      <span className={styles.metricFill} style={{ width: `${(agent.averageAgentPerformance / 5) * 100}%` }} />
                    </span>
                    <span className={styles.metricValue}>{agent.averageAgentPerformance.toFixed(1)}</span>
                  </div>
                  <div className={styles.metricRow}>
                    <span className={styles.metricLabel}>Lead</span>
                    <span className={styles.metricTrack}>
                      <span className={styles.metricFill} style={{ width: `${(agent.averageLeadQuality / 5) * 100}%` }} />
                    </span>
                    <span className={styles.metricValue}>{agent.averageLeadQuality.toFixed(1)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Recurring Sales Patterns">
          <ul className={styles.patternList}>
            {summary.recurringPatterns.map((pattern, i) => (
              <li key={i}>{pattern}</li>
            ))}
          </ul>
        </SectionCard>
      </div>

      <SectionCard title="Coaching Opportunities">
        {summary.coachingOpportunities.map((opp) => (
          <div className={styles.opportunity} key={opp.id}>
            <div className={styles.opportunityTitle}>{opp.title}</div>
            <p className={styles.opportunityDescription}>{opp.description}</p>
            <div className={styles.opportunityAgents}>
              {opp.affectedAgents.map((name) => (
                <StatusBadge key={name} label={name} tone="neutral" />
              ))}
            </div>
          </div>
        ))}
      </SectionCard>
    </>
  )
}
