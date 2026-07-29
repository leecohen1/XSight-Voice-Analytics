/**
 * Regression: an earlier version used a plain <a href> for linked rows,
 * which is not intercepted by React Router -- clicking it would trigger a
 * full page reload instead of client-side navigation. Every linked row
 * must render a real router Link.
 */
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import RankedBarChart, { type RankedBar } from './RankedBarChart'

function renderChart(bars: RankedBar[], props: Partial<Parameters<typeof RankedBarChart>[0]> = {}) {
  return render(
    <MemoryRouter>
      <RankedBarChart bars={bars} max={5} {...props} />
    </MemoryRouter>
  )
}

describe('RankedBarChart', () => {
  it('renders a linked row as a real anchor with the given href (a router Link)', () => {
    renderChart([{ key: 'a', label: 'Sarah Levi', value: 4.2, sampleSize: 5, href: '/calls?agent=Sarah%20Levi' }])
    const link = screen.getByText('Sarah Levi').closest('a')
    expect(link).toHaveAttribute('href', '/calls?agent=Sarah%20Levi')
  })

  it('renders an unlinked row as a plain div, not a link', () => {
    renderChart([{ key: 'a', label: 'Sarah Levi', value: 4.2, sampleSize: 5 }])
    expect(screen.getByText('Sarah Levi').closest('a')).toBeNull()
  })

  it('shows the value against the fixed max, not an auto-scaled one', () => {
    renderChart([{ key: 'a', label: 'Sarah Levi', value: 4.2, sampleSize: 5 }], { max: 5 })
    expect(screen.getByText('4.2')).toBeInTheDocument()
    expect(screen.getByText('/ 5')).toBeInTheDocument()
  })

  it('renders a null value as "not scored" rather than a zero-length bar', () => {
    renderChart([{ key: 'a', label: 'Sarah Levi', value: null, sampleSize: 0 }])
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('flags a row below minConfidentSample as low sample', () => {
    renderChart([{ key: 'a', label: 'Sarah Levi', value: 5, sampleSize: 1 }], { minConfidentSample: 4 })
    expect(screen.getByText('low sample')).toBeInTheDocument()
  })

  it('does not flag a row at or above minConfidentSample', () => {
    renderChart([{ key: 'a', label: 'Sarah Levi', value: 5, sampleSize: 4 }], { minConfidentSample: 4 })
    expect(screen.queryByText('low sample')).not.toBeInTheDocument()
  })

  it('renders optional meta text when provided', () => {
    renderChart([{ key: 'a', label: 'Sarah Levi', value: 4, sampleSize: 5, meta: '50% close rate' }])
    expect(screen.getByText('50% close rate')).toBeInTheDocument()
  })

  it('renders nothing for an empty list', () => {
    const { container } = renderChart([])
    expect(container.querySelector('ul')).toBeNull()
  })
})
