'use client';

import { useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '@/store/store';
import { approveRalph } from '@/store/slices/agentSlice';
import { submitApproval } from '@/store/slices/ralphLoopSlice';

export function useRalphLoop() {
  const dispatch = useDispatch<AppDispatch>();
  const ralphLoop = useSelector((state: RootState) => state.ralphLoop);
  const currentRun = useSelector((state: RootState) => state.agent.currentRun);

  const approve = useCallback(
    async (feedback?: string) => {
      if (!currentRun?.id) return;
      await dispatch(
        approveRalph({ runId: currentRun.id, approved: true, feedback }),
      );
      dispatch(submitApproval({ approved: true, feedback }));
    },
    [dispatch, currentRun],
  );

  const reject = useCallback(
    async (feedback: string) => {
      if (!currentRun?.id) return;
      await dispatch(
        approveRalph({ runId: currentRun.id, approved: false, feedback }),
      );
      dispatch(submitApproval({ approved: false, feedback }));
    },
    [dispatch, currentRun],
  );

  return {
    ...ralphLoop,
    approve,
    reject,
  };
}
