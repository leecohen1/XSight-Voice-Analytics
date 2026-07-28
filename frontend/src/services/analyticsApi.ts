/**
 * Overview analytics.
 *
 * Real backend only — there is deliberately no mock branch here. Every KPI,
 * trend bucket, improved-agent row and attention ordering is computed by
 * `call_data_service` (services/call_data_service/app/aggregation.py) and
 * rendered as-is. If the service is unreachable this throws, so the Overview
 * shows a real error instead of silently degrading into demo numbers.
 */
import type { OverviewPeriod, OverviewSummary } from '../types'
import { callDataServiceUrl } from './config'
import { getJson } from './httpClient'

export async function getOverview(
  period: OverviewPeriod = '7d',
  signal?: AbortSignal
): Promise<OverviewSummary> {
  return getJson<OverviewSummary>(`${callDataServiceUrl()}/overview?period=${period}`, signal)
}
