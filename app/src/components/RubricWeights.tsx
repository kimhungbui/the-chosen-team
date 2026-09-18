import { RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Slider } from "@/components/ui/slider"

export const CRITERIA = [
  { id: "problem_understanding", name: "Problem Understanding" },
  { id: "scope_deliverables_clarity", name: "Scope & Deliverables" },
  { id: "pricing_clarity", name: "Pricing Clarity" },
  { id: "timeline_clarity", name: "Timeline Clarity" },
  { id: "completeness_vs_rfp", name: "Completeness vs RFP" },
  { id: "tone_persuasiveness", name: "Tone & Persuasiveness" },
  { id: "risk_transparency", name: "Risk & Assumptions" },
] as const

export type CriterionId = (typeof CRITERIA)[number]["id"]
export type Weights = Record<CriterionId, number>

export const DEFAULT_WEIGHTS: Weights = {
  problem_understanding: 15,
  scope_deliverables_clarity: 20,
  pricing_clarity: 15,
  timeline_clarity: 15,
  completeness_vs_rfp: 20,
  tone_persuasiveness: 5,
  risk_transparency: 10,
}

export const weightsTotal = (weights: Weights) =>
  CRITERIA.reduce((sum, criterion) => sum + weights[criterion.id], 0)

export const weightsValid = (weights: Weights) =>
  Math.abs(weightsTotal(weights) - 100) <= 0.1

export function RubricWeights({
  weights,
  onChange,
  disabled,
}: {
  weights: Weights
  onChange: (weights: Weights) => void
  disabled: boolean
}) {
  const total = weightsTotal(weights)
  const valid = weightsValid(weights)
  return (
    <Card className="document-card">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2>Rubric weights</h2>
          <p className="muted small mt-1">
            Optional. Weights shape the overall score only — each criterion’s
            quality score stays unchanged.
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          disabled={disabled}
          onClick={() => onChange({ ...DEFAULT_WEIGHTS })}
        >
          <RotateCcw size={14} />
          Reset
        </Button>
      </div>
      <div className="mt-5 space-y-3.5">
        {CRITERIA.map((criterion) => (
          <div key={criterion.id} className="flex items-center gap-4">
            <span className="w-44 shrink-0 text-[13px]">{criterion.name}</span>
            <Slider
              className="flex-1"
              value={[weights[criterion.id]]}
              min={0}
              max={100}
              step={1}
              disabled={disabled}
              aria-label={`${criterion.name} weight`}
              onValueChange={(values) => {
                const next = { ...weights }
                next[criterion.id] = values[0] ?? 0
                onChange(next)
              }}
            />
            <span className="w-11 shrink-0 text-right text-[13px] font-medium tabular-nums">
              {weights[criterion.id]}%
            </span>
          </div>
        ))}
      </div>
      <p role="status" className={`small mt-4 ${valid ? "muted" : "error-text"}`}>
        Total {total}% of 100 —{" "}
        {valid
          ? "these weights will be applied to the overall score."
          : "adjust the sliders so the total equals 100 before starting."}
      </p>
    </Card>
  )
}
