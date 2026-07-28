import styles from './LoadingSkeleton.module.css'

export interface LoadingSkeletonProps {
  /** Number of bars to render when used as a simple text-line skeleton. */
  lines?: number
  height?: number
  className?: string
}

export default function LoadingSkeleton({ lines = 3, height = 14, className }: LoadingSkeletonProps) {
  return (
    <div className={[styles.stack, className].filter(Boolean).join(' ')} role="status" aria-label="Loading">
      {Array.from({ length: lines }).map((_, i) => (
        <span
          key={i}
          className={styles.bar}
          style={{ height, width: i === lines - 1 ? '65%' : '100%' }}
        />
      ))}
    </div>
  )
}
