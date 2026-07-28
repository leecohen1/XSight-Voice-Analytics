import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import type { CallListItem } from '../types'
import { toDisplayStatus } from '../types'
import { listCalls } from '../services/callsApi'
import PageHeader from '../components/ui/PageHeader'
import SectionCard from '../components/ui/SectionCard'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import EmptyState from '../components/ui/EmptyState'
import CallListItemRow from '../components/calls/CallListItemRow'
import rowStyles from '../components/calls/CallListItemRow.module.css'
import CallFilters, { type CallStatusFilter } from '../components/calls/CallFilters'
import { buttonClassName } from '../components/ui/buttonClassName'
import { CallsIcon } from '../components/icons'
import styles from './Calls.module.css'

const STATUS_PARAM_MAP: Record<string, CallStatusFilter> = {
  needs_review: 'Needs Review',
  processing: 'Processing',
  ready: 'Ready',
  flagged: 'Flagged',
  failed: 'Failed',
}

export default function Calls() {
  const [searchParams] = useSearchParams()
  const [calls, setCalls] = useState<CallListItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<CallStatusFilter>(
    STATUS_PARAM_MAP[searchParams.get('status') ?? ''] ?? 'All'
  )

  useEffect(() => {
    let cancelled = false
    listCalls()
      .then((result) => {
        if (!cancelled) setCalls(result)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err))
      })
    return () => {
      cancelled = true
    }
  }, [])

  const filtered = useMemo(() => {
    if (!calls) return []
    const query = search.trim().toLowerCase()
    return calls.filter((call) => {
      const matchesStatus = statusFilter === 'All' || toDisplayStatus(call.status) === statusFilter
      const matchesSearch =
        !query ||
        call.agentName.toLowerCase().includes(query) ||
        call.customerName?.toLowerCase().includes(query) ||
        call.callId.toLowerCase().includes(query)
      return matchesStatus && matchesSearch
    })
  }, [calls, search, statusFilter])

  return (
    <>
      <PageHeader
        title="Calls"
        insight="Every call ever submitted, with its current processing state — search, filter, and reopen any completed analysis."
        actions={
          <Link to="/analyze" className={buttonClassName('primary', 'md')}>
            Analyze New Call
          </Link>
        }
      />

      <div className={styles.toolbar}>
        <CallFilters search={search} onSearchChange={setSearch} statusFilter={statusFilter} onStatusFilterChange={setStatusFilter} />
      </div>

      <SectionCard>
        {error && <ErrorState description={error} />}
        {!error && !calls && <LoadingSkeleton lines={6} />}
        {!error && calls && (
          <>
            <p className={styles.resultCount}>
              {filtered.length} of {calls.length} call{calls.length === 1 ? '' : 's'}
            </p>
            {filtered.length > 0 ? (
              <div className={styles.list}>
                <div className={rowStyles.headerRow} aria-hidden="true">
                  <span>Agent / Customer</span>
                  <span>Date</span>
                  <span>Status</span>
                  <span>Outcome</span>
                  <span>Call ID</span>
                  <span />
                </div>
                {filtered.map((call) => (
                  <CallListItemRow call={call} key={call.callId} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={<CallsIcon size={18} />}
                title="No calls match your filters"
                description="Try a different search term or status filter."
              />
            )}
          </>
        )}
      </SectionCard>
    </>
  )
}
