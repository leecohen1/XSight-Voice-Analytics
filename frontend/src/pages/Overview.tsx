import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getOverview } from '../services/analyticsApi'
import type { AttentionCall, KpiMetric, OverviewPeriod, OverviewSummary, RecentCall } from '../types'
import { ATTENTION_CATEGORY_LABELS } from '../types'
import { buildExecutiveSummary } from '../analytics/executiveSummary'
import PageHeader from '../components/ui/PageHeader'
import KpiCard from '../components/ui/KpiCard'
import SectionCard from '../components/ui/SectionCard'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import EmptyState from '../components/ui/EmptyState'
import Button from '../components/ui/Button'
import DonutChart from '../components/charts/DonutChart'
import PeriodTrendChart from '../components/charts/PeriodTrendChart'
import { buttonClassName } from '../components/ui/buttonClassName'
import { CallsIcon, AiOperationsIcon, AlertIcon } from '../components/icons'
import styles from './Overview.module.css'

const PERIOD_OPTIONS: { value: OverviewPeriod; label: string }[] = [
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
]

/**
 * Four primary KPIs, not six equally-weighted cards -- the business
 * outcome, the volume behind it, what needs action, and what is still
 * open. "Follow-up Needed" stands in for a "recovery opportunities" count:
 * `attention_calls` is capped at a handful of rows server-side, so counting
 * from it here would silently undercount in any period with more attention
 * items than fit that list. `outcome_distribution.follow_up` is a real,
 * complete, non-paginated count for the exact same window.
 */
const PRIMARY_KPIS = [
  { key: 'calls_analyzed', label: 'Calls Analyzed', icon: CallsIcon, format: 'count' as const },
  { key: 'close_rate', label: 'Close Rate', icon: AiOperationsIcon, format: 'percent' as const },
  { key: 'calls_requiring_attention', label: 'Needs Attention', icon: AlertIcon, format: 'count' as const },
] as const

const SUPPORTING_KPIS = [
  { key: 'average_agent_performance', label: 'Avg. Agent Performance', format: 'score' as const },
  { key: 'average_lead_quality', label: 'Avg. Lead Quality', format: 'score' as const },
  { key: 'improved_agents_count', label: 'Improved Representatives', format: 'count' as const },
] as const

function AttentionRow({ call }: { call: AttentionCall }) {
  return (
    <Link to={`/calls/${call.call_id}`} className={styles.attentionRow}>
      <span className={`${styles.priorityDot} ${styles[`priority_${call.priority}`]}`} aria-hidden="true" />
      <span className={styles.attentionMain}>
        <span className={styles.attentionAgent}>
          {call.agent_name}
          {call.customer_name ? ` · ${call.customer_name}` : ''}
        </span>
        <span className={styles.attentionReason}>{call.reason ?? ATTENTION_CATEGORY_LABELS[call.category]}</span>
      </span>
      <span className={styles.attentionMeta}>
        <span className={styles.attentionCategory}>{ATTENTION_CATEGORY_LABELS[call.category]}</span>
        <span className={styles.attentionScore}>{call.priority}</span>
      </span>
    </Link>
  )
}

function RecentRow({ call }: { call: RecentCall }) {
  return (
    <Link to={`/calls/${call.call_id}`} className={styles.recentRow}>
      <span className={styles.attentionMain}>
        <span className={styles.attentionAgent}>
          {call.agent_name}
          {call.customer_name ? ` · ${call.customer_name}` : ''}
        </span>
        <span className={styles.attentionReason}>{call.call_date ?? call.created_at.slice(0, 10)}</span>
      </span>
      <span className={styles.attentionMeta}>
        <span className={styles.attentionCategory}>{call.call_outcome ?? 'Outcome not recorded'}</span>
        {call.source === 'live_analysis' && <span className={styles.liveBadge}>Live</span>}
      </span>
    </Link>
  )
}

/** Outcome slices in a fixed, meaningful order -- decided outcomes first,
    open/unknown last, so the legend reads like a funnel.
    Returns null when the backend response predates `outcome_distribution`
    (an older deployment) -- the section renders an honest "not available"
    state instead of crashing on an undefined field. */
function outcomeSlices(data: OverviewSummary) {
  const d = data.outcome_distribution
  if (!d) return null
  return [
    { key: 'sale', label: 'Sale', value: d.sale, color: 'var(--color-status-success)' },
    { key: 'no_sale', label: 'No Sale', value: d.no_sale, color: 'var(--color-status-danger)' },
    { key: 'follow_up', label: 'Follow-up Needed', value: d.follow_up, color: 'var(--color-status-warning)' },
    { key: 'uncertain', label: 'Uncertain', value: d.uncertain, color: 'var(--color-status-review)' },
    ...(d.unknown > 0 ? [{ key: 'unknown', label: 'Not recorded', value: d.unknown, color: 'var(--color-text-muted)' }] : []),
  ]
}

export default function Overview() {
  const [period, setPeriod] = useState<OverviewPeriod>('7d')
  const [data, setData] = useState<OverviewSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [reloadToken, setReloadToken] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    let cancelled = false
    setLoading(true)
    setError(null)

    getOverview(period, controller.signal)
      .then((result) => {
        if (!cancelled) {
          setData(result)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (cancelled || (err instanceof DOMException && err.name === 'AbortError')) return
        setError(err instanceof Error ? err.message : String(err))
        setLoading(false)
      })

    return () => {
      cancelled = true
      controller.abort()
    }
  }, [period, reloadToken])

  const retry = useCallback(() => setReloadToken((n) => n + 1), [])

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
        <PageHeader title="Overview" actions={periodSelector} />
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

  if (loading || !data) {
    return (
      <>
        <PageHeader title="Overview" actions={periodSelector} />
        <LoadingSkeleton lines={8} />
      </>
    )
  }

  const hasCalls = (data.kpis.calls_analyzed.current_value ?? 0) > 0
  const headline = buildExecutiveSummary(data)

  // A KpiMetric shape for follow_up so it renders through the same KpiCard
  // as every other primary metric. There is no previous-period comparison
  // for outcome_distribution yet, so previous/absolute/percentage are
  // honestly null rather than invented -- KpiCard already renders that as
  // "Not enough comparison data". current_value falls back to null (rendered
  // as "--") rather than crashing when an older backend deployment predates
  // this field.
  const followUpMetric: KpiMetric = {
    current_value: data.outcome_distribution?.follow_up ?? null,
    previous_value: null,
    absolute_change: null,
    percentage_change: null,
    trend_direction: 'unknown',
  }
  const slices = outcomeSlices(data)

  return (
    <>
      <section className={styles.hero}>
        <div className={styles.heroText}>
          <span className={styles.heroEyebrow}>
            <span className={styles.heroEyebrowDot} aria-hidden="true" />
            Sales Intelligence · Overview
          </span>
          <h1 className={styles.heroTitle}>{headline}</h1>
        </div>
        <div className={styles.heroActions}>
          {periodSelector}
          <Link to="/analyze" className={buttonClassName('primary', 'md')}>
            Analyze a Call
          </Link>
        </div>
      </section>

      {!hasCalls ? (
        <SectionCard>
          <EmptyState
            icon={<CallsIcon size={18} />}
            title="No calls in this period"
            description={
              data.data_quality.loaded_records > 0
                ? 'Calls exist in storage but none fall inside the selected period. Try Last 30 days.'
                : 'Analyze your first sales call, or seed the historical corpus, to populate this dashboard.'
            }
            action={
              <Link to="/analyze" className={buttonClassName('primary', 'md')}>
                Analyze a call
              </Link>
            }
          />
        </SectionCard>
      ) : (
        <>
          <div className={styles.kpiGrid}>
            {PRIMARY_KPIS.map((card) => (
              <KpiCard
                key={card.key}
                metricKey={card.key}
                metric={data.kpis[card.key]}
                label={card.label}
                format={card.format}
                icon={<card.icon size={16} />}
              />
            ))}
            <KpiCard
              metricKey="follow_up"
              metric={followUpMetric}
              label="Follow-up Needed"
              format="count"
              icon={<AlertIcon size={16} />}
              context="Open conversations, no decision yet"
            />
          </div>

          <div>
            <p className={styles.supportingLabel}>Supporting metrics</p>
            <div className={styles.supportingGrid}>
              {SUPPORTING_KPIS.map((card) => (
                <KpiCard
                  key={card.key}
                  metricKey={card.key}
                  metric={data.kpis[card.key]}
                  label={card.label}
                  format={card.format}
                  variant="supporting"
                />
              ))}
            </div>
          </div>

          <div className={styles.sectionRow}>
            <SectionCard title="Outcome Distribution" subtitle="Every analyzed call in this period, by outcome">
              {slices ? (
                <DonutChart
                  slices={slices}
                  centerValue={String(data.kpis.calls_analyzed.current_value ?? 0)}
                  centerLabel="calls"
                />
              ) : (
                <EmptyState
                  icon={<CallsIcon size={18} />}
                  title="Not available"
                  description="This backend deployment does not report an outcome breakdown yet."
                />
              )}
            </SectionCard>

            <SectionCard
              title="Close Rate Trend"
              subtitle={`${period === '7d' ? 'Daily' : 'Weekly'} buckets, fixed 0–100% scale`}
            >
              <PeriodTrendChart
                buckets={data.close_rate_trend.map((bucket) => ({
                  label: bucket.start_date.slice(5),
                  value: bucket.close_rate,
                  sampleSize: bucket.known_outcomes,
                }))}
                max={100}
                unit="%"
                ariaLabel="Close rate by period, fixed 0 to 100 percent scale"
              />
            </SectionCard>
          </div>

          <div className={styles.columns}>
            <SectionCard
              title="Calls Requiring Attention"
              subtitle="Ranked by priority score, then recency"
              className={data.attention_calls.length > 0 ? styles.attentionCard : undefined}
            >
              {data.attention_calls.length > 0 ? (
                <div className={styles.list}>
                  {data.attention_calls.map((call) => (
                    <AttentionRow call={call} key={call.call_id} />
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={<CallsIcon size={18} />}
                  title="Nothing needs attention"
                  description="No call in this period was flagged for review, coaching, or recovery."
                />
              )}
            </SectionCard>

            <SectionCard title="Recent Calls" subtitle="Newest first">
              {data.recent_calls.length > 0 ? (
                <div className={styles.list}>
                  {data.recent_calls.map((call) => (
                    <RecentRow call={call} key={call.call_id} />
                  ))}
                </div>
              ) : (
                <EmptyState title="No calls yet" description="Analyze your first sales call to get started." />
              )}
            </SectionCard>
          </div>

          <SectionCard title="Improved Representatives" subtitle="At least 2 calls in each period, and a +0.2 or better gain">
            {data.improved_agents.length > 0 ? (
              <div className={styles.improvedList}>
                {data.improved_agents.map((agent) => (
                  <div className={styles.improvedRow} key={agent.agent_name}>
                    <span className={styles.improvedName}>{agent.agent_name}</span>
                    <span className={styles.improvedScores}>
                      {agent.previous_average_score.toFixed(2)} → {agent.current_average_score.toFixed(2)}
                    </span>
                    <span className={styles.improvedDelta}>+{agent.improvement.toFixed(2)}</span>
                    <span className={styles.improvedCounts}>
                      {agent.previous_call_count} → {agent.current_call_count} calls
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No measurable improvement yet"
                description="An agent needs at least 2 scored calls in both periods, and a gain of 0.2 or more, to appear here."
              />
            )}
          </SectionCard>
        </>
      )}

      {data.data_quality.skipped_malformed_records > 0 && (
        <p className={styles.dataQualityNote}>
          {data.data_quality.skipped_malformed_records} stored record
          {data.data_quality.skipped_malformed_records === 1 ? ' was' : 's were'} unreadable and excluded from these
          figures.
        </p>
      )}
    </>
  )
}
