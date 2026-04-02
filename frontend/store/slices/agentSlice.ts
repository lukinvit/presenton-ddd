import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { agentAPI } from '@/lib/api';
import type {
  AgentConfig,
  AgentRun,
  AgentState,
  PipelineEvent,
} from '@/types/agent';

const initialState: AgentState = {
  configs: [],
  currentRun: null,
  pipelineEvents: [],
  isLoading: false,
  error: null,
};

export const fetchAgentConfigs = createAsyncThunk(
  'agent/fetchConfigs',
  async (_, { rejectWithValue }) => {
    try {
      return await agentAPI.listConfigs();
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to fetch agent configs',
      );
    }
  },
);

export const updateAgentConfig = createAsyncThunk(
  'agent/updateConfig',
  async (
    { id, data }: { id: string; data: Partial<AgentConfig> },
    { rejectWithValue },
  ) => {
    try {
      return await agentAPI.updateConfig(id, data);
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to update agent config',
      );
    }
  },
);

export const startPipeline = createAsyncThunk(
  'agent/startPipeline',
  async (presentationId: string, { rejectWithValue }) => {
    try {
      return await agentAPI.startPipeline(presentationId);
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to start pipeline',
      );
    }
  },
);

export const fetchAgentRun = createAsyncThunk(
  'agent/fetchRun',
  async (runId: string, { rejectWithValue }) => {
    try {
      return await agentAPI.getRun(runId);
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to fetch run',
      );
    }
  },
);

export const approveRalph = createAsyncThunk(
  'agent/approveRalph',
  async (
    {
      runId,
      approved,
      feedback,
    }: { runId: string; approved: boolean; feedback?: string },
    { rejectWithValue },
  ) => {
    try {
      await agentAPI.approveRalph(runId, approved, feedback);
      return { approved, feedback };
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to submit approval',
      );
    }
  },
);

const agentSlice = createSlice({
  name: 'agent',
  initialState,
  reducers: {
    addPipelineEvent(state, action: PayloadAction<PipelineEvent>) {
      state.pipelineEvents.push(action.payload);
    },
    clearPipelineEvents(state) {
      state.pipelineEvents = [];
    },
    updateRunFromEvent(state, action: PayloadAction<PipelineEvent>) {
      const event = action.payload;
      if (!state.currentRun) return;
      if (event.type === 'pipeline_completed') {
        state.currentRun.status = 'completed';
        state.currentRun.progress = 100;
      } else if (event.type === 'pipeline_failed') {
        state.currentRun.status = 'failed';
      } else if (event.type === 'stage_started') {
        state.currentRun.current_stage = event.data.stage_name as string;
      } else if (event.type === 'agent_progress') {
        state.currentRun.progress = (event.data.progress as number) ?? state.currentRun.progress;
      }
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAgentConfigs.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchAgentConfigs.fulfilled, (state, action) => {
        state.isLoading = false;
        state.configs = action.payload as AgentConfig[];
      })
      .addCase(fetchAgentConfigs.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(updateAgentConfig.fulfilled, (state, action) => {
        const updated = action.payload as AgentConfig;
        const idx = state.configs.findIndex((c) => c.id === updated.id);
        if (idx !== -1) state.configs[idx] = updated;
      })
      .addCase(startPipeline.fulfilled, (state) => {
        state.pipelineEvents = [];
      })
      .addCase(fetchAgentRun.fulfilled, (state, action) => {
        state.currentRun = action.payload as AgentRun;
      });
  },
});

export const {
  addPipelineEvent,
  clearPipelineEvents,
  updateRunFromEvent,
  clearError,
} = agentSlice.actions;
export default agentSlice.reducer;
