import type { CallDisplayStatus } from '../../types'
import { SearchIcon } from '../icons'
import styles from './CallFilters.module.css'

export type CallStatusFilter = 'All' | CallDisplayStatus

/**
 * Only the statuses a stored call can actually have.
 *
 * `call_data_service` persists one of `completed | flagged |
 * human_review_required`, and `toCallStatus` narrows anything else onto that
 * set, so `toDisplayStatus` can only ever return 'Ready', 'Needs Review' or
 * 'Flagged'. 'Processing' and 'Failed' were offered here too and matched
 * nothing by construction — a filter that always returns an empty list reads
 * as "you have no failed calls" when the truth is "this app cannot tell you
 * that". They belong to the in-flight pipeline states in `CallStatus`, which
 * are never written to storage.
 */
const FILTERS: CallStatusFilter[] = ['All', 'Ready', 'Needs Review', 'Flagged']

export interface CallFiltersProps {
  search: string
  onSearchChange: (value: string) => void
  statusFilter: CallStatusFilter
  onStatusFilterChange: (value: CallStatusFilter) => void
}

export default function CallFilters({ search, onSearchChange, statusFilter, onStatusFilterChange }: CallFiltersProps) {
  return (
    <div className={styles.wrap}>
      <div className={styles.search}>
        <span className={styles.searchIcon}>
          <SearchIcon size={16} />
        </span>
        <input
          type="search"
          className={styles.searchInput}
          placeholder="Search by agent, customer, or call ID"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          aria-label="Search calls"
        />
      </div>
      <span className={styles.divider} aria-hidden="true" />
      <div className={styles.chips} role="group" aria-label="Filter by status">
        {FILTERS.map((filter) => (
          <button
            key={filter}
            type="button"
            className={[styles.chip, filter === statusFilter ? styles.chipActive : ''].join(' ')}
            aria-pressed={filter === statusFilter}
            onClick={() => onStatusFilterChange(filter)}
          >
            {filter}
          </button>
        ))}
      </div>
    </div>
  )
}
