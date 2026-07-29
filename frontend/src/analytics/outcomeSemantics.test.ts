/**
 * Cross-screen audit finding: Call Details, Similar Calls and the Calls
 * table each defined their own outcomeTone, and two of the three had
 * silently drifted -- "Follow-up Needed" rendered as an amber warning on
 * the Calls table but as neutral grey everywhere else. This locks in the
 * single, now-shared implementation every screen imports.
 */
import { describe, expect, it } from 'vitest'
import { outcomeTone } from './outcomeSemantics'

describe('outcomeTone', () => {
  it('is consistent for every outcome value regardless of caller', () => {
    expect(outcomeTone('Sale')).toBe('success')
    expect(outcomeTone('No Sale')).toBe('danger')
    expect(outcomeTone('Follow-up Needed')).toBe('warning')
    expect(outcomeTone('Uncertain')).toBe('neutral')
  })

  it('treats a missing outcome as neutral rather than throwing', () => {
    expect(outcomeTone(undefined)).toBe('neutral')
    expect(outcomeTone(null)).toBe('neutral')
    expect(outcomeTone('')).toBe('neutral')
  })
})
