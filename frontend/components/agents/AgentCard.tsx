import { Bot, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { AgentConfig } from '@/types/agent';

interface AgentCardProps {
  config: AgentConfig;
  onEdit: (config: AgentConfig) => void;
}

const roleLabels: Record<string, string> = {
  orchestrator: 'Orchestrator',
  researcher: 'Researcher',
  content_writer: 'Content Writer',
  designer: 'Designer',
  fact_checker: 'Fact Checker',
  ralph: 'Ralph (QA)',
};

export function AgentCard({ config, onEdit }: AgentCardProps) {
  return (
    <Card className="flex flex-col gap-0">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100">
              <Bot className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">{config.name}</h3>
              <p className="text-xs text-slate-500">
                {roleLabels[config.role] ?? config.role}
              </p>
            </div>
          </div>
          <span
            className={`flex items-center gap-1 text-xs font-medium ${
              config.is_active ? 'text-green-600' : 'text-slate-400'
            }`}
          >
            {config.is_active ? (
              <CheckCircle className="h-3.5 w-3.5" />
            ) : (
              <XCircle className="h-3.5 w-3.5" />
            )}
            {config.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>

        <div className="mt-4 space-y-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Model</span>
            <span className="font-mono text-xs bg-slate-100 px-2 py-0.5 rounded">
              {config.model}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Temperature</span>
            <span className="text-slate-700">{config.temperature}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Max Tokens</span>
            <span className="text-slate-700">
              {config.max_tokens.toLocaleString()}
            </span>
          </div>
        </div>

        <div className="mt-4">
          <Button
            variant="secondary"
            size="sm"
            className="w-full"
            onClick={() => onEdit(config)}
          >
            Edit Config
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
