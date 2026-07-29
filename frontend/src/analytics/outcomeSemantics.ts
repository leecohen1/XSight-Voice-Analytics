/**
 * The single source of truth for how a call_outcome value maps to a
 * StatusTone. Found via cross-screen audit: Call Details, Similar Calls and
 * the Calls table each had their own copy of this function, and two of the
 * three had silently drifted (Follow-up Needed rendered as an amber warning
 * on the Calls table, but as neutral grey everywhere else) -- the exact
 * "Sale / No Sale / Follow-up colors must remain consistent" rule this
 * module exists to enforce. Every screen must import this rather than
 * redefine it.
 */
import type { StatusTone } from '../components/ui/StatusBadge'

export function outcomeTone(outcome?: string | null): StatusTone {
  if (outcome === 'Sale') return 'success'
  if (outcome === 'No Sale') return 'danger'
  // Follow-up Needed is a distinct, actionable, open state -- it must not
  // be visually indistinguishable from a genuinely uncertain/unknown one.
  if (outcome === 'Follow-up Needed') return 'warning'
  return 'neutral'
}
