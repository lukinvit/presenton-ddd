import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface RalphIteration {
  iteration: number;
  content_summary: string;
  feedback?: string;
  approved: boolean;
  timestamp: string;
}

export interface RalphLoopState {
  isActive: boolean;
  currentIteration: number;
  maxIterations: number;
  iterations: RalphIteration[];
  pendingApproval: boolean;
  approvalContent?: string;
  runId?: string;
}

const initialState: RalphLoopState = {
  isActive: false,
  currentIteration: 0,
  maxIterations: 3,
  iterations: [],
  pendingApproval: false,
  approvalContent: undefined,
  runId: undefined,
};

const ralphLoopSlice = createSlice({
  name: 'ralphLoop',
  initialState,
  reducers: {
    startRalphLoop(
      state,
      action: PayloadAction<{ runId: string; maxIterations?: number }>,
    ) {
      state.isActive = true;
      state.runId = action.payload.runId;
      state.maxIterations = action.payload.maxIterations ?? 3;
      state.currentIteration = 0;
      state.iterations = [];
      state.pendingApproval = false;
    },
    addIteration(state, action: PayloadAction<RalphIteration>) {
      state.iterations.push(action.payload);
      state.currentIteration = action.payload.iteration;
    },
    requestApproval(
      state,
      action: PayloadAction<{ content: string }>,
    ) {
      state.pendingApproval = true;
      state.approvalContent = action.payload.content;
    },
    submitApproval(
      state,
      action: PayloadAction<{ approved: boolean; feedback?: string }>,
    ) {
      state.pendingApproval = false;
      const lastIteration = state.iterations[state.iterations.length - 1];
      if (lastIteration) {
        lastIteration.approved = action.payload.approved;
        lastIteration.feedback = action.payload.feedback;
      }
    },
    completeRalphLoop(state) {
      state.isActive = false;
      state.pendingApproval = false;
    },
    resetRalphLoop() {
      return initialState;
    },
  },
});

export const {
  startRalphLoop,
  addIteration,
  requestApproval,
  submitApproval,
  completeRalphLoop,
  resetRalphLoop,
} = ralphLoopSlice.actions;
export default ralphLoopSlice.reducer;
