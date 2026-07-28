import type { CallProcessingCost } from '../../types'
import StatusBadge from '../ui/StatusBadge'
import LoadingSkeleton from '../ui/LoadingSkeleton'
import EmptyState from '../ui/EmptyState'
import styles from './UsageCostPanel.module.css'

export interface UsageCostPanelProps {
  cost: CallProcessingCost | null
  loading?: boolean
}

const formatUsd = (value: number) => `$${value.toFixed(2)}`

export default function UsageCostPanel({ cost, loading }: UsageCostPanelProps) {
  if (loading) return <LoadingSkeleton lines={4} />
  if (!cost) return <EmptyState title="No cost data yet" description="Usage and cost figures are recorded once processing begins." />

  return (
    <div>
      <div className={styles.summary}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Total cost</span>
          <span className={styles.statValue}>{formatUsd(cost.totalCostUsd)}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Processing time</span>
          <span className={styles.statValue}>{Math.round(cost.processingDurationSeconds)}s</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Failed steps</span>
          <span className={styles.statValue}>{cost.failedSteps.length}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Retried steps</span>
          <span className={styles.statValue}>{cost.retriedSteps.length}</span>
        </div>
      </div>

      <table className={styles.table}>
        <thead>
          <tr>
            <th>Component</th>
            <th className={styles.numeric}>Tokens</th>
            <th className={styles.numeric}>Cost</th>
          </tr>
        </thead>
        <tbody>
          {cost.componentBreakdown.map((c) => (
            <tr key={c.component}>
              <td>{c.label}</td>
              <td className={styles.numeric}>{c.totalTokens?.toLocaleString() ?? '—'}</td>
              <td className={styles.numeric}>{formatUsd(c.costUsd)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {(cost.failedSteps.length > 0 || cost.retriedSteps.length > 0) && (
        <div className={styles.stepList}>
          {cost.failedSteps.map((s, i) => (
            <StatusBadge key={`f-${i}`} label={`Failed: ${s}`} tone="danger" />
          ))}
          {cost.retriedSteps.map((s, i) => (
            <StatusBadge key={`r-${i}`} label={`Retried: ${s}`} tone="warning" />
          ))}
        </div>
      )}

      <p className={styles.disclaimer}>
        Cost figures are estimates derived from measured usage and configured provider pricing — not an actual provider invoice.
      </p>
    </div>
  )
}
