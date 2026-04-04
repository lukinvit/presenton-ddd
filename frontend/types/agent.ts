export interface AgentConfigDetails {
  model: string;
  provider: string;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  tools: string[];
}

export interface AgentConfig {
  id: string;
  name: string;
  config: AgentConfigDetails;
  enabled: boolean;
}

export type AgentRunStatus =
  | 'pending'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface AgentRunStage {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  output?: unknown;
  error?: string;
}

export interface AgentRun {
  id: string;
  presentation_id: string;
  status: AgentRunStatus;
  stages: AgentRunStage[];
  current_stage?: string;
  progress: number;
  error?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface PipelineEvent {
  type:
    | 'stage_started'
    | 'agent_progress'
    | 'stage_completed'
    | 'ralph_loop_iteration'
    | 'human_approval_needed'
    | 'pipeline_completed'
    | 'pipeline_failed';
  run_id: string;
  timestamp: string;
  data: Record<string, unknown>;
}

export interface AgentState {
  configs: AgentConfig[];
  currentRun: AgentRun | null;
  pipelineEvents: PipelineEvent[];
  isLoading: boolean;
  error: string | null;
}
