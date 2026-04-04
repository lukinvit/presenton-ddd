const API_BASE = (process.env.NEXT_PUBLIC_API_URL || '') + '/api/v1';

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'APIError';
  }
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options?.headers,
  };
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new APIError(res.status, errorText);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}

// Auth
export const authAPI = {
  login: (email: string, password: string) =>
    fetchAPI<{ access_token: string; refresh_token: string }>('/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (data: {
    email: string;
    password: string;
  }) =>
    fetchAPI<{ access_token: string; refresh_token: string }>(
      '/register',
      {
        method: 'POST',
        body: JSON.stringify(data),
      },
    ),
};

// Presentations
export const presentationAPI = {
  list: () => fetchAPI<unknown[]>('/presentations'),

  get: (id: string) => fetchAPI<unknown>(`/presentations/${id}`),

  create: (data: unknown) =>
    fetchAPI<unknown>('/presentations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: unknown) =>
    fetchAPI<unknown>(`/presentations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchAPI<void>(`/presentations/${id}`, { method: 'DELETE' }),

  export: (id: string, format: 'pptx' | 'pdf') =>
    fetchAPI<{ download_url: string }>(`/presentations/${id}/export`, {
      method: 'POST',
      body: JSON.stringify({ format }),
    }),
};

// Slides
export const slideAPI = {
  list: (presentationId: string) =>
    fetchAPI<unknown[]>(`/presentations/${presentationId}/slides`),

  update: (presentationId: string, slideId: string, data: unknown) =>
    fetchAPI<unknown>(`/presentations/${presentationId}/slides/${slideId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  reorder: (presentationId: string, slideIds: string[]) =>
    fetchAPI<void>(`/presentations/${presentationId}/slides/reorder`, {
      method: 'POST',
      body: JSON.stringify({ slide_ids: slideIds }),
    }),
};

// Agents
export const agentAPI = {
  listConfigs: () => fetchAPI<unknown[]>('/agents'),

  updateConfig: (id: string, data: unknown) =>
    fetchAPI<unknown>(`/agents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  startPipeline: (presentationId: string) =>
    fetchAPI<{ run_id: string }>('/agents/pipeline', {
      method: 'POST',
      body: JSON.stringify({ presentation_id: presentationId }),
    }),

  getRun: (runId: string) => fetchAPI<unknown>(`/agents/runs/${runId}`),

  approveRalph: (runId: string, approved: boolean, feedback?: string) =>
    fetchAPI<void>(`/agents/ralph-loop/${runId}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved, feedback }),
    }),

  chat: (
    agent: string,
    messages: Array<{ role: string; content: string }>,
    presentationId?: string,
  ) =>
    fetchAPI<{ content: string; model: string; agent: string }>('/agents/chat', {
      method: 'POST',
      body: JSON.stringify({ agent, messages, presentation_id: presentationId }),
    }),

  generate: (
    messages: Array<{ role: string; content: string }>,
    slideCount: number,
    styleGuide?: string,
    presentationId?: string | null,
    mode?: string,
  ) =>
    fetchAPI<{
      presentation_id: string;
      slides: Array<{
        index: number;
        title: string;
        html: string;
        speaker_notes: string;
      }>;
      slide_count: number;
      pipeline_state: {
        current_stage: string;
        stages: Record<string, { status: string }>;
        quality_gates: Record<string, boolean>;
        decisions: Record<string, string>;
      };
      output_files: string[];
    }>('/agents/generate', {
      method: 'POST',
      signal: AbortSignal.timeout(10 * 60 * 1000), // 10 minute timeout
      body: JSON.stringify({
        messages,
        slide_count: slideCount,
        style_guide: styleGuide,
        presentation_id: presentationId ?? null,
        mode: mode ?? 'from_scratch',
      }),
    }),

  getWorkspace: (presentationId: string) =>
    fetchAPI<any>(`/agents/workspace/${presentationId}`),

  getArtifact: (presentationId: string, filename: string) =>
    fetchAPI<any>(`/agents/workspace/${presentationId}/artifact/${filename}`),
};

// Styles
export const styleAPI = {
  listPresets: () => fetchAPI<unknown[]>('/styles/presets'),

  listProfiles: () => fetchAPI<unknown[]>('/styles/presets'),

  createProfile: (data: unknown) =>
    fetchAPI<unknown>('/styles/presets', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  extractFromURL: (url: string) =>
    fetchAPI<unknown>('/styles/extract-from-url', {
      method: 'POST',
      body: JSON.stringify({ url }),
    }),

  uploadFile: (file: File) => {
    const token = getToken();
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${API_BASE}/styles/extract-from-file`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    }).then((r) => r.json());
  },
};

// Connections (API Key)
export const connectionAPI = {
  list: () => fetchAPI<Array<{ provider: string; connected: boolean }>>('/auth/connections').catch(() => [] as Array<{ provider: string; connected: boolean }>),

  connect: (provider: string, apiKey: string) =>
    fetchAPI<{ status: string; provider: string }>('/auth/connect/api-key', {
      method: 'POST',
      body: JSON.stringify({ provider, api_key: apiKey }),
    }),

  disconnect: (provider: string) =>
    fetchAPI<{ status: string; provider: string }>(`/auth/disconnect/${provider}`, {
      method: 'POST',
    }),
};

export { APIError };
export default fetchAPI;
