'use client';

import { useState } from 'react';
import { Dialog, DialogFooter } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import type { AgentConfig, AgentConfigDetails } from '@/types/agent';

type AgentConfigUpdate = Partial<Omit<AgentConfig, 'config'>> & {
  config?: Partial<AgentConfigDetails>;
};

interface AgentConfigEditorProps {
  config: AgentConfig;
  open: boolean;
  onClose: () => void;
  onSave: (id: string, data: AgentConfigUpdate) => Promise<void>;
}

const MODELS: string[] = [
  'claude-opus-4-6',
  'claude-sonnet-4-6',
  'claude-haiku-4-5',
  'gpt-4o',
  'gpt-4o-mini',
];

export function AgentConfigEditor({
  config,
  open,
  onClose,
  onSave,
}: AgentConfigEditorProps) {
  const [form, setForm] = useState({
    name: config.name,
    enabled: config.enabled,
    config: {
      model: config.config.model,
      system_prompt: config.config.system_prompt,
      temperature: config.config.temperature,
      max_tokens: config.config.max_tokens,
    },
  });
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(config.id, form);
      onClose();
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={`Edit: ${config.name}`}
      description="Configure this agent's behavior"
      className="max-w-2xl"
    >
      <div className="space-y-4">
        <Input
          label="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />

        <div className="flex flex-col gap-1">
          <label className="text-sm font-medium text-slate-700">Model</label>
          <select
            value={form.config.model}
            onChange={(e) =>
              setForm({ ...form, config: { ...form.config, model: e.target.value } })
            }
            className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {MODELS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        <Textarea
          label="System Prompt"
          value={form.config.system_prompt}
          onChange={(e) =>
            setForm({ ...form, config: { ...form.config, system_prompt: e.target.value } })
          }
          className="min-h-[140px]"
        />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Temperature"
            type="number"
            min={0}
            max={2}
            step={0.1}
            value={form.config.temperature}
            onChange={(e) =>
              setForm({ ...form, config: { ...form.config, temperature: parseFloat(e.target.value) } })
            }
          />
          <Input
            label="Max Tokens"
            type="number"
            min={100}
            max={200000}
            step={100}
            value={form.config.max_tokens}
            onChange={(e) =>
              setForm({ ...form, config: { ...form.config, max_tokens: parseInt(e.target.value) } })
            }
          />
        </div>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={form.enabled}
            onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
            className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="text-sm font-medium text-slate-700">Active</span>
        </label>
      </div>

      <DialogFooter>
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button isLoading={isSaving} onClick={handleSave}>
          Save Changes
        </Button>
      </DialogFooter>
    </Dialog>
  );
}
