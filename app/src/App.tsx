import { useEffect, useState } from "react";
import {
  QueryClient,
  QueryClientProvider,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  ArrowRight,
  FileCheck2,
  Plus,
  Search,
  Files,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
} from "@/components/ui/command";
import { TooltipProvider } from "@/components/ui/tooltip";
import { listReviews, importReport, reviewKeys } from "@/lib/api/reviews";
import { NewReview } from "@/components/NewReview";
import { ReviewWorkspace } from "@/components/ReviewWorkspace";
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: Infinity, retry: false, refetchOnWindowFocus: false },
    mutations: { retry: false },
  },
});
function Workspace() {
  const [page, setPage] = useState("history");
  const [searchOpen, setSearchOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [info, setInfo] = useState<"help" | "settings" | null>(null);
  const query = useQuery({ queryKey: reviewKeys.all, queryFn: () => listReviews() });
  const client = useQueryClient();
  const navigate = (id: string) => {
    setPage(id);
    setMobileOpen(false);
    setSearchOpen(false);
  };
  const importer = useMutation({
    mutationFn: importReport,
    onSuccess: (review) => {
      client.setQueryData(reviewKeys.detail(review.id), review);
      void client.invalidateQueries({ queryKey: reviewKeys.all });
      navigate(review.id);
    },
  });
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen((open) => !open);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);
  const sidebar = (
    <>
      <button className="brand text-center" onClick={() => navigate("history")}>

        <span className="">
          Proposal Scorer
        </span>
      </button>
      <button className="search-button" onClick={() => setSearchOpen(true)}>
        <Search size={16} />
        <span>Search reviews…</span>
        <kbd>⌘K</kbd>
      </button>
      <Button className="w-full my-5 justify-start gap-[11px] px-3 text-[13px]" onClick={() => navigate("new")}>
        <Plus className="size-[18px]" />
        New review
      </Button>
      <nav aria-label="Main navigation">
        <button
          className={`nav-item ${page === "history" ? "active" : ""}`}
          onClick={() => navigate("history")}
        >
          <Files size={18} />
          Review history
        </button>
        <p className="sidebar-label">RECENT REVIEWS</p>
        {query.data?.slice(0, 2).map((review) => (
          <button
            className={`recent-item ${page === review.id ? "active" : ""}`}
            key={review.id}
            onClick={() => navigate(review.id)}
          >
            <span>{review.title}</span>

          </button>
        ))}
      </nav>

    </>
  );
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar">{sidebar}</aside>
      <div className="main-shell">

        <main id="main-content" className="main-content">
          {page === "history" ? (
            <>
              <div className="page-heading flex justify-between gap-4 items-end">
                <div>
                  <h1>Ready for a second look?</h1>
                  <p className="muted">
                    Find the gaps. Verify the evidence. Send a stronger
                    proposal.
                  </p>
                </div>
                <Button onClick={() => navigate("new")}>
                  <Plus />
                  New review
                </Button>
              </div>
              <Card className="intro-card">
                <div className="intro-symbol">
                  <FileCheck2 size={31} />
                </div>
                <div className="flex-1">
                  <h2>Before you hit send.</h2>
                  <p className="muted mt-2 max-w-xl">
                    Review your draft against the client’s RFP. Get specific
                    findings and clear next steps — not another AI-written
                    proposal.
                  </p>
                </div>
                <Button variant="outline" onClick={() => navigate("new")}>
                  Start a review
                  <ArrowRight />
                </Button>
              </Card>
              <div className="section-heading px-0 mt-8">
                <div>
                  <h2>Recent reviews</h2>
                </div>
              </div>
              {importer.error && (
                <div className="error-banner mb-4" role="alert">
                  {importer.error.message}
                </div>
              )}
              {query.isPending ? (
                <div className="space-y-3">
                  <Skeleton className="h-24" />
                  <Skeleton className="h-24" />
                </div>
              ) : query.isError ? (
                <div className="error-banner" role="alert">
                  {query.error.message}
                  <Button onClick={() => void query.refetch()}>Retry</Button>
                </div>
              ) : (
                <Card className="py-0 gap-0 overflow-hidden">
                  {query.data.map((review) => (
                    <button
                      key={review.id}
                      className="history-row"
                      onClick={() => navigate(review.id)}
                    >
                      <span className="history-icon">
                        <FileCheck2 size={21} />
                      </span>
                      <span className="flex-1 text-left min-w-0">
                        <span className="flex flex-wrap items-center gap-3 font-semibold ">
                          {review.title}
                          {review.demo && (
                            <Badge variant="outline" className="font-normal">
                              Example
                            </Badge>
                          )}
                        </span>
                        <span className="muted small block mt-1">
                          {review.demo
                            ? "Illustrative review · no source documents"
                            : new Date(review.updatedAt).toLocaleString()}
                        </span>
                      </span>
                      <span className="history-stat">
                        <strong>
                          {(review.score / 20).toFixed(1)}
                          <span className="muted font-normal"> / 5</span>
                        </strong>
                        <small>Overall score</small>
                      </span>
                      <span className="history-stat">
                        <strong>{review.critical} critical</strong>
                        <small>Needs verification</small>
                      </span>
                      <ArrowRight size={17} className="muted" />
                    </button>
                  ))}
                </Card>
              )}
            </>
          ) : page === "new" ? (
            <NewReview onOpen={navigate} />
          ) : (
            <ReviewWorkspace key={page} id={page} />
          )}
        </main>
      </div>
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="mobile-sidebar p-5">
          <SheetHeader className="sr-only">
            <SheetTitle>Navigation</SheetTitle>
            <SheetDescription>Navigate your review workspace</SheetDescription>
          </SheetHeader>
          {sidebar}
        </SheetContent>
      </Sheet>
      <CommandDialog open={searchOpen} onOpenChange={setSearchOpen}>
        <CommandInput placeholder="Search reviews or actions…" />
        <CommandList>
          <CommandEmpty>No matching reviews.</CommandEmpty>
          <CommandGroup heading="Actions">
            <CommandItem onSelect={() => navigate("new")}>
              <Plus />
              Start a new review
            </CommandItem>
            <CommandItem onSelect={() => navigate("history")}>
              <Files />
              Review history
            </CommandItem>
          </CommandGroup>
          <CommandGroup heading="Reviews">
            {query.data?.map((review) => (
              <CommandItem
                key={review.id}
                value={`${review.title} ${review.id}`}
                onSelect={() => navigate(review.id)}
              >
                <FileCheck2 />
                {review.title}
                {review.demo && <span className="muted ml-auto">Example</span>}
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </CommandDialog>
      <Dialog
        open={!!info}
        onOpenChange={(open) => {
          if (!open) setInfo(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {info === "settings"
                ? "API connection"
                : "Review with confidence"}
            </DialogTitle>
            <DialogDescription>
              {info === "settings"
                ? "POST /evaluate uploads your RFP and proposal to the evaluation service."
                : "Proposal Scorer evaluates an existing draft; it does not write a proposal from scratch."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 small leading-relaxed">
            {info === "settings" ? (
              <>
                <p>
                  Local development proxies /evaluate to http://localhost:8000. For production, configure a same-origin reverse proxy or VITE_API_BASE_URL with backend CORS enabled.
                </p>
                <p>
                  The request sends rfp_file and proposal_file as multipart/form-data. Pasted text is sent as UTF-8 text files. Review names remain local to this workspace.
                </p>
                <p>
                  PDF, Markdown and text are supported. PDFs must contain readable text; scanned PDFs need OCR first. Progress is indeterminate, with no automatic frontend timeout.
                </p>
              </>
            ) : (
              <>
                <p>
                  1. Add the client RFP and draft proposal.
                  <br />
                  2. Run a review through a configured service, or import an
                  exported evaluator JSON report.
                  <br />
                  3. Open Issues to verify evidence and act on specific fixes.
                </p>
                <p>
                  Coverage is not calculated from a gap-only report. Missing
                  citations are explicitly shown, never invented. Example
                  reviews are not real evaluations.
                </p>
                <p>
                  Keep exported reports: this workspace has no persistent
                  history.
                </p>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Workspace />
      </TooltipProvider>
    </QueryClientProvider>
  );
}
