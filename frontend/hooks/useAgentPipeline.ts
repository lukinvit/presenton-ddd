'use client';

import { useCallback, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '@/store/store';
import {
  addPipelineEvent,
  fetchAgentRun,
  updateRunFromEvent,
} from '@/store/slices/agentSlice';
import {
  addIteration,
  requestApproval,
  completeRalphLoop,
} from '@/store/slices/ralphLoopSlice';
import { useWebSocket } from './useWebSocket';
import type { PipelineEvent } from '@/types/agent';

const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1';

export function useAgentPipeline(runId: string | null) {
  const dispatch = useDispatch<AppDispatch>();
  const { currentRun, pipelineEvents } = useSelector(
    (state: RootState) => state.agent,
  );
  const ralphLoop = useSelector((state: RootState) => state.ralphLoop);

  const wsUrl = runId
    ? `${WS_BASE}/agents/pipeline/${runId}/stream`
    : null;

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const pipelineEvent = JSON.parse(event.data as string) as PipelineEvent;
        dispatch(addPipelineEvent(pipelineEvent));
        dispatch(updateRunFromEvent(pipelineEvent));

        if (pipelineEvent.type === 'ralph_loop_iteration') {
          dispatch(
            addIteration({
              iteration: pipelineEvent.data.iteration as number,
              content_summary: pipelineEvent.data.content_summary as string,
              approved: false,
              timestamp: pipelineEvent.timestamp,
            }),
          );
        }

        if (pipelineEvent.type === 'human_approval_needed') {
          dispatch(
            requestApproval({
              content: pipelineEvent.data.content as string,
            }),
          );
        }

        if (pipelineEvent.type === 'pipeline_completed') {
          dispatch(completeRalphLoop());
          if (runId) dispatch(fetchAgentRun(runId));
        }
      } catch {
        // ignore parse errors
      }
    },
    [dispatch, runId],
  );

  const { status } = useWebSocket(wsUrl, {
    onMessage: handleMessage,
    reconnect: true,
  });

  useEffect(() => {
    if (runId) {
      dispatch(fetchAgentRun(runId));
    }
  }, [runId, dispatch]);

  return {
    currentRun,
    pipelineEvents,
    ralphLoop,
    wsStatus: status,
  };
}
