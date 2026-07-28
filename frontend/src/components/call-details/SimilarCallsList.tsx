import type { SimilarCall } from '../../types'
import CitationChip from '../ui/CitationChip'
import StatusBadge from '../ui/StatusBadge'
import EmptyState from '../ui/EmptyState'
import { LinkIcon } from '../icons'
import styles from './SimilarCallsList.module.css'

function outcomeTone(result: string): 'success' | 'danger' | 'neutral' {
  if (result === 'Sale') return 'success'
  if (result === 'No Sale') return 'danger'
  return 'neutral'
}

export interface SimilarCallsListProps {
  calls: SimilarCall[]
}

export default function SimilarCallsList({ calls }: SimilarCallsListProps) {
  if (calls.length === 0) {
    return (
      <EmptyState
        icon={<LinkIcon size={18} />}
        title="Not enough evidence"
        description="No similar historical calls cleared the retrieval similarity threshold for this transcript."
      />
    )
  }

  return (
    <div className={styles.list}>
      {calls.map((call) => (
        <div className={styles.card} key={call.call_id}>
          <div className={styles.header}>
            <CitationChip label={call.call_id} title="Historical call citation" />
            <span className={styles.agentName}>{call.agent_name}</span>
            <StatusBadge label={call.sale_result} tone={outcomeTone(call.sale_result)} />
            <span className={styles.similarity}>{Math.round(call.similarity_score * 100)}% similar</span>
          </div>
          <p className={styles.objection}>
            Objection: <strong>{call.main_objection}</strong>
          </p>
          <p className={styles.reason}>{call.reason}</p>
        </div>
      ))}
    </div>
  )
}
