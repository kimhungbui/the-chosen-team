import { z } from 'zod'

const text = z.string().default('')
const metricsSchema = z.object({ format: z.string().optional(), units_label: z.string().optional(), count: z.number().optional(), word_count: z.number().optional() }).default({})
export const citationSchema = z.object({ rfp_section: text, rfp_quote: text, proposal_section: text, proposal_quote: text })
const criterionSchema = z.object({
  criterion_id: z.string(), criterion_name: z.string(), score_1_to_5: z.number().min(1).max(5),
  weight: z.number().default(0), weighted_score: z.number().default(0), traffic_light: z.enum(['GREEN', 'YELLOW', 'RED']).optional(), score_factors_high: z.array(z.string()).default([]), score_factors_low: z.array(z.string()).default([]), rationale: text, citations: z.array(citationSchema).default([]),
  suggested_fixes: z.array(z.string()).default([]),
})
const gapSchema = z.object({
  requirement_id: z.string(), requirement_title: z.string(), status: z.string(),
  rfp_snippet: text, proposal_snippet: text, issue_description: text,
  placement_anchor: text, priority_level: z.string().default('HIGH'), actionable_rewrite: text,
})
const ambiguitySchema = z.object({
  requirement_id: z.string(), requirement_title: z.string().default('Ambiguous requirement'),
  rfp_snippet: text, ambiguity_reason: text, proposal_handling: text,
  clarification_question: text, recommended_assumption: text,
})
export const reportSchema = z.object({
  detected_client_priorities: text, rfp_metrics: metricsSchema, proposal_metrics: metricsSchema, llm_error: z.string().nullable().default(null),
  proposal_title: z.string().min(1), rfp_title: text, overall_score_pct: z.number().min(0).max(100),
  overall_traffic_light: z.enum(['GREEN', 'YELLOW', 'RED']), executive_summary: text,
  rubric_scores: z.array(criterionSchema).default([]), requirement_gaps: z.array(gapSchema).default([]),
  ambiguous_requirements: z.array(ambiguitySchema).default([]), top_strengths: z.array(z.string()).default([]),
  top_risks_and_remediations: z.array(z.string()).default([]), engine_mode: text, engine_notice: text,
})
export type ReviewResult = z.infer<typeof reportSchema>
export type CriterionScore = z.infer<typeof criterionSchema>
export type Evidence = z.infer<typeof citationSchema>
export type RequirementStatus = 'Covered' | 'Partial' | 'Missing' | 'Conflict' | 'Overpromised' | 'Unresolved risk' | 'Unknown'
export type SuggestedFix = { text: string; placement?: string }
export type Issue = { id: string; title: string; severity: string; category: string; evidence: Evidence; explanation: string; fix: SuggestedFix }
export type Requirement = Issue & { status: RequirementStatus }
export type Review = { id: string; title: string; updatedAt: string; demo: boolean; result: ReviewResult }
export type ReviewSummary = Pick<Review, 'id' | 'title' | 'updatedAt' | 'demo'> & { score: number; critical: number }

export function mapStatus(value: string): RequirementStatus {
  const statuses: Record<string, RequirementStatus> = {
    FULFILLED: 'Covered', FULLY_ADDRESSED: 'Covered', PARTIAL_GAP: 'Partial', PARTIAL: 'Partial',
    MISSING: 'Missing', CONTRADICTED: 'Conflict', OVERPROMISED: 'Overpromised',
    RISK_UNRESOLVED: 'Unresolved risk', UNRESOLVED_ASSUMPTION: 'Unresolved risk',
  }
  return statuses[value.toUpperCase()] ?? 'Unknown'
}
export function requirementsFor(report: ReviewResult): Requirement[] {
  return report.requirement_gaps.map((gap, index) => ({
    id: `${gap.requirement_id}-${index}`, title: gap.requirement_title, severity: gap.priority_level,
    category: 'RFP requirement', status: mapStatus(gap.status),
    evidence: { rfp_section: '', rfp_quote: gap.rfp_snippet, proposal_section: '', proposal_quote: gap.proposal_snippet },
    explanation: gap.issue_description, fix: { text: gap.actionable_rewrite, placement: gap.placement_anchor },
  }))
}
export function issuesFor(report: ReviewResult): Issue[] {
  return [
    ...requirementsFor(report).filter(item => item.status !== 'Covered'),
    ...report.ambiguous_requirements.filter(item => item.proposal_handling !== 'HANDLED_WITH_ASSUMPTIONS').map((item, index) => ({
      id: `ambiguity-${index}`, title: item.requirement_title, severity: 'REVIEW', category: 'Risk / assumptions',
      evidence: { rfp_section: '', rfp_quote: item.rfp_snippet, proposal_section: '', proposal_quote: '' },
      explanation: item.ambiguity_reason,
      fix: { text: [item.clarification_question, item.recommended_assumption].filter(Boolean).join('\n\n') },
    })),
  ]
}
export const criticalCount = (report: ReviewResult) => issuesFor(report).filter(issue => issue.severity === 'CRITICAL').length
// The backend exposes a gap list, not a complete requirement inventory. Coverage cannot be inferred from it.
