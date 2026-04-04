'use client';

import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchAgentConfigs,
  updateAgentConfig,
} from '@/store/slices/agentSlice';
import type { AppDispatch, RootState } from '@/store/store';
import { AgentCard } from '@/components/agents/AgentCard';
import { AgentConfigEditor } from '@/components/agents/AgentConfigEditor';
import type { AgentConfig, AgentConfigDetails } from '@/types/agent';

type AgentConfigUpdate = Partial<Omit<AgentConfig, 'config'>> & {
  config?: Partial<AgentConfigDetails>;
};

export default function AgentsSettingsPage() {
  const dispatch = useDispatch<AppDispatch>();
  const { configs, isLoading } = useSelector(
    (state: RootState) => state.agent,
  );
  const [editingConfig, setEditingConfig] = useState<AgentConfig | null>(null);

  useEffect(() => {
    dispatch(fetchAgentConfigs());
  }, [dispatch]);

  const handleSave = async (id: string, data: AgentConfigUpdate) => {
    await dispatch(updateAgentConfig({ id, data: data as Partial<AgentConfig> }));
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Agent Configuration</h1>
        <p className="text-sm text-slate-500 mt-1">
          Configure AI agents for the presentation generation pipeline
        </p>
      </div>

      {isLoading && configs.length === 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-48 rounded-xl border border-slate-200 bg-white animate-pulse"
            />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {configs.map((config) => (
            <AgentCard
              key={config.id}
              config={config}
              onEdit={setEditingConfig}
            />
          ))}
        </div>
      )}

      {editingConfig && (
        <AgentConfigEditor
          config={editingConfig}
          open={!!editingConfig}
          onClose={() => setEditingConfig(null)}
          onSave={handleSave}
        />
      )}
    </div>
  );
}
