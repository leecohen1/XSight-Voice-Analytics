import { Link } from 'react-router-dom'
import type { SimilarCall } from '../../types'
import { outcomeTone } from '../../analytics/outcomeSemantics'
import CitationChip from '../ui/CitationChip'
import StatusBadge from '../ui/StatusBadge'
import EmptyState from '../ui/EmptyState'
import { LinkIcon } from '../icons'
import styles from './SimilarCallsList.module.css'

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
            {/* The citation is the evidence trail — it has to be followable.
                Every cited id comes from the retrieval corpus, which is seeded
                into call_data_service, so this resolves; if a citation ever
                outlives its record the target renders its "Call not found"
                state rather than a broken page. */}
            <Link to={`/calls/${call.call_id}`} className={styles.citationLink}>
              <CitationChip label={call.call_id} title={`Open ${call.call_id}`} />
            </Link>
            <span className={styles.agentName}>{call.agent_name}</span>
            <StatusBadge label={call.sale_result} tone={outcomeTone(call.sale_result)} />
            {/* A missing score is left out entirely — rendering Math.round(null*100)
                printed "NaN% similar", which reads as a real measurement. */}
            {Number.isFinite(call.similarity_score) && (
              <span className={styles.similarity}>{Math.round(call.similarity_score * 100)}% similar</span>
            )}
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
