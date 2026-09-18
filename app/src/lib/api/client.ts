export class ApiError extends Error {
  status?: number
  fields: Record<string, string>
  constructor(message: string, status?: number, fields: Record<string, string> = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fields = fields
  }
}

export const apiConfig = {
  baseUrl: (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, ''),
  reviewPath: '/evaluate',
  historyPath: '/history',
  statsPath: '/stats',
}

export async function requestJson(
  path: string,
  options?: {
    method?: 'GET' | 'POST' | 'DELETE' | 'PUT'
    body?: FormData | unknown
    signal?: AbortSignal
  }
): Promise<unknown> {
  const method = options?.method ?? (options?.body instanceof FormData ? 'POST' : 'GET')
  const isFormData = options?.body instanceof FormData
  const headers: Record<string, string> = { Accept: 'application/json' }
  
  let body: BodyInit | undefined = undefined
  if (isFormData) {
    body = options.body as FormData
  } else if (options?.body !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.body)
  }

  try {
    const response = await fetch(`${apiConfig.baseUrl}${path}`, {
      method,
      headers,
      body,
      signal: options?.signal,
    })
    const payload: unknown = await response.json().catch(() => null)
    options?.signal?.throwIfAborted()

    if (!response.ok) {
      let detail = ''
      const fields: Record<string, string> = {}
      if (payload && typeof payload === 'object' && 'detail' in payload) {
        if (typeof payload.detail === 'string') {
          detail = payload.detail
        } else if (Array.isArray(payload.detail)) {
          detail = payload.detail
            .map((item: unknown) => {
              if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') {
                const field =
                  'loc' in item && Array.isArray(item.loc)
                    ? item.loc.find((part: unknown) => part === 'rfp_file' || part === 'proposal_file')
                    : undefined
                if (typeof field === 'string') {
                  fields[field] = item.msg
                  return `${field === 'rfp_file' ? 'RFP' : 'Proposal'}: ${item.msg}`
                }
                return item.msg
              }
              return 'Invalid document input'
            })
            .join('; ')
        }
      }

      const advice =
        response.status === 415
          ? ' Use PDF, Markdown or plain text.'
          : response.status === 422
          ? detail.toLowerCase().includes('weight')
            ? ' Adjust the rubric weights so all seven values total 100.'
            : ' Upload the document again or paste its text. Scanned PDFs need OCR first.'
          : response.status === 404
          ? ' The requested evaluation record was not found.'
          : ' Your documents are preserved; check the backend and try again.'

      throw new ApiError((detail || `Request failed (HTTP ${response.status}).`) + advice, response.status, fields)
    }

    if (payload === null && response.status !== 204) {
      throw new ApiError('The server returned invalid JSON. Check the API response format and try again.')
    }
    return payload
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (options?.signal?.aborted) throw new ApiError('Request cancelled.')
    throw new ApiError('Cannot reach the backend service. Check that the backend is running and the proxy is configured.')
  }
}
