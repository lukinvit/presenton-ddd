'use client';

import { useState } from 'react';
import { CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { useRalphLoop } from '@/hooks/useRalphLoop';

export function RalphLoopPanel() {
  const {
    isActive,
    pendingApproval,
    approvalContent,
    currentIteration,
    maxIterations,
    iterations,
    approve,
    reject,
  } = useRalphLoop();

  const [feedback, setFeedback] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isActive) return null;

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      await approve(feedback || undefined);
      setFeedback('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!feedback.trim()) return;
    setIsSubmitting(true);
    try {
      await reject(feedback);
      setFeedback('');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <RefreshCw className="h-5 w-5 text-primary-600" />
          Ralph Quality Loop
        </CardTitle>
        <p className="text-sm text-slate-500">
          Iteration {currentIteration} of {maxIterations}
        </p>
      </CardHeader>
      <CardContent>
        {/* Iteration history */}
        {iterations.length > 0 && (
          <div className="mb-4 space-y-2">
            {iterations.map((iter) => (
              <div
                key={iter.iteration}
                className="flex items-start gap-2 rounded-lg bg-slate-50 p-3 text-sm"
              >
                <span className="font-mono text-xs text-slate-500 mt-0.5">
                  #{iter.iteration}
                </span>
                <div className="flex-1">
                  <p className="text-slate-700">{iter.content_summary}</p>
                  {iter.feedback && (
                    <p className="mt-1 text-xs text-slate-500 italic">
                      Feedback: {iter.feedback}
                    </p>
                  )}
                </div>
                {iter.approved ? (
                  <CheckCircle className="h-4 w-4 text-green-500 shrink-0" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-400 shrink-0" />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Approval UI */}
        {pendingApproval && (
          <div className="space-y-3">
            <div className="rounded-lg border border-primary-200 bg-primary-50 p-3">
              <p className="text-sm font-medium text-primary-800">
                Human approval required
              </p>
              {approvalContent && (
                <p className="mt-1 text-sm text-primary-700">
                  {approvalContent}
                </p>
              )}
            </div>

            <Textarea
              label="Feedback (optional for approval, required for rejection)"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Enter your feedback..."
              className="min-h-[80px]"
            />

            <div className="flex gap-2">
              <Button
                variant="danger"
                size="sm"
                className="flex-1"
                isLoading={isSubmitting}
                disabled={!feedback.trim()}
                onClick={handleReject}
              >
                <XCircle className="h-4 w-4" />
                Reject & Iterate
              </Button>
              <Button
                size="sm"
                className="flex-1"
                isLoading={isSubmitting}
                onClick={handleApprove}
              >
                <CheckCircle className="h-4 w-4" />
                Approve
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
