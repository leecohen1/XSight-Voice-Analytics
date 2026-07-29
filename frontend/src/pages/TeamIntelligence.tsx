import { useCallback, useEffect, useState } from 'react'
import { getTeamIntelligence, type TeamIntelligenceData } from '../services/teamApi'
import { ATTENTION_CATEGORY_LABELS, type OverviewPeriod } from '../types'
import PageHeader from '../components/ui/PageHeader'
import SectionCard from '../components/ui/SectionCard'
import MetricCard from '../components/ui/MetricCard'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import EmptyState from '../components/ui/EmptyState'
import StatusBadge from '../components/ui/StatusBadge'
import Button from '../components/ui/Button'
import RankedBarChart, { type RankedBar } from '../components/charts/RankedBarChart'
import { TeamIcon } from '../components/icons'
import styles from './TeamIntelligence.module.css'

const PERIOD_OPTIONS: { value: OverviewPeriod; label: string }[] = [
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
]

/** Renders a null score as an explicit dash rather than a misleading 0.0. */
function score(value: number | null): string {
  return value === null ? '—' : value.toFixed(1)
}

const TREND_META: Record<string, string> = {
  improving: 'Improving',
  declining: 'Needs coaching',
  flat: 'Steady',
  unknown: '',
}

export default function TeamIntelligence() {
  const [period, setPeriod] = useState<OverviewPeriod>('7d')
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
    setData(null)
    setError(null)
    getTeamIntelligence(period, controller.signal)
      .then((result) => !cancelled && setData(result))
      .catch((err) => {
        if (cancelled || controller.signal.aborted) return
        setError(err instanceof Error ? err.message : String(err))
      })
    return () => {
      cancelled = true
      controller.abort()
    }
  }, [period, reloadToken])

  const periodSelector = (
    <div className={styles.periodSelector} role="group" aria-label="Reporting period">
      {PERIOD_OPTIONS.map((option) => (
        <button
          key={option.value}
          type="button"
          className={period === option.value ? styles.periodActive : styles.periodButton}
          aria-pressed={period === option.value}
          onClick={() => setPeriod(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )

  if (error) {
    return (
      <>
        <PageHeader title="Team Intelligence" actions={periodSelector} />
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
        <PageHeader title="Team Intelligence" actions={periodSelector} />
        <LoadingSkeleton lines={6} />
      </>
    )
  }

  const { insight, summary } = data

  if (summary.callsAnalyzed === 0) {
    return (
      <>
        <PageHeader title="Team Intelligence" actions={periodSelector} />
        <EmptyState icon={<TeamIcon size={18} />} title={insight.headline} description={insight.detail} />
      </>
    )
  }

  // Sorted ascending (weakest first) so the manager sees who may need
  // coaching before who is already doing well -- a fixed 0..5 domain means
  // a 0.3 gap between two reps is never drawn as if it were a 3-point gap.
  const bars: RankedBar[] = [...summary.agents]
    .sort((a, b) => (a.averageAgentPerformance ?? -1) - (b.averageAgentPerformance ?? -1))
    .map((agent) => {
      const metaParts: string[] = []
      if (agent.closeRate !== null) metaParts.push(`${agent.closeRate.toFixed(0)}% close rate`)
      if (agent.attentionCalls > 0) metaParts.push(`${agent.attentionCalls} need${agent.attentionCalls === 1 ? 's' : ''} attention`)
      const trendLabel = TREND_META[agent.trendDirection]
      if (trendLabel) metaParts.push(agent.trendDelta !== null ? `${trendLabel} (${agent.trendDelta > 0 ? '+' : ''}${agent.trendDelta.toFixed(1)})` : trendLabel)

      return {
        key: agent.agentName,
        label: agent.agentName,
        value: agent.averageAgentPerformance,
        sampleSize: agent.callsAnalyzed,
        meta: metaParts.join(' · '),
        href: `/calls?agent=${encodeURIComponent(agent.agentName)}`,
      }
    })

  return (
    <>
      <section className={styles.hero}>
        <div className={styles.heroText}>
          <span className={styles.heroEyebrow}>Coaching &amp; Performance</span>
          <h1 className={styles.heroTitle}>{insight.headline}</h1>
          <p className={styles.heroDetail}>{insight.detail}</p>
        </div>
        {periodSelector}
      </section>

      <div className={styles.summaryGrid}>
        <MetricCard tone="violet" label="Team Avg. Agent Performance" value={score(summary.teamAverageAgentPerformance)} helpText="out of 5" />
        <MetricCard tone="primary" label="Team Close Rate" value={summary.teamCloseRate === null ? '—' : `${summary.teamCloseRate.toFixed(1)}%`} helpText="of calls with a known outcome" />
        <MetricCard tone="secondary" label="Calls Needing Attention" value={String(summary.attentionCalls)} helpText="flagged by the router" />
        <MetricCard tone="success" label="Calls Analyzed" value={String(summary.callsAnalyzed)} helpText={`${summary.periodStart} – ${summary.periodEnd}`} />
      </div>

      <div className={styles.summaryGrid}>
        <p className={styles.supportingLabel}>Supporting metric — Team Avg. Lead Quality: {score(summary.teamAverageLeadQuality)} / 5</p>
      </div>

      <SectionCard
        title="Representative Performance"
        subtitle="Sorted lowest first — a fixed 0–5 scale, so small gaps never look larger than they are"
      >
        <RankedBarChart bars={bars} max={5} minConfidentSample={4} />
      </SectionCard>

      <div className={styles.columns}>
        <SectionCard title="Outcome Mix" subtitle="Across every analyzed call in range">
          <ul className={styles.patternList}>
            {summary.outcomeBreakdown.map((entry) => (
              <li key={entry.outcome}>
                {entry.outcome} — {entry.count} call{entry.count === 1 ? '' : 's'}
              </li>
            ))}
          </ul>
        </SectionCard>

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
      </div>
    </>
  )
}
