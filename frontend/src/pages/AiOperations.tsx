import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import type { AIUsageSummary, CallListItem, CallProcessingCost, RagasSystemSummary } from '../types'
import { getUsageSummary, getCallCost, getQualitySummary } from '../services/aiOperationsApi'
import { listCalls } from '../services/callsApi'
import SectionCard from '../components/ui/SectionCard'
import MetricCard from '../components/ui/MetricCard'
import Tabs from '../components/ui/Tabs'
import StatusBadge, { type StatusTone } from '../components/ui/StatusBadge'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import TrendSparkline from '../components/charts/TrendSparkline'
import { AiOperationsIcon, AlertIcon, CallsIcon, CheckCircleIcon, ClockIcon } from '../components/icons'
import type { EvaluationStatus } from '../types'
import styles from './AiOperations.module.css'

const TAB_ITEMS = [
  { id: 'usage-cost', label: 'Usage & Cost' },
  { id: 'quality-evaluation', label: 'Quality Evaluation' },
]

const EVAL_TONE: Record<EvaluationStatus, StatusTone> = {
  passed: 'success',
  needs_review: 'warning',
  failed: 'danger',
  not_evaluated: 'neutral',
}

const EVAL_LABEL: Record<EvaluationStatus, string> = {
  passed: 'Passed',
  needs_review: 'Needs Review',
  failed: 'Failed',
  not_evaluated: 'Not Evaluated',
}

const formatUsd = (v: number) => `$${v.toFixed(2)}`

function UsageCostTab() {
  const [usage, setUsage] = useState<AIUsageSummary | null>(null)
  const [callCosts, setCallCosts] = useState<(CallListItem & { cost: CallProcessingCost })[] | null>(null)

  useEffect(() => {
    getUsageSummary().then(setUsage)
    listCalls().then(async (calls) => {
      const withCosts = await Promise.all(
        calls.map(async (call) => {
          const cost = await getCallCost(call.callId)
          return cost ? { ...call, cost } : null
        })
      )
      setCallCosts(withCosts.filter((c): c is CallListItem & { cost: CallProcessingCost } => c !== null).sort((a, b) => b.cost.totalCostUsd - a.cost.totalCostUsd))
    })
  }, [])

  if (!usage) return <LoadingSkeleton lines={6} />

  return (
    <>
      <div className={styles.kpiGrid}>
        <MetricCard tone="primary" icon={<AiOperationsIcon size={16} />} label="Total Cost" value={formatUsd(usage.totalCostUsd)} helpText={`${usage.periodStart} – ${usage.periodEnd}`} />
        <MetricCard tone="secondary" icon={<AiOperationsIcon size={16} />} label="Avg. Cost / Call" value={formatUsd(usage.averageCostPerCallUsd)} />
        <MetricCard tone="success" icon={<CallsIcon size={16} />} label="Calls Processed" value={String(usage.totalCallsProcessed)} helpText={`${usage.failedExecutions} failed, ${usage.retriedExecutions} retried`} />
        <MetricCard tone="violet" icon={<ClockIcon size={16} />} label="Avg. Processing Time" value={`${Math.round(usage.averageProcessingDurationSeconds)}s`} />
      </div>

      <SectionCard title="Cost Trend" subtitle="Cumulative estimated cost, last 5 weeks">
        <TrendSparkline data={usage.costTrend} formatValue={formatUsd} />
      </SectionCard>

      <SectionCard title="Cost by Component">
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Component</th>
              <th className={styles.numeric}>Events</th>
              <th className={styles.numeric}>Tokens</th>
              <th className={styles.numeric}>Cost</th>
            </tr>
          </thead>
          <tbody>
            {usage.componentBreakdown.map((c) => (
              <tr key={c.component}>
                <td>{c.label}</td>
                <td className={styles.numeric}>{c.eventsCount}</td>
                <td className={styles.numeric}>{c.totalTokens?.toLocaleString() ?? '—'}</td>
                <td className={styles.numeric}>{formatUsd(c.costUsd)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </SectionCard>

      <SectionCard title="Cost by Call" subtitle="Highest cost first">
        {callCosts ? (
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Call</th>
                <th className={styles.numeric}>Duration</th>
                <th className={styles.numeric}>Cost</th>
              </tr>
            </thead>
            <tbody>
              {callCosts.map((c) => (
                <tr key={c.callId}>
                  <td>
                    <Link to={`/calls/${c.callId}`}>
                      {c.agentName} · {c.callId}
                    </Link>
                  </td>
                  <td className={styles.numeric}>{Math.round(c.cost.processingDurationSeconds)}s</td>
                  <td className={styles.numeric}>{formatUsd(c.cost.totalCostUsd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <LoadingSkeleton lines={4} />
        )}
      </SectionCard>

      <p className={styles.disclaimer}>{usage.labels.join(' ')}</p>
    </>
  )
}

function QualityEvaluationTab() {
  const [summary, setSummary] = useState<RagasSystemSummary | null>(null)

  useEffect(() => {
    getQualitySummary().then(setSummary)
  }, [])

  if (!summary) return <LoadingSkeleton lines={6} />

  return (
    <>
      <div className={styles.kpiGrid}>
        <MetricCard tone="success" icon={<CheckCircleIcon size={16} />} label="Overall Quality" value={summary.overallScore.toFixed(2)} />
        <MetricCard tone="secondary" icon={<CallsIcon size={16} />} label="Evaluated Calls" value={String(summary.evaluatedCalls)} />
        <MetricCard tone="violet" icon={<AlertIcon size={16} />} label="Evaluation Failures" value={String(summary.evaluationFailures)} />
        <MetricCard tone="primary" icon={<ClockIcon size={16} />} label="Period" value={`${summary.periodStart.slice(5)} – ${summary.periodEnd.slice(5)}`} />
      </div>

      <SectionCard title="Quality Trend">
        <TrendSparkline data={summary.scoreTrend} color="var(--color-evidence)" formatValue={(v) => v.toFixed(2)} />
      </SectionCard>

      <SectionCard title="Metric Averages">
        <div className={styles.metricAverages}>
          {summary.metricAverages.map((m) => (
            <div key={m.name}>
              <div style={{ fontWeight: 600, fontSize: 'var(--text-sm)', marginBottom: 4 }}>{m.label}</div>
              <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700 }}>{m.score.toFixed(2)}</div>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Evaluation Records">
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Call</th>
              <th>Status</th>
              <th className={styles.numeric}>Overall Score</th>
            </tr>
          </thead>
          <tbody>
            {summary.records.map((record) => (
              <tr key={record.callId}>
                <td>
                  <Link to={`/calls/${record.callId}`}>{record.callId}</Link>
                </td>
                <td>
                  <StatusBadge label={EVAL_LABEL[record.status]} tone={EVAL_TONE[record.status]} />
                </td>
                <td className={styles.numeric}>{record.status === 'not_evaluated' ? '—' : record.overallScore.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </SectionCard>

      <p className={styles.disclaimer}>
        Evaluation Framework: RAGAS. RAGAS evaluates generated output and retrieved context — it is not the official
        call analysis. A high score does not remove the need for guardrails; a low score may require human review or
        further investigation.
      </p>
    </>
  )
}

export default function AiOperations() {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get('tab') === 'quality-evaluation' ? 'quality-evaluation' : 'usage-cost'

  return (
    <>
      <section className={styles.hero}>
        <div className={styles.heroText}>
          <span className={styles.heroEyebrow}>AI Operations</span>
          <h1 className={styles.heroTitle}>AI quality held steady while average cost per call went down.</h1>
          <p className={styles.heroDetail}>
            Operational visibility into what the pipeline costs to run and how reliable its output is — not a
            developer console. Every figure below is an estimate, clearly labeled, and secondary to the official
            analysis it supports.
          </p>
        </div>
      </section>

      <div className={styles.tabsRow}>
        <Tabs
          items={TAB_ITEMS}
          activeId={activeTab}
          onChange={(id) => setSearchParams(id === 'usage-cost' ? {} : { tab: id })}
          label="AI Operations sections"
        />
      </div>

      <div role="tabpanel" id={`tabpanel-${activeTab}`} aria-labelledby={`tab-${activeTab}`}>
        {activeTab === 'usage-cost' ? <UsageCostTab /> : <QualityEvaluationTab />}
      </div>
    </>
  )
}
