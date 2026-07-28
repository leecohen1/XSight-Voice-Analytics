import styles from './StatusBadge.module.css'

export type StatusTone = 'success' | 'warning' | 'danger' | 'review' | 'processing' | 'neutral'

export interface StatusBadgeProps {
  label: string
  tone: StatusTone
  className?: string
}

/**
 * Status language — a word plus a small instrument-style mark. Status is
 * always conveyed through the visible label text, not color alone; the
 * mark is reinforcement only. Strictly semantic — this tone set is never
 * reused as brand decoration.
 */
export default function StatusBadge({ label, tone, className }: StatusBadgeProps) {
  return (
    <span className={[styles.badge, styles[tone], className].filter(Boolean).join(' ')}>
      <span className={styles.mark} aria-hidden="true" />
      {label}
    </span>
  )
}
