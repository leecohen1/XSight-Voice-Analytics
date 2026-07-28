import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getOverview } from '../services/analyticsApi'
import type { AttentionCall, KpiMetric, OverviewPeriod, OverviewSummary, RecentCall } from '../types'
import { ATTENTION_CATEGORY_LABELS } from '../types'
import PageHeader from '../components/ui/PageHeader'
import MetricCard, { type MetricCardTone } from '../components/ui/MetricCard'
import SectionCard from '../components/ui/SectionCard'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import EmptyState from '../components/ui/EmptyState'
import Button from '../components/ui/Button'
import TrendSparkline from '../components/charts/TrendSparkline'
import { buttonClassName } from '../components/ui/buttonClassName'
import { CallsIcon, AiOperationsIcon, AlertIcon, TeamIcon } from '../components/icons'
import styles from './Overview.module.css'

const PERIOD_OPTIONS: { value: OverviewPeriod; label: string }[] = [
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
]

/**
 * KPI presentation config. The values themselves are computed by
 * call_data_service — this only decides icon, tone and formatting.
 */
const KPI_CARDS = [
  { key: 'calls_analyzed', label: 'Calls Analyzed', icon: CallsIcon, tone: 'primary', format: 'count' },
  { key: 'close_rate', label: 'Close Rate', icon: AiOperationsIcon, tone: 'secondary', format: 'percent' },
  { key: 'calls_requiring_attention', label: 'Needs Attention', icon: AlertIcon, tone: 'violet', format: 'count' },
  { key: 'average_agent_performance', label: 'Avg. Agent Performance', icon: TeamIcon, tone: 'success', format: 'score' },
  { key: 'average_lead_quality', label: 'Avg. Lead Quality', icon: AiOperationsIcon, tone: 'secondary', format: 'score' },
  { key: 'improved_agents_count', label: 'Improved Agents', icon: TeamIcon, tone: 'success', format: 'count' },
] as const

/**
 * `null` is a real, meaningful value from the backend — it means "not
 * measured in this window", which is not the same as zero. It is rendered as
 * an em dash rather than being coerced to 0.
 */
function formatValue(metric: KpiMetric, format: string): string {
  const value = metric.current_value
  if (value === null || value === undefined) return '—'
  if (format === 'percent') return `${value}%`
  if (format === 'score') return value.toFixed(1)
  return String(Math.round(value))
}

function formatComparison(metric: KpiMetric, format: string): string {
  if (metric.previous_value === null || metric.previous_value === undefined) {
    return 'no comparable previous period'
  }
  if (metric.absolute_change === null) return 'no change data'

  const change = metric.absolute_change
  const sign = change > 0 ? '+' : ''
  const magnitude = format === 'score' ? change.toFixed(2) : format === 'percent' ? `${change}%` : String(Math.round(change))
  // A percentage change of null means the previous value was zero, so the
  // ratio is undefined — say so instead of printing a fabricated number.
  const pct = metric.percentage_change === null ? '' : ` (${metric.percentage_change > 0 ? '+' : ''}${metric.percentage_change}%)`
  if (change === 0) return 'unchanged vs. previous period'
  return `${sign}${magnitude}${pct} vs. previous period`
}

function AttentionRow({ call, onOpen }: { call: AttentionCall; onOpen: (id: string) => void }) {
  return (
    <button type="button" className={styles.attentionRow} onClick={() => onOpen(call.call_id)}>
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
    </button>
  )
}

function RecentRow({ call, onOpen }: { call: RecentCall; onOpen: (id: string) => void }) {
  return (
    <button type="button" className={styles.recentRow} onClick={() => onOpen(call.call_id)}>
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
    </button>
  )
}

export default function Overview() {
  const navigate = useNavigate()
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

  const openCall = useCallback((callId: string) => navigate(`/calls/${callId}`), [navigate])
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

  return (
    <>
      <section className={styles.hero}>
        <div className={styles.heroText}>
          <span className={styles.heroEyebrow}>
            <span className={styles.heroEyebrowDot} aria-hidden="true" />
            Sales Intelligence · Overview
          </span>
          <h1 className={styles.heroTitle}>{data.executive_summary}</h1>
          <p className={styles.heroInsight}>
            Every call, reconciled across transcript, retrieval, and signal evidence into one grounded read — so you
            know exactly which deals need your attention today.
          </p>
        </div>
        {periodSelector}
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
            {KPI_CARDS.map((card) => {
              const metric = data.kpis[card.key]
              const Icon = card.icon
              return (
                <MetricCard
                  key={card.key}
                  icon={<Icon size={16} />}
                  tone={card.tone as MetricCardTone}
                  label={card.label}
                  value={formatValue(metric, card.format)}
                  helpText={formatComparison(metric, card.format)}
                />
              )
            })}
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
                    <AttentionRow call={call} key={call.call_id} onOpen={openCall} />
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
                    <RecentRow call={call} key={call.call_id} onOpen={openCall} />
                  ))}
                </div>
              ) : (
                <EmptyState title="No calls yet" description="Analyze your first sales call to get started." />
              )}
            </SectionCard>
          </div>

          <SectionCard title="Close Rate Trend" subtitle={`Four buckets across the last ${period === '7d' ? '7' : '30'} days`}>
            <TrendSparkline
              data={data.close_rate_trend.map((bucket) => ({
                date: bucket.start_date,
                value: bucket.close_rate ?? 0,
              }))}
              formatValue={(v) => `${v}% close rate`}
            />
            <div className={styles.trendLegend}>
              {data.close_rate_trend.map((bucket) => (
                <div className={styles.trendBucket} key={bucket.label}>
                  <span className={styles.trendBucketLabel}>{bucket.start_date}</span>
                  <span className={styles.trendBucketValue}>
                    {bucket.close_rate === null ? '—' : `${bucket.close_rate}%`}
                  </span>
                  <span className={styles.trendBucketMeta}>
                    {bucket.sales}/{bucket.known_outcomes} sold
                  </span>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Improved Agents" subtitle="At least 2 calls in each period, and a +0.2 or better gain">
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
