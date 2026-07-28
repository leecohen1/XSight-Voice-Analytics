import type { ReactNode } from 'react'
import { AlertIcon } from '../icons'
import styles from './EmptyState.module.css'

export interface ErrorStateProps {
  title?: string
  description: string
  action?: ReactNode
}

export default function ErrorState({ title = 'Something went wrong', description, action }: ErrorStateProps) {
  return (
    <div className={styles.wrap} role="alert">
      <span className={styles.icon} style={{ color: 'var(--color-status-danger)' }}>
        <AlertIcon size={20} />
      </span>
      <span className={styles.title}>{title}</span>
      <p className={styles.description}>{description}</p>
      {action}
    </div>
  )
}
