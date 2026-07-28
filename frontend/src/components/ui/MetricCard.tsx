import type { ReactNode, CSSProperties } from 'react'
import styles from './MetricCard.module.css'

export type MetricCardTone = 'primary' | 'secondary' | 'violet' | 'success'

export interface MetricCardProps {
  label: string
  value: string
  helpText?: string
  icon?: ReactNode
  tone?: MetricCardTone
}

/**
 * Token-compatibility mapping only (Signal Room palette) — this card
 * shape is still the pre-redesign KPI grid and is scheduled to become a
 * ledger-style metric row when Overview/Team Intelligence/AI Operations
 * get their own redesign pass. Not touched visually beyond that until then.
 */
const TONE_VARS: Record<MetricCardTone, CSSProperties> = {
  primary: { ['--accent-a' as string]: 'var(--color-accent)', ['--accent-b' as string]: 'var(--color-evidence)', ['--accent-bg' as string]: 'var(--color-accent-bg)' },
  secondary: { ['--accent-a' as string]: 'var(--color-evidence)', ['--accent-b' as string]: 'var(--color-accent)', ['--accent-bg' as string]: 'var(--color-evidence-bg)' },
  violet: { ['--accent-a' as string]: 'var(--color-status-review)', ['--accent-b' as string]: 'var(--color-evidence)', ['--accent-bg' as string]: 'var(--color-status-review-bg)' },
  success: { ['--accent-a' as string]: 'var(--color-status-success)', ['--accent-b' as string]: 'var(--color-evidence)', ['--accent-bg' as string]: 'var(--color-status-success-bg)' },
}

export default function MetricCard({ label, value, helpText, icon, tone = 'primary' }: MetricCardProps) {
  return (
    <div className={styles.card} style={TONE_VARS[tone]}>
      <div className={styles.topRow}>
        <span className={styles.label}>{label}</span>
        {icon && <span className={styles.iconWrap}>{icon}</span>}
      </div>
      <span className={styles.value}>{value}</span>
      {helpText && <span className={styles.helpText}>{helpText}</span>}
    </div>
  )
}
