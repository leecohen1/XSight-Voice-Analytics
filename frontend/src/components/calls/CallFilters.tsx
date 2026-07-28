import type { CallDisplayStatus } from '../../types'
import { SearchIcon } from '../icons'
import styles from './CallFilters.module.css'

export type CallStatusFilter = 'All' | CallDisplayStatus

const FILTERS: CallStatusFilter[] = ['All', 'Processing', 'Ready', 'Needs Review', 'Flagged', 'Failed']

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
