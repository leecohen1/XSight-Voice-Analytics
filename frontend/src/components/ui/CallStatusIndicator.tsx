import type { CallStatus } from '../../types'
import { toDisplayStatus } from '../../types'
import StatusBadge, { type StatusTone } from './StatusBadge'

const TONE_BY_DISPLAY_STATUS: Record<ReturnType<typeof toDisplayStatus>, StatusTone> = {
  Processing: 'processing',
  Ready: 'success',
  'Needs Review': 'review',
  Flagged: 'warning',
  Failed: 'danger',
}

export interface CallStatusIndicatorProps {
  status: CallStatus
  className?: string
}

export default function CallStatusIndicator({ status, className }: CallStatusIndicatorProps) {
  const displayStatus = toDisplayStatus(status)
  return <StatusBadge label={displayStatus} tone={TONE_BY_DISPLAY_STATUS[displayStatus]} className={className} />
}
