export type AgentRole =
  | 'orchestrator'
  | 'researcher'
  | 'content_writer'
  | 'designer'
  | 'fact_checker'
  | 'ralph';

export type AgentModel =
  | 'claude-3-5-sonnet-20241022'
  | 'claude-3-opus-20240229'
  | 'claude-3-haiku-20240307'
  | 'gpt-4o'
  | 'gpt-4o-mini'
  | 'gpt-4-turbo';

export interface AgentConfig {
  id: string;
  role: AgentRole;
  name: string;
  model: AgentModel;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  tools_enabled: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
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
