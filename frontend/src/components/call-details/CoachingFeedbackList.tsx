import EmptyState from '../ui/EmptyState'
import styles from './CoachingFeedbackList.module.css'

export interface CoachingFeedbackListProps {
  feedback: string[]
}

export default function CoachingFeedbackList({ feedback }: CoachingFeedbackListProps) {
  if (feedback.length === 0) {
    return <EmptyState title="No coaching feedback" description="XSight did not generate coaching feedback for this call." />
  }
  return (
    <ul className={styles.list}>
      {feedback.map((point, i) => (
        <li key={i}>{point}</li>
      ))}
    </ul>
  )
}
