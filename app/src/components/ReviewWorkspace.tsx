import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Copy,
  Check,
  ShieldAlert,
  ThumbsUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  Table,
  TableHeader,
  TableHead,
  TableRow,
  TableBody,
  TableCell,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { getReview, reviewKeys } from "@/lib/api/reviews";
import {
  criticalCount,
  issuesFor,
  requirementsFor,
  type Issue,
} from "@/lib/api/types";

export function Status({ value }: { value: string }) {
  const tone = ["Covered", "GREEN"].includes(value)
    ? "status-green"
    : ["CRITICAL", "HIGH", "Missing", "Conflict", "RED"].includes(value)
      ? "status-red"
      : ["Partial", "Overpromised", "Unresolved risk", "MEDIUM", "YELLOW"].includes(value)
        ? "status-amber"
        : "status-neutral";
  return (
    <Badge variant="outline" className={tone}>
      {value.replaceAll("_", " ")}
    </Badge>
  );
}

export function ReviewWorkspace({ id }: { id: string }) {
  const query = useQuery({
    queryKey: reviewKeys.detail(id),
    queryFn: () => getReview(id),
  });
  const [tab, setTab] = useState("overview");
  const [filter, setFilter] = useState("All statuses");
  const [selected, setSelected] = useState<Issue | null>(null);
  const [copied, setCopied] = useState(false);

  if (query.isPending)
    return (
      <div className="space-y-4">
        <Skeleton className="h-20" />
        <Skeleton className="h-64" />
      </div>
    );
  if (query.isError)
    return (
      <div role="alert" className="error-banner">
        {query.error.message}
        <Button variant="outline" onClick={() => void query.refetch()}>
          Retry
        </Button>
      </div>
    );

  const { result, demo } = query.data;
  const issues = issuesFor(result);
  const requirements = requirementsFor(result);
  const critical = criticalCount(result);
  const visibleRequirements = requirements.filter(
    (item) => filter === "All statuses" || item.status === filter,
  );
  const priorityIssues = [...issues]
    .sort(
      (a, b) =>
        Number(b.severity === "CRITICAL") - Number(a.severity === "CRITICAL"),
    )
    .slice(0, 3);

  const copyFix = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const selectedCriterion = result.rubric_scores.find(
    (item) => item.criterion_id === selected?.id,
  );

  return (
    <>
      <div className="page-heading">
        <div className="flex items-center gap-3">
          <span className="eyebrow">REVIEW WORKSPACE</span>
          {demo && <Badge variant="outline">Example data</Badge>}
        </div>
        <h1>{query.data.title}</h1>
        <p className="muted small flex items-center gap-2">
          <FileText size={14} /> {result.rfp_title || "RFP title not supplied"} ·{" "}
          {demo
            ? "Illustrative review"
            : `Reviewed ${new Date(query.data.updatedAt).toLocaleString()}`}
        </p>
      </div>

      {demo && (
        <div className="notice mb-6">
          This is a UI example, not a real evaluation. No source citations or
          coverage percentages have been fabricated.
        </div>
      )}

      {result.engine_notice && (
        <div role="status" className="notice mb-6">
          {result.engine_notice}
        </div>
      )}

      {result.engine_mode === "rule_engine" && (
        <div className="notice mb-6">
          Rule-engine evaluation. Verify findings against your documents before
          making a submission decision.
        </div>
      )}

      <div className="flex flex-wrap gap-3 mb-5 items-center">
        <Status value={result.overall_traffic_light} />
        {[
          ["RFP", result.rfp_metrics],
          ["Proposal", result.proposal_metrics],
        ].map(
          ([label, metrics]) =>
            typeof metrics !== "string" &&
            metrics && (
              <span className="muted small" key={String(label)}>
                {String(label)}: {metrics.format || "Document"}
                {metrics.count !== undefined
                  ? ` · ${metrics.count} ${metrics.units_label || "units"}`
                  : ""}
                {metrics.word_count !== undefined
                  ? ` · ${metrics.word_count.toLocaleString()} words`
                  : ""}
              </span>
            ),
        )}
      </div>

      {result.llm_error && (
        <details className="notice mb-5">
          <summary className="font-semibold cursor-pointer">
            Evaluation engine notice
          </summary>
          <p className="whitespace-pre-wrap mt-2">{result.llm_error}</p>
        </details>
      )}

      {result.detected_client_priorities && (
        <Card className="p-5 mb-5 border-l-4 border-l-[#0066B3]">
          <h2 className="text-[#0066B3] font-semibold">
            Client Strategic Priorities (Extracted from RFP)
          </h2>
          <p className="mt-2 text-[13px] leading-relaxed text-[#172033]">
            {result.detected_client_priorities}
          </p>
        </Card>
      )}

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="workspace-tabs">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="issues">
            Issues <span className="tab-count">{issues.length}</span>
          </TabsTrigger>
          <TabsTrigger value="requirements">Requirements</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 pt-6">
          <div className="summary-grid">
            <Card className="metric">
              <span>Overall score</span>
              <strong>
                {(result.overall_score_pct / 20).toFixed(1)} <small>/ 5</small>
              </strong>
              <Progress value={result.overall_score_pct} className="h-1.5" />
              <p className="muted small">
                {result.overall_score_pct.toFixed(1)}% weighted compliance
              </p>
            </Card>
            <Card className="metric">
              <span>Critical issues</span>
              <strong className={critical ? "text-red-700" : ""}>
                {critical.toString().padStart(2, "0")}
              </strong>
              <p className="muted small">
                {critical
                  ? "Resolve before client submission"
                  : "No critical issues flagged in this report"}
              </p>
            </Card>
            <Card className="metric">
              <span>Gaps identified</span>
              <strong>{result.requirement_gaps.length.toString().padStart(2, "0")}</strong>
              <p className="muted small">Specific requirements needing attention</p>
            </Card>
          </div>

          <Card className="verdict">
            <div className="flex gap-3">
              <AlertTriangle className="shrink-0 text-blue-800" size={21} />
              <div>
                <h2>Executive Assessment</h2>
                <p className="mt-2 leading-relaxed muted">
                  {result.executive_summary || "No executive summary provided."}
                </p>
              </div>
            </div>
          </Card>

          {/* Top Strengths & Critical Risks */}
          {(result.top_strengths?.length > 0 ||
            result.top_risks_and_remediations?.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.top_strengths?.length > 0 && (
                <Card className="p-5 border-l-4 border-l-[#0DB14B]">
                  <div className="flex items-center gap-2 text-[#087a34] font-semibold text-[14px]">
                    <ThumbsUp size={16} /> Key Strengths
                  </div>
                  <ul className="mt-3 space-y-2 text-[13px] text-[#172033]">
                    {result.top_strengths.map((strength, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-[#0DB14B] font-bold">•</span>
                        <span>{strength}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {result.top_risks_and_remediations?.length > 0 && (
                <Card className="p-5 border-l-4 border-l-[#b42318]">
                  <div className="flex items-center gap-2 text-[#b42318] font-semibold text-[14px]">
                    <ShieldAlert size={16} /> Critical Risks & Remediations
                  </div>
                  <ul className="mt-3 space-y-2 text-[13px] text-[#172033]">
                    {result.top_risks_and_remediations.map((risk, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-[#b42318] font-bold">•</span>
                        <span>{risk}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>
          )}

          <Card className="overflow-hidden gap-0 py-0">
            <div className="section-heading">
              <div>
                <h2>Fix these first</h2>
                <p className="muted small mt-1">
                  The most important findings to take back to your proposal.
                </p>
              </div>
              <Button variant="ghost" onClick={() => setTab("issues")}>
                Review all issues <ArrowRight />
              </Button>
            </div>
            {priorityIssues.length ? (
              priorityIssues.map((issue) => (
                <IssueRow
                  key={issue.id}
                  issue={issue}
                  onClick={() => setSelected(issue)}
                />
              ))
            ) : (
              <div className="empty-state">
                <CheckCircle2 />
                <p>
                  No requirement issues were reported. Verify the report’s scope
                  before sending.
                </p>
              </div>
            )}
          </Card>

          <Card className="p-6">
            <h2>Evaluation Criteria (7 Rubrics)</h2>
            <p className="muted small mt-1">
              Click any criterion to inspect scoring rationale, strengths, weaknesses, and direct citations.
            </p>
            {result.rubric_scores.length ? (
              <div className="mt-4 divide-y divide-[#edf0f5]">
                {result.rubric_scores.map((criterion) => (
                  <button
                    key={criterion.criterion_id}
                    className="criterion-row"
                    onClick={() =>
                      setSelected({
                        id: criterion.criterion_id,
                        title: criterion.criterion_name,
                        severity: `${criterion.score_1_to_5.toFixed(1)}/5`,
                        category: "Scoring Rationale",
                        evidence: criterion.citations[0] ?? {
                          rfp_section: "",
                          rfp_quote: "",
                          proposal_section: "",
                          proposal_quote: "",
                        },
                        explanation: criterion.rationale,
                        fix: { text: criterion.suggested_fixes.join("\n\n") },
                      })
                    }
                  >
                    <span>{criterion.criterion_name}</span>
                    <div className="flex items-center gap-3">
                      <span className="muted small">{criterion.weight}% weight</span>
                      <strong>
                        {criterion.score_1_to_5.toFixed(1)}{" "}
                        <span className="muted font-normal">/ 5</span>
                      </strong>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <p className="muted py-5">
                No criterion scores included in this report.
              </p>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="issues" className="pt-6">
          <div className="section-heading px-0">
            <div>
              <h2>
                Issues to resolve{" "}
                <span className="muted">({issues.length})</span>
              </h2>
              <p className="muted small mt-1">
                Evidence first. Concrete changes next.
              </p>
            </div>
          </div>
          <Card className="gap-0 overflow-hidden py-0">
            {issues.length ? (
              issues.map((issue) => (
                <IssueRow
                  key={issue.id}
                  issue={issue}
                  onClick={() => setSelected(issue)}
                />
              ))
            ) : (
              <div className="empty-state">
                No unresolved issues included in this report.
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="requirements" className="pt-6">
          <div className="section-heading px-0">
            <div>
              <h2>Requirement Findings (Matrix)</h2>
              <p className="muted small mt-1">
                Only requirements present in the evaluator’s report are shown.
              </p>
            </div>
            <select
              aria-label="Filter requirements by status"
              className="text-input w-auto"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            >
              {[
                "All statuses",
                "Covered",
                "Partial",
                "Missing",
                "Conflict",
                "Overpromised",
                "Unresolved risk",
                "Unknown",
              ].map((status) => (
                <option key={status}>{status}</option>
              ))}
            </select>
          </div>
          <Card className="py-0 overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Requirement</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Proposal Evidence</TableHead>
                  <TableHead>Severity</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visibleRequirements.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <button
                        className="text-left font-medium text-blue-800 hover:underline"
                        onClick={() => setSelected(item)}
                      >
                        {item.title}
                      </button>
                    </TableCell>
                    <TableCell>
                      <Status value={item.status} />
                    </TableCell>
                    <TableCell className="max-w-64 whitespace-normal">
                      <span className="line-clamp-2 text-[12px] text-slate-600">
                        {item.evidence.proposal_quote || "Not supplied"}
                      </span>
                    </TableCell>
                    <TableCell>
                      {item.status === "Covered" ? (
                        "—"
                      ) : (
                        <Status value={item.severity} />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {!visibleRequirements.length && (
              <div className="empty-state">
                No requirements match this filter.
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>

      {/* Right Detail Sheet */}
      <Sheet
        open={!!selected}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
      >
        <SheetContent className="w-full sm:max-w-xl overflow-y-auto p-0">
          <SheetHeader className="border-b p-7 pr-12">
            <SheetTitle>{selected?.title}</SheetTitle>
            <SheetDescription>
              {selected?.category} · Verify evidence before applying a fix.
            </SheetDescription>
            {selected && (
              <div>
                <Status value={selected.severity} />
              </div>
            )}
          </SheetHeader>
          {selected && (
            <div className="p-7 space-y-7">
              {/* If inspecting a Criterion Score */}
              {selectedCriterion && (
                <>
                  {selectedCriterion.score_factors_high.length > 0 && (
                    <section>
                      <h3 className="text-[#087a34] flex items-center gap-1.5">
                        <ThumbsUp size={14} /> Key Strengths
                      </h3>
                      <ul className="mt-2 space-y-1.5 text-[13px] text-slate-700">
                        {selectedCriterion.score_factors_high.map((factor, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-[#0DB14B] font-bold">•</span>
                            <span>{factor}</span>
                          </li>
                        ))}
                      </ul>
                    </section>
                  )}

                  {selectedCriterion.score_factors_low.length > 0 && (
                    <section>
                      <h3 className="text-[#b42318] flex items-center gap-1.5">
                        <ShieldAlert size={14} /> Weaknesses / Gaps
                      </h3>
                      <ul className="mt-2 space-y-1.5 text-[13px] text-slate-700">
                        {selectedCriterion.score_factors_low.map((factor, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-[#b42318] font-bold">•</span>
                            <span>{factor}</span>
                          </li>
                        ))}
                      </ul>
                    </section>
                  )}
                </>
              )}

              {/* Citations & Evidence */}
              <EvidenceBlock
                label="RFP Requirement"
                location={selected.evidence.rfp_section}
                text={selected.evidence.rfp_quote}
              />
              <EvidenceBlock
                label="Proposal Evidence"
                location={selected.evidence.proposal_section}
                text={selected.evidence.proposal_quote}
              />

              <section>
                <h3>Analysis & Impact</h3>
                <p className="mt-3 muted whitespace-pre-wrap">
                  {selected.explanation || "No explanation supplied."}
                </p>
              </section>

              {/* Actionable Fix & Copy Button */}
              {selected.fix.text && (
                <section className="fix-panel relative">
                  <div className="flex items-center justify-between">
                    <h3 className="text-[#162670]">Actionable Rewrite / Fix</h3>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="gap-1.5 text-[12px]"
                      onClick={() => copyFix(selected.fix.text)}
                    >
                      {copied ? (
                        <>
                          <Check size={14} className="text-[#0DB14B]" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy size={14} />
                          Copy Text
                        </>
                      )}
                    </Button>
                  </div>
                  {selected.fix.placement && (
                    <p className="small mt-2 font-medium text-[#0066B3]">
                      📍 {selected.fix.placement}
                    </p>
                  )}
                  <p className="mt-3 whitespace-pre-wrap bg-white p-3 rounded border border-[#d9e6fb] font-mono text-[12px] text-slate-800">
                    {selected.fix.text}
                  </p>
                </section>
              )}

              {/* Additional citations if criterion score */}
              {selectedCriterion &&
                selectedCriterion.citations.slice(1).map((citation, i) => (
                  <section key={i} className="space-y-4 pt-4 border-t border-slate-200">
                    <EvidenceBlock
                      label={`Additional Citation ${i + 2} — RFP`}
                      location={citation.rfp_section}
                      text={citation.rfp_quote}
                    />
                    <EvidenceBlock
                      label="Proposal Quote"
                      location={citation.proposal_section}
                      text={citation.proposal_quote}
                    />
                  </section>
                ))}
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}

function IssueRow({ issue, onClick }: { issue: Issue; onClick: () => void }) {
  return (
    <button className="issue-row" onClick={onClick}>
      <span className="issue-symbol">
        <AlertTriangle size={17} />
      </span>
      <span className="flex-1 min-w-0">
        <strong>{issue.title}</strong>
        <span className="block small muted mt-1">
          {issue.category} · View evidence and suggested fix
        </span>
      </span>
      <Status value={issue.severity} />
      <ArrowRight size={16} className="muted shrink-0" />
    </button>
  );
}

function EvidenceBlock({
  label,
  location,
  text,
}: {
  label: string;
  location: string;
  text: string;
}) {
  return (
    <section>
      <h3>{label}</h3>
      {location && <p className="small muted mt-2">Section: {location}</p>}
      <blockquote className="evidence">
        {text ||
          "No direct quote found in the document for this requirement."}
      </blockquote>
    </section>
  );
}
