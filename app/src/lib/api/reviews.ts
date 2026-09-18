import { apiConfig, ApiError, requestJson } from './client'
import { demoReviews } from './demo'
import { criticalCount, reportSchema, type Review, type ReviewSummary } from './types'

// In-memory cache for fast local access and demo fallback
const localReviews = new Map<string, Review>(demoReviews.map((review) => [review.id, review]))

export const reviewKeys = {
  all: ['reviews'] as const,
  detail: (id: string) => ['reviews', id] as const,
  stats: ['stats'] as const,
}

export async function listReviews(search?: string): Promise<ReviewSummary[]> {
  try {
    const url = search ? `${apiConfig.historyPath}?search=${encodeURIComponent(search)}` : apiConfig.historyPath
    const payload = (await requestJson(url)) as {
      success?: boolean
      items?: Array<{
        id: string
        timestamp: string
        rfp_title: string
        proposal_title: string
        overall_score_pct: number
        overall_traffic_light: 'GREEN' | 'YELLOW' | 'RED'
        engine_mode?: string
        rfp_filename?: string | null
        proposal_filename?: string | null
      }>
    }

    if (payload && Array.isArray(payload.items)) {
      const remoteItems: ReviewSummary[] = payload.items.map((item) => ({
        id: item.id,
        title: item.proposal_title || item.proposal_filename || 'Untitled Proposal',
        updatedAt: item.timestamp,
        demo: false,
        score: item.overall_score_pct,
        critical: 0,
      }))

      // Merge with any local in-memory reviews not already in backend DB
      const localItems = [...localReviews.values()]
        .filter((r) => !payload.items?.some((item) => item.id === r.id))
        .map((review) => ({
          id: review.id,
          title: review.title,
          updatedAt: review.updatedAt,
          demo: review.demo,
          score: review.result.overall_score_pct,
          critical: criticalCount(review.result),
        }))

      const combined = [...remoteItems, ...localItems]
      if (search?.trim()) {
        const q = search.toLowerCase()
        return combined.filter(
          (item) => item.title.toLowerCase().includes(q) || item.id.toLowerCase().includes(q)
        )
      }
      return combined
    }
  } catch {
    // Graceful fallback to local session reviews if backend history endpoint is not reachable
  }

  let items = [...localReviews.values()].map((review) => ({
    id: review.id,
    title: review.title,
    updatedAt: review.updatedAt,
    demo: review.demo,
    score: review.result.overall_score_pct,
    critical: criticalCount(review.result),
  }))

  if (search?.trim()) {
    const q = search.toLowerCase()
    items = items.filter(
      (item) => item.title.toLowerCase().includes(q) || item.id.toLowerCase().includes(q)
    )
  }

  return items.reverse()
}

export async function getReview(id: string): Promise<Review> {
  // 1. Check local cache first (e.g. demo reviews or recently evaluated in this session)
  const cached = localReviews.get(id)
  if (cached && !id.startsWith('eval_')) {
    return cached
  }

  // 2. Fetch from backend GET /history/:record_id
  try {
    const payload = (await requestJson(`${apiConfig.historyPath}/${id}`)) as {
      success?: boolean
      record?: {
        id: string
        timestamp: string
        rfp_title: string
        proposal_title: string
        overall_score_pct: number
        overall_traffic_light: 'GREEN' | 'YELLOW' | 'RED'
        report: unknown
      }
    }

    if (payload?.record?.report) {
      const parsed = reportSchema.safeParse(payload.record.report)
      if (parsed.success) {
        const review: Review = {
          id: payload.record.id,
          title: payload.record.proposal_title || parsed.data.proposal_title || 'Untitled Proposal',
          updatedAt: payload.record.timestamp,
          demo: false,
          result: parsed.data,
        }
        localReviews.set(review.id, review)
        return review
      }
    }
  } catch {
    // If backend fetch failed, fall back to cached copy if available
  }

  if (cached) return cached
  throw new ApiError('This review is not available. Please start a new review or import a report.')
}

export function saveReport(payload: unknown, customTitle?: string, explicitId?: string): Review {
  let rawReport = payload
  let historyId = explicitId

  // Support Envelope { success: true, report: { ... }, history_id: "..." } and direct EvaluationReport
  if (payload && typeof payload === 'object' && 'report' in payload && (payload as { report: unknown }).report) {
    const envelope = payload as { report: unknown; history_id?: string | null }
    rawReport = envelope.report
    if (envelope.history_id) historyId = envelope.history_id
  }

  const parsed = reportSchema.safeParse(rawReport)
  if (!parsed.success) {
    throw new ApiError(
      'The response does not match the ProposalEvaluationReport schema. Please check the backend evaluator version.'
    )
  }

  const id = historyId || `eval_${crypto.randomUUID().slice(0, 12)}`
  const title = customTitle?.trim() || parsed.data.proposal_title || 'Untitled Proposal'

  const review: Review = {
    id,
    title,
    updatedAt: new Date().toISOString(),
    demo: false,
    result: parsed.data,
  }

  localReviews.set(review.id, review)
  return review
}

export type ReviewInput = {
  rfp: File
  proposal: File
  title?: string
  weights?: Record<string, number>
}

export async function runReview(input: ReviewInput, signal: AbortSignal): Promise<Review> {
  const body = new FormData()
  body.append('rfp_file', input.rfp)
  body.append('proposal_file', input.proposal)
  if (input.weights) {
    body.append('weights', JSON.stringify(input.weights))
  }

  const payload = await requestJson(apiConfig.reviewPath, {
    method: 'POST',
    body,
    signal,
  })

  signal.throwIfAborted()
  return saveReport(payload, input.title)
}

export async function deleteReview(id: string): Promise<void> {
  localReviews.delete(id)
  try {
    await requestJson(`${apiConfig.historyPath}/${id}`, { method: 'DELETE' })
  } catch {
    // Ignored if backend history is not available
  }
}

export async function importReport(file: File): Promise<Review> {
  if (file.size > 10 * 1024 * 1024) {
    throw new ApiError('The report exceeds 10 MB. Please select a smaller JSON report.')
  }
  let payload: unknown
  try {
    payload = JSON.parse(await file.text())
  } catch {
    throw new ApiError('This file is not valid JSON. Please export a valid JSON report from the evaluator.')
  }
  return saveReport(payload)
}
