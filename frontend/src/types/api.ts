/** Generic API envelope types shared across every service module. */

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  pageSize: number
  totalCount: number
}

export interface ApiError {
  code: string
  message: string
  /** Which pipeline stage rejected the request, when the backend reports one (e.g. "pre_transcription"). */
  stage?: string
  details?: unknown
}
