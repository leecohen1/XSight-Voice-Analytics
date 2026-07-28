import { useCallback, useEffect, useState } from 'react'
import { getTeamIntelligence, type TeamIntelligenceData } from '../services/teamApi'
import { ATTENTION_CATEGORY_LABELS, type AgentTrendDirection } from '../types'
import PageHeader from '../components/ui/PageHeader'
import SectionCard from '../components/ui/SectionCard'
import MetricCard from '../components/ui/MetricCard'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import EmptyState from '../components/ui/EmptyState'
import StatusBadge, { type StatusTone } from '../components/ui/StatusBadge'
import Button from '../components/ui/Button'
import TrendSparkline from '../components/charts/TrendSparkline'
import { TeamIcon } from '../components/icons'
import styles from './TeamIntelligence.module.css'

function initials(name: string): string {
  return name
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

/** Renders a null score as an explicit dash rather than a misleading 0.0. */
function score(value: number | null): string {
  return value === null ? '—' : value.toFixed(1)
}

const TREND_LABEL: Record<AgentTrendDirection, string> = {
  improving: 'Improving',
  declining: 'Needs coaching',
  flat: 'Steady',
  unknown: 'Not enough calls',
}

const TREND_TONE: Record<AgentTrendDirection, StatusTone> = {
  improving: 'success',
  declining: 'warning',
  flat: 'neutral',
  unknown: 'neutral',
}


export default function TeamIntelligence() {
  const [data, setData] = useState<TeamIntelligenceData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  const retry = useCallback(() => {
    setError(null)
    setData(null)
    setReloadToken((n) => n + 1)
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    let cancelled = false
    getTeamIntelligence(controller.signal)
      .then((result) => !cancelled && setData(result))
      .catch((err) => {
        if (cancelled || controller.signal.aborted) return
        setError(err instanceof Error ? err.message : String(err))
      })
    return () => {
      cancelled = true
      controller.abort()
    }
  }, [reloadToken])

  if (error) {
    return (
      <>
        <PageHeader title="Team Intelligence" />
        <ErrorState
          description={error}
          action={
            <Button variant="secondary" onClick={retry} type="button">
              Retry
            </Button>
          }
        />
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

  if (summary.callsAnalyzed === 0) {
    return (
      <>
        <PageHeader title="Team Intelligence" />
        <EmptyState icon={<TeamIcon size={18} />} title={insight.headline} description={insight.detail} />
      </>
    )
  }

  return (
    <>
      <section className={styles.hero}>
        <div className={styles.heroText}>
          <span className={styles.heroEyebrow}>Coaching &amp; Performance</span>
          <h1 className={styles.heroTitle}>{insight.headline}</h1>
          <p className={styles.heroDetail}>{insight.detail}</p>
        </div>
      </section>

      <div className={styles.summaryGrid}>
        <MetricCard tone="violet" label="Team Avg. Agent Performance" value={score(summary.teamAverageAgentPerformance)} helpText="out of 5" />
        <MetricCard tone="secondary" label="Team Avg. Lead Quality" value={score(summary.teamAverageLeadQuality)} helpText="out of 5" />
        <MetricCard tone="primary" label="Calls Analyzed" value={String(summary.callsAnalyzed)} helpText={`${summary.periodStart} – ${summary.periodEnd}`} />
        <MetricCard tone="secondary" label="Calls Needing Attention" value={String(summary.attentionCalls)} helpText="flagged by the router" />
      </div>

      <SectionCard title="Performance Trend" subtitle={`Average agent performance per day · ${summary.periodStart} – ${summary.periodEnd}`}>
        {summary.performanceTrend.length > 0 ? (
          <TrendSparkline data={summary.performanceTrend} color="var(--color-status-review)" formatValue={(v) => v.toFixed(1)} />
        ) : (
          <p className={styles.opportunityDescription}>No scored calls yet in this range.</p>
        )}
      </SectionCard>

      <div className={styles.columns}>
        <SectionCard title="Representatives" subtitle="Coaching view — sorted by calls needing attention, not a ranking">
          <div className={styles.agentList}>
            {summary.agents.map((agent) => (
              <div className={styles.agentCard} key={agent.agentName}>
                <span className={styles.agentAvatar} aria-hidden="true">
                  {initials(agent.agentName)}
                </span>
                <div className={styles.agentInfo}>
                  <div className={styles.agentName}>{agent.agentName}</div>
                  <div className={styles.agentSkillRow}>
                    <span className={styles.agentSkillLabel}>Calls</span>
                    <span>
                      {agent.callsAnalyzed}
                      {agent.closeRate !== null ? ` · ${agent.closeRate.toFixed(0)}% close rate` : ''}
                    </span>
                  </div>
                  <div className={styles.agentSkillRow}>
                    <span className={styles.agentGrowthLabel}>Trend</span>
                    <StatusBadge
                      label={
                        agent.trendDelta !== null && agent.trendDirection !== 'unknown'
                          ? `${TREND_LABEL[agent.trendDirection]} (${agent.trendDelta > 0 ? '+' : ''}${agent.trendDelta.toFixed(1)})`
                          : TREND_LABEL[agent.trendDirection]
                      }
                      tone={TREND_TONE[agent.trendDirection]}
                    />
                  </div>
                  {agent.attentionCalls > 0 && (
                    <div className={styles.agentSkillRow}>
                      <span className={styles.agentGrowthLabel}>Attention</span>
                      <span>
                        {agent.attentionCalls} call{agent.attentionCalls === 1 ? '' : 's'} flagged
                      </span>
                    </div>
                  )}
                </div>
                <div className={styles.agentMetrics}>
                  <div className={styles.metricRow}>
                    <span className={styles.metricLabel}>Perf.</span>
                    <span className={styles.metricTrack}>
                      <span
                        className={styles.metricFill}
                        style={{ width: `${((agent.averageAgentPerformance ?? 0) / 5) * 100}%` }}
                      />
                    </span>
                    <span className={styles.metricValue}>{score(agent.averageAgentPerformance)}</span>
                  </div>
                  <div className={styles.metricRow}>
                    <span className={styles.metricLabel}>Lead</span>
                    <span className={styles.metricTrack}>
                      <span
                        className={styles.metricFill}
                        style={{ width: `${((agent.averageLeadQuality ?? 0) / 5) * 100}%` }}
                      />
                    </span>
                    <span className={styles.metricValue}>{score(agent.averageLeadQuality)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Outcome Mix" subtitle="Across every analyzed call in range">
          <ul className={styles.patternList}>
            {summary.outcomeBreakdown.map((entry) => (
              <li key={entry.outcome}>
                {entry.outcome} — {entry.count} call{entry.count === 1 ? '' : 's'}
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>

      <SectionCard title="Attention Categories" subtitle="Router-assigned priority reasons, aggregated across the team">
        {summary.attentionBreakdown.length === 0 ? (
          <p className={styles.opportunityDescription}>No calls are currently flagged for attention.</p>
        ) : (
          <div className={styles.opportunityAgents}>
            {summary.attentionBreakdown.map((entry) => (
              <StatusBadge
                key={entry.category}
                label={`${ATTENTION_CATEGORY_LABELS[entry.category]} · ${entry.count}`}
                tone="neutral"
              />
            ))}
          </div>
        )}
      </SectionCard>
    </>
  )
}
