'use client';

import { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import type { SlideElement } from '@/types/presentation';

interface InfographicEditorProps {
  element: SlideElement;
  onUpdate: (element: SlideElement) => void;
}

interface InfographicDataPoint {
  label: string;
  value: string | number;
  color?: string;
}

export function InfographicEditor({ element, onUpdate }: InfographicEditorProps) {
  const rawData = element.content as
    | { title?: string; data?: InfographicDataPoint[] }
    | undefined;

  const [title, setTitle] = useState(rawData?.title ?? '');
  const [dataPoints, setDataPoints] = useState<InfographicDataPoint[]>(
    rawData?.data ?? [{ label: '', value: '', color: '#0ea5e9' }],
  );

  const addDataPoint = () => {
    setDataPoints([
      ...dataPoints,
      { label: '', value: '', color: '#0ea5e9' },
    ]);
  };

  const removeDataPoint = (idx: number) => {
    const next = dataPoints.filter((_, i) => i !== idx);
    setDataPoints(next);
  };

  const updateDataPoint = (
    idx: number,
    field: keyof InfographicDataPoint,
    value: string,
  ) => {
    const next = dataPoints.map((dp, i) =>
      i === idx ? { ...dp, [field]: value } : dp,
    );
    setDataPoints(next);
  };

  const handleApply = () => {
    onUpdate({
      ...element,
      content: { title, data: dataPoints },
    });
  };

  return (
    <div className="space-y-4">
      <Input
        label="Chart Title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-slate-700">
            Data Points
          </label>
          <Button variant="ghost" size="sm" onClick={addDataPoint}>
            <Plus className="h-3.5 w-3.5" />
            Add
          </Button>
        </div>

        <div className="space-y-2">
          {dataPoints.map((dp, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <input
                type="color"
                value={dp.color ?? '#0ea5e9'}
                onChange={(e) => updateDataPoint(idx, 'color', e.target.value)}
                className="h-8 w-8 rounded border border-slate-300 cursor-pointer"
              />
              <Input
                placeholder="Label"
                value={dp.label}
                onChange={(e) => updateDataPoint(idx, 'label', e.target.value)}
                className="flex-1"
              />
              <Input
                placeholder="Value"
                value={String(dp.value)}
                onChange={(e) => updateDataPoint(idx, 'value', e.target.value)}
                className="w-24"
              />
              <button
                onClick={() => removeDataPoint(idx)}
                className="p-1.5 text-slate-400 hover:text-red-500"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      <Button onClick={handleApply} size="sm" className="w-full">
        Apply Changes
      </Button>
    </div>
  );
}
