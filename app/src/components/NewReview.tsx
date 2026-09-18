import { useEffect, useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, FileText, X, LoaderCircle, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { runReview, reviewKeys, type ReviewInput } from '@/lib/api/reviews'
import { ApiError } from '@/lib/api/client'
import { DEFAULT_WEIGHTS, RubricWeights, weightsValid, type Weights } from '@/components/RubricWeights'
import heroImg from '@/assets/image123.png'

type DocumentValue = { mode: 'upload' | 'paste'; text: string; file: File | null }
const emptyDocument = (): DocumentValue => ({ mode: 'upload', text: '', file: null })
const ready = (value: DocumentValue) => value.mode === 'paste' ? !!value.text.trim() : !!value.file
const toFile = (value: DocumentValue, name: string): File => {
  if (value.mode === 'upload' && value.file) return value.file
  return new File([value.text], name, { type: 'text/plain;charset=utf-8' })
}
function DocumentInput({ label, value, onChange, disabled, serverError }: { label: string; value: DocumentValue; onChange: (value: DocumentValue) => void; disabled: boolean; serverError?: string }) {
  const [error, setError] = useState('')
  const input = useRef<HTMLInputElement>(null)
  function select(file?: File) {
    if (!file || disabled) return
    setError('')
    if (!/\.(pdf|md|txt)$/i.test(file.name) || file.size === 0) {
      onChange({ ...value, file: null })
      setError(file.size === 0 ? 'This file is empty. Choose another file or paste text.' : 'Use a PDF, Markdown or plain-text file.')
      return
    }
    onChange({ ...value, file })
  }
  return <Card className="document-card"><div className="flex items-center gap-3"><span className="document-icon"><FileText size={20}/></span><div><h2>{label}</h2><p className="muted small">{label === 'Client RFP' ? 'The source of truth for this review' : 'The response you want to evaluate'}</p></div></div>
    <Tabs value={value.mode} onValueChange={mode => { if (mode === 'upload' || mode === 'paste') { setError(''); onChange({ ...value, mode }) } }}><TabsList className="my-5"><TabsTrigger value="upload" disabled={disabled}>Upload file</TabsTrigger><TabsTrigger value="paste" disabled={disabled}>Paste text</TabsTrigger></TabsList>
    <TabsContent value="upload"><div className="dropzone" onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); select(event.dataTransfer.files[0]) }}><Upload size={27}/><strong>{value.file?.name || 'Drop your document here'}</strong><p className="muted small">PDF, Markdown or plain text</p><input ref={input} type="file" accept=".pdf,.md,.txt" className="sr-only" aria-label={`Upload ${label}`} disabled={disabled} onChange={event => { select(event.target.files?.[0]); event.target.value = '' }}/><div className="flex gap-2"><Button type="button" variant="outline" disabled={disabled} onClick={() => input.current?.click()}>{value.file ? 'Replace file' : 'Browse files'}</Button>{value.file && <Button type="button" variant="ghost" aria-label={`Remove ${label}`} disabled={disabled} onClick={() => { setError(''); onChange({ ...value, file: null }) }}><X/></Button>}</div></div></TabsContent>
    <TabsContent value="paste"><label className="sr-only" htmlFor={label}>{label} text</label><Textarea id={label} className="min-h-56 resize-y" value={value.text} placeholder={`Paste the complete ${label.toLowerCase()} here…`} disabled={disabled} onChange={event => onChange({ ...value, text: event.target.value })}/></TabsContent></Tabs>
    {(error || serverError) && <p role="alert" className="error-text small mt-3">{error || serverError}</p>}<p className="muted small mt-3">{value.mode === 'paste' ? `${value.text.trim() ? value.text.trim().split(/\s+/).length : 0} words` : 'PDFs must contain readable text. Scanned PDFs / OCR are not supported.'}</p>
  </Card>
}
export function NewReview({ onOpen }: { onOpen: (id: string) => void }) {
  const [rfp, setRfp] = useState(emptyDocument)
  const [proposal, setProposal] = useState(emptyDocument)
  const [title, setTitle] = useState('')
  const [weights, setWeights] = useState<Weights>({ ...DEFAULT_WEIGHTS })
  const controller = useRef<AbortController | null>(null)
  const locked = useRef(false)
  const queryClient = useQueryClient()
  useEffect(() => () => controller.current?.abort(), [])
  const mutation = useMutation({
    mutationFn: ({ input, signal }: { input: ReviewInput; signal: AbortSignal }) => runReview(input, signal),
    onSuccess: (review, variables) => { if (variables.signal.aborted) return; queryClient.setQueryData(reviewKeys.detail(review.id), review); void queryClient.invalidateQueries({ queryKey: reviewKeys.all }); onOpen(review.id) },
    onSettled: () => { locked.current = false }, retry: false,
  })
  const fields = mutation.error instanceof ApiError ? mutation.error.fields : {}
  return <><div className="page-heading flex justify-between items-start gap-6"><div><h1>New proposal review</h1><p className="muted">Check your response against what the client actually asked for.</p></div><img src={heroImg} alt="AI comparing RFP and Proposal documents" className="hidden md:block w-64 shrink-0 -mt-2" /></div><form onSubmit={event => {
    event.preventDefault()
    if (locked.current || !ready(rfp) || !ready(proposal) || !weightsValid(weights)) return
    locked.current = true
    controller.current = new AbortController()
    mutation.mutate({ input: { rfp: toFile(rfp, 'rfp.txt'), proposal: toFile(proposal, 'proposal.txt'), title, weights }, signal: controller.current.signal })
  }}><label className="field-label" htmlFor="review-title">Review name <span className="muted font-normal">(optional)</span></label><input id="review-title" className="text-input mb-6 max-w-xl" value={title} onChange={event => setTitle(event.target.value)} disabled={mutation.isPending} placeholder="Client name — project proposal"/><div className="document-grid"><DocumentInput label="Client RFP" value={rfp} onChange={value => { setRfp(value); mutation.reset() }} disabled={mutation.isPending} serverError={fields.rfp_file}/><DocumentInput label="Draft Proposal" value={proposal} onChange={value => { setProposal(value); mutation.reset() }} disabled={mutation.isPending} serverError={fields.proposal_file}/></div>
    <div className="mt-6"><RubricWeights weights={weights} onChange={setWeights} disabled={mutation.isPending}/></div>
    {mutation.error && <div className="error-banner mt-5" role="alert">{mutation.error.message}</div>}
    {mutation.isPending && <div className="notice mt-5" role="status"><LoaderCircle className="animate-spin shrink-0" size={20} style={{ animation: 'spin 1s linear infinite' }}/><div><strong>Review in progress</strong><p>The evaluator is checking your documents. Exact progress is not available. You can cancel at any time; cancelling this request may not stop backend processing.</p><Button type="button" variant="outline" className="mt-3" onClick={() => controller.current?.abort()}>Cancel review</Button></div></div>}
    <div className="form-footer"><p className="muted small">Evaluation, not generation. You stay in control of the final proposal.</p><Button size="lg" type="submit" disabled={mutation.isPending || !ready(rfp) || !ready(proposal) || !weightsValid(weights)}>{mutation.isPending ? 'Reviewing…' : 'Start review'}<ArrowRight size={16}/></Button></div></form></>
}
