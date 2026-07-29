import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import type { CallListItem } from '../types'
import { toDisplayStatus } from '../types'
import { listCalls } from '../services/callsApi'
import { sortCalls, groupByRepresentative, SORT_LABELS, type CallSortOrder } from '../analytics/callGrouping'
import PageHeader from '../components/ui/PageHeader'
import SectionCard from '../components/ui/SectionCard'
import LoadingSkeleton from '../components/ui/LoadingSkeleton'
import ErrorState from '../components/ui/ErrorState'
import EmptyState from '../components/ui/EmptyState'
import Tabs from '../components/ui/Tabs'
import CallListItemRow from '../components/calls/CallListItemRow'
import rowStyles from '../components/calls/CallListItemRow.module.css'
import CallFilters, { type CallStatusFilter } from '../components/calls/CallFilters'
import { buttonClassName } from '../components/ui/buttonClassName'
import { CallsIcon, ChevronDownIcon } from '../components/icons'
import styles from './Calls.module.css'

const STATUS_PARAM_MAP: Record<string, CallStatusFilter> = {
  needs_review: 'Needs Review',
  ready: 'Ready',
  flagged: 'Flagged',
}

const VIEW_TABS = [
  { id: 'all', label: 'All Calls' },
  { id: 'by_rep', label: 'By Representative' },
]

const SORT_ORDER: CallSortOrder[] = ['attention_first', 'newest', 'performance_high', 'performance_low', 'outcome']

function RepresentativeCard({ group }: { group: ReturnType<typeof groupByRepresentative>[number] }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={styles.repGroup}>
      <button
        type="button"
        className={styles.repHeader}
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <span className={styles.repName}>{group.agentName}</span>
        <span className={styles.repStats}>
          <span className={styles.repStat}>
            <strong>{group.callsAnalyzed}</strong> calls
          </span>
          <span className={styles.repStat}>
            <strong>{group.closeRate === null ? '—' : `${group.closeRate.toFixed(0)}%`}</strong> close rate
          </span>
          <span className={styles.repStat}>
            <strong>{group.averageAgentPerformance === null ? '—' : group.averageAgentPerformance.toFixed(1)}</strong>
            <span className={styles.repStatSuffix}>/5 perf.</span>
          </span>
          {group.attentionCount > 0 && (
            <span className={[styles.repStat, styles.repAttention].join(' ')}>
              <strong>{group.attentionCount}</strong> need attention
            </span>
          )}
        </span>
        <Link
          to={`/calls?agent=${encodeURIComponent(group.agentName)}`}
          className={styles.repOpenAll}
          onClick={(e) => e.stopPropagation()}
        >
          View all
        </Link>
        <ChevronDownIcon size={16} className={[styles.repChevron, expanded ? styles.repChevronOpen : ''].join(' ')} />
      </button>

      {expanded && (
        <div className={styles.repCalls}>
          {/* The representative's name is the group header above -- it must
              not repeat on every row inside an already-expanded group. */}
          {group.calls.map((call) => (
            <CallListItemRow call={call} key={call.callId} hideAgentName />
          ))}
        </div>
      )}
    </div>
  )
}

export default function Calls() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [calls, setCalls] = useState<CallListItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<CallStatusFilter>(
    STATUS_PARAM_MAP[searchParams.get('status') ?? ''] ?? 'All'
  )
  const [view, setView] = useState<'all' | 'by_rep'>('all')
  const [sortOrder, setSortOrder] = useState<CallSortOrder>('attention_first')
  const agentFilter = searchParams.get('agent')

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
      const matchesAgent = !agentFilter || call.agentName === agentFilter
      const matchesSearch =
        !query ||
        call.agentName.toLowerCase().includes(query) ||
        call.customerName?.toLowerCase().includes(query) ||
        call.callId.toLowerCase().includes(query)
      return matchesStatus && matchesAgent && matchesSearch
    })
  }, [calls, search, statusFilter, agentFilter])

  const sorted = useMemo(() => sortCalls(filtered, sortOrder), [filtered, sortOrder])
  const groups = useMemo(() => groupByRepresentative(filtered), [filtered])

  const clearAgentFilter = () => {
    const next = new URLSearchParams(searchParams)
    next.delete('agent')
    setSearchParams(next)
  }

  return (
    <>
      <PageHeader
        title="Calls"
        insight="Every analyzed call, prioritized for triage -- search, filter, and reopen any completed analysis."
        actions={
          <Link to="/analyze" className={buttonClassName('primary', 'md')}>
            Analyze New Call
          </Link>
        }
      />

      <div className={styles.toolbar}>
        <Tabs items={VIEW_TABS} activeId={view} onChange={(id) => setView(id as 'all' | 'by_rep')} label="View" />
        <CallFilters search={search} onSearchChange={setSearch} statusFilter={statusFilter} onStatusFilterChange={setStatusFilter} />
        {view === 'all' && (
          <label className={styles.sortControl}>
            <span className={styles.sortLabel}>Sort</span>
            <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value as CallSortOrder)}>
              {SORT_ORDER.map((order) => (
                <option key={order} value={order}>
                  {SORT_LABELS[order]}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      {agentFilter && (
        <div className={styles.activeFilterBanner}>
          Showing calls for <strong>{agentFilter}</strong>
          <button type="button" onClick={clearAgentFilter} className={styles.clearFilter}>
            Clear
          </button>
        </div>
      )}

      <SectionCard>
        {error && <ErrorState description={error} />}
        {!error && !calls && <LoadingSkeleton lines={6} />}
        {!error && calls && (
          <>
            <p className={styles.resultCount}>
              {filtered.length} of {calls.length} call{calls.length === 1 ? '' : 's'}
              {view === 'by_rep' && ` across ${groups.length} representative${groups.length === 1 ? '' : 's'}`}
            </p>

            {filtered.length === 0 ? (
              <EmptyState
                icon={<CallsIcon size={18} />}
                title="No calls match your filters"
                description="Try a different search term, status filter, or representative."
              />
            ) : view === 'all' ? (
              <div className={styles.list}>
                <div className={rowStyles.headerRow} aria-hidden="true">
                  <span>Representative / Customer</span>
                  <span>Outcome</span>
                  <span>Attention</span>
                  <span>Agent Perf.</span>
                  <span>Confidence</span>
                  <span>Date</span>
                  <span />
                </div>
                {sorted.map((call) => (
                  <CallListItemRow call={call} key={call.callId} />
                ))}
              </div>
            ) : (
              <div className={styles.repList}>
                {groups.map((group) => (
                  <RepresentativeCard group={group} key={group.agentName} />
                ))}
              </div>
            )}
          </>
        )}
      </SectionCard>
    </>
  )
}
