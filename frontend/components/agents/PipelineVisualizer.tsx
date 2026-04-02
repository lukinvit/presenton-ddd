'use client';

import { CheckCircle, Circle, Loader, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { AgentRun, AgentRunStage } from '@/types/agent';

interface PipelineVisualizerProps {
  run: AgentRun;
}

function StageIcon({ status }: { status: AgentRunStage['status'] }) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case 'running':
      return <Loader className="h-5 w-5 text-primary-500 animate-spin" />;
    case 'failed':
      return <XCircle className="h-5 w-5 text-red-500" />;
    default:
      return <Circle className="h-5 w-5 text-slate-300" />;
  }
}

export function PipelineVisualizer({ run }: PipelineVisualizerProps) {
  const progressPercent = Math.min(100, Math.max(0, run.progress));

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium text-slate-700">
            {run.current_stage ?? run.status}
          </span>
          <span className="text-slate-500">{progressPercent}%</span>
        </div>
        <div className="h-2 w-full rounded-full bg-slate-100">
          <div
            className="h-2 rounded-full bg-primary-500 transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Stages list */}
      {run.stages.length > 0 && (
        <ol className="space-y-3">
          {run.stages.map((stage, idx) => (
            <li key={idx} className="flex items-start gap-3">
              <StageIcon status={stage.status} />
              <div className="flex-1 min-w-0">
                <p
                  className={cn(
                    'text-sm font-medium',
                    stage.status === 'running'
                      ? 'text-primary-700'
                      : stage.status === 'completed'
                        ? 'text-slate-700'
                        : stage.status === 'failed'
                          ? 'text-red-700'
                          : 'text-slate-400',
                  )}
                >
                  {stage.name}
                </p>
                {stage.error && (
                  <p className="text-xs text-red-500 mt-0.5">{stage.error}</p>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}

      {run.error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3">
          <p className="text-sm text-red-700">{run.error}</p>
        </div>
      )}
    </div>
  );
}
