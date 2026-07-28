import { useId, useState, type ReactNode } from 'react'
import { ChevronRightIcon } from '../icons'
import styles from './SectionCard.module.css'

export interface SectionCardProps {
  title?: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
  /** Progressive disclosure — used for transcript/cost/RAGAS detail sections that shouldn't compete with the official analysis. */
  collapsible?: boolean
  defaultOpen?: boolean
  className?: string
}

export default function SectionCard({ title, subtitle, action, children, collapsible = false, defaultOpen = false, className }: SectionCardProps) {
  const [open, setOpen] = useState(defaultOpen)
  const panelId = useId()

  if (collapsible && title) {
    return (
      <section className={[styles.card, className].filter(Boolean).join(' ')}>
        <button
          type="button"
          className={styles.headerCollapsible}
          aria-expanded={open}
          aria-controls={panelId}
          onClick={() => setOpen((v) => !v)}
        >
          <div className={styles.header} style={{ padding: 0 }}>
            <div className={styles.titleGroup}>
              <span className={styles.title}>{title}</span>
              {subtitle && <span className={styles.subtitle}>{subtitle}</span>}
            </div>
            <ChevronRightIcon size={18} className={[styles.chevron, open ? styles.chevronOpen : ''].join(' ')} />
          </div>
        </button>
        {open && (
          <div id={panelId} className={[styles.body, styles.bodyCollapsible, 'animateReveal'].join(' ')}>
            {children}
          </div>
        )}
      </section>
    )
  }

  return (
    <section className={[styles.card, className].filter(Boolean).join(' ')}>
      {(title || action) && (
        <div className={styles.header}>
          <div className={styles.titleGroup}>
            {title && <h2 className={styles.title}>{title}</h2>}
            {subtitle && <span className={styles.subtitle}>{subtitle}</span>}
          </div>
          {action}
        </div>
      )}
      <div className={[styles.body, title || action ? styles.bodyWithHeader : ''].join(' ')}>{children}</div>
    </section>
  )
}
