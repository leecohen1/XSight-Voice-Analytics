/**
 * The rule under test: colour and direction come from what a metric means.
 * The same numeric movement must read as good news on one KPI and bad news
 * on another, and "no comparison available" must never masquerade as zero.
 */
import { describe, expect, it } from 'vitest'
import { formatComparison, formatMetricValue, metricSemantics } from './kpiSemantics'
import type { KpiMetric } from '../types'

function kpi(overrides: Partial<KpiMetric> = {}): KpiMetric {
  return {
    current_value: 10,
    previous_value: 8,
    absolute_change: 2,
    percentage_change: 25,
    trend_direction: 'up',
    ...overrides,
  }
}

describe('metricSemantics — polarity', () => {
  it('treats a rising close rate as positive', () => {
    const s = metricSemantics('close_rate', kpi({ current_value: 44, previous_value: 36, absolute_change: 8 }))
    expect(s.direction).toBe('up')
    expect(s.sentiment).toBe('positive')
    expect(s.tone).toBe('success')
  })

  it('treats a falling close rate as negative', () => {
    const s = metricSemantics('close_rate', kpi({ current_value: 36, previous_value: 44, absolute_change: -8 }))
    expect(s.direction).toBe('down')
    expect(s.sentiment).toBe('negative')
  })

  it('treats rising attention count as negative even though the number went up', () => {
    const s = metricSemantics('calls_requiring_attention', kpi({ current_value: 5, previous_value: 2, absolute_change: 3 }))
    expect(s.direction).toBe('up')
    expect(s.sentiment).toBe('negative')
  })

  it('treats falling attention count as positive even though the number went down', () => {
    const s = metricSemantics('calls_requiring_attention', kpi({ current_value: 1, previous_value: 4, absolute_change: -3 }))
    expect(s.direction).toBe('down')
    expect(s.sentiment).toBe('positive')
  })

  it('treats call volume movement as neither good nor bad', () => {
    const up = metricSemantics('calls_analyzed', kpi({ absolute_change: 5 }))
    const down = metricSemantics('calls_analyzed', kpi({ absolute_change: -5 }))
    expect(up.sentiment).toBe('neutral')
    expect(down.sentiment).toBe('neutral')
  })
})

describe('metricSemantics — standing overrides movement for attention', () => {
  it('stays critical while calls still need attention, even after improving', () => {
    const s = metricSemantics('calls_requiring_attention', kpi({ current_value: 2, previous_value: 6, absolute_change: -4 }))
    expect(s.sentiment).toBe('positive') // it did improve
    expect(s.tone).toBe('critical') // but 2 calls still need the manager today
  })

  it('goes success only when the attention queue is actually empty', () => {
    const s = metricSemantics('calls_requiring_attention', kpi({ current_value: 0, previous_value: 3, absolute_change: -3 }))
    expect(s.tone).toBe('success')
  })
})

describe('metricSemantics — missing data', () => {
  it('reports unknown rather than flat when there is no previous period', () => {
    const s = metricSemantics('close_rate', kpi({ previous_value: null, absolute_change: null, percentage_change: null }))
    expect(s.direction).toBe('unknown')
    expect(s.sentiment).toBe('unknown')
  })

  it('mutes a metric with no current value', () => {
    const s = metricSemantics('average_agent_performance', kpi({ current_value: null }))
    expect(s.tone).toBe('muted')
  })

  it('distinguishes a real zero-change from missing comparison data', () => {
    const flat = metricSemantics('close_rate', kpi({ absolute_change: 0, previous_value: 44 }))
    expect(flat.direction).toBe('flat')
    expect(flat.sentiment).toBe('neutral')
  })
})

describe('formatMetricValue', () => {
  it('renders a missing value as an em dash, never zero', () => {
    expect(formatMetricValue(null, 'count')).toBe('—')
    expect(formatMetricValue(null, 'percent')).toBe('—')
    expect(formatMetricValue(null, 'score')).toBe('—')
  })

  it('renders a real zero as zero', () => {
    expect(formatMetricValue(0, 'count')).toBe('0')
  })

  it('formats percent and score consistently', () => {
    expect(formatMetricValue(44.4, 'percent')).toBe('44.4%')
    expect(formatMetricValue(4.13, 'score')).toBe('4.1')
  })
})

describe('formatComparison', () => {
  it('says there is not enough comparison data instead of inventing a change', () => {
    expect(formatComparison(kpi({ previous_value: null }), 'count')).toBe('Not enough comparison data')
  })

  it('omits a percentage when the ratio is undefined', () => {
    const text = formatComparison(kpi({ previous_value: 0, absolute_change: 3, percentage_change: null }), 'count')
    expect(text).toContain('+3')
    expect(text).not.toContain('%)')
  })

  it('states unchanged explicitly', () => {
    expect(formatComparison(kpi({ absolute_change: 0 }), 'count')).toBe('Unchanged vs. previous period')
  })
})
