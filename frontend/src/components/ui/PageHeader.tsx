import type { ReactNode } from 'react'
import styles from './PageHeader.module.css'

export interface PageHeaderProps {
  eyebrow?: string
  title: string
  /** The page's one primary insight (§13.2) — kept visually distinct from routine description text. */
  insight?: string
  actions?: ReactNode
}

export default function PageHeader({ eyebrow, title, insight, actions }: PageHeaderProps) {
  return (
    <header className={styles.wrap}>
      <div className={styles.titleGroup}>
        {eyebrow && <span className={styles.eyebrow}>{eyebrow}</span>}
        <h1 className={styles.title}>{title}</h1>
        {insight && <p className={styles.insight}>{insight}</p>}
      </div>
      {actions && <div className={styles.actions}>{actions}</div>}
    </header>
  )
}
