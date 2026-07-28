import { Link } from 'react-router-dom'
import type { CallListItem } from '../../types'
import CallStatusIndicator from '../ui/CallStatusIndicator'
import { ChevronRightIcon } from '../icons'
import styles from './CallListItemRow.module.css'

export interface CallListItemRowProps {
  call: CallListItem
}

export default function CallListItemRow({ call }: CallListItemRowProps) {
  return (
    <Link to={`/calls/${call.callId}`} className={styles.row}>
      <div className={styles.primary}>
        <span className={styles.agentName}>{call.agentName}</span>
        <span className={styles.customerName}>{call.customerName ?? 'No customer name provided'}</span>
      </div>
      <div className={styles.meta}>
        <span className={[styles.cell, styles.cellDate].join(' ')}>{call.callDate}</span>
        <CallStatusIndicator status={call.status} />
        <span className={styles.cell}>{call.callOutcome ?? '—'}</span>
        <span className={[styles.cell, styles.callId].join(' ')}>{call.callId}</span>
      </div>
      <ChevronRightIcon size={16} className={styles.chevron} />
    </Link>
  )
}
