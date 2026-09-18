import type { Review } from './types'
import { reportSchema } from './types'

// UI-only fixtures. They are never used as the result of submitting user documents.
// No source excerpts are fabricated: example evidence is deliberately absent.
export const demoReviews: Review[] = [
  { id: 'demo-migration', title: 'Nordframe Migration', updatedAt: 'Example review', demo: true, result: reportSchema.parse({
    proposal_title: 'Nordframe Migration', rfp_title: 'Example RFP', overall_score_pct: 76, overall_traffic_light: 'YELLOW',
    executive_summary: 'Illustrative workspace only. Resolve commercial and delivery gaps before sending a proposal. Import an evaluator report to inspect real findings and citations.',
    requirement_gaps: [
      { requirement_id: 'DEMO-01', requirement_title: 'Migration plan needs detail', status: 'MISSING', priority_level: 'CRITICAL', issue_description: 'This is an example issue, not an assessment of a real document.', actionable_rewrite: 'For a real review, describe migration phases, ownership, rollback and acceptance criteria against the actual RFP.' },
      { requirement_id: 'DEMO-02', requirement_title: 'Pricing structure is incomplete', status: 'PARTIAL_GAP', priority_level: 'HIGH', issue_description: 'Example of a commercial clarification to resolve before submission.', actionable_rewrite: 'Verify the requested pricing model, then itemize the relevant costs and assumptions.' },
      { requirement_id: 'DEMO-03', requirement_title: 'Delivery commitment needs verification', status: 'CONTRADICTED', priority_level: 'HIGH', issue_description: 'Example of a delivery constraint that requires source verification.', actionable_rewrite: 'Align delivery milestones with the client’s actual deadline and state dependencies.' },
    ],
  }) },
  { id: 'demo-retail', title: 'Retail CRM', updatedAt: 'Example review', demo: true, result: reportSchema.parse({
    proposal_title: 'Retail CRM', rfp_title: 'Example RFP', overall_score_pct: 71, overall_traffic_light: 'YELLOW',
    executive_summary: 'Illustrative review. This example shows how unresolved assumptions appear in the workspace; no client documents were analyzed.',
    ambiguous_requirements: [{ requirement_id: 'DEMO-01', requirement_title: 'Support expectations need clarification', rfp_snippet: '', ambiguity_reason: 'Example of an unresolved service-level assumption.', proposal_handling: 'UNADDRESSED', clarification_question: 'Confirm required support hours and response targets with the client.', recommended_assumption: 'Record the agreed support scope before finalizing pricing.' }],
  }) },
]
