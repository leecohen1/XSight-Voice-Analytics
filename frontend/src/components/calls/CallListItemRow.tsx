import { Link } from 'react-router-dom'
import type { CallListItem } from '../../types'
import { outcomeTone } from '../../analytics/outcomeSemantics'
import CallStatusIndicator from '../ui/CallStatusIndicator'
import StatusBadge from '../ui/StatusBadge'
import { ChevronRightIcon } from '../icons'
import styles from './CallListItemRow.module.css'

export interface CallListItemRowProps {
  call: CallListItem
  /** True inside an already-expanded representative group, where the
      agent's name is the group header and repeating it on every row
      would be pure noise. */
  hideAgentName?: boolean
}

/**
 * One row in the Calls table.
 *
 * The raw call UUID is deliberately not a visible column here -- it is
 * technical metadata nobody making a business decision needs to scan past.
 * It still appears where it is actually useful: in the URL once a row is
 * opened (so links stay shareable/copyable), on Call Details itself, and as
 * this row's own title attribute for anyone who does need it.
 */
export default function CallListItemRow({ call, hideAgentName }: CallListItemRowProps) {
  return (
    <Link to={`/calls/${call.callId}`} className={styles.row} title={call.callId}>
      <div className={styles.primary}>
        {!hideAgentName && <span className={styles.agentName}>{call.agentName}</span>}
        <span className={hideAgentName ? styles.agentName : styles.customerName}>
          {call.customerName ?? 'No customer name provided'}
        </span>
      </div>

      {/* .meta is `display: contents` at desktop width (so these render as
          direct grid columns of .row) and a wrapping flex row at mobile
          width, where .row itself collapses to a two-column card. */}
      <div className={styles.meta}>
        <span className={styles.cell}>
          {call.callOutcome ? <StatusBadge label={call.callOutcome} tone={outcomeTone(call.callOutcome)} /> : '—'}
        </span>

        <span className={styles.cell}>
          {call.attentionRequired ? (
            <StatusBadge label={call.attentionPriority ?? 'Attention'} tone="warning" />
          ) : (
            <CallStatusIndicator status={call.status} />
          )}
        </span>

        <span className={[styles.cell, styles.numeric].join(' ')}>
          {call.agentPerformanceScore !== undefined ? (
            <>
              {call.agentPerformanceScore}
              <span className={styles.scaleSuffix}>/5</span>
            </>
          ) : (
            '—'
          )}
        </span>

        <span className={[styles.cell, styles.numeric].join(' ')}>
          {call.confidence !== undefined ? `${Math.round(call.confidence * 100)}%` : '—'}
        </span>

        <span className={[styles.cell, styles.cellDate].join(' ')}>{call.callDate}</span>
      </div>

      <ChevronRightIcon size={16} className={styles.chevron} />
    </Link>
  )
}
