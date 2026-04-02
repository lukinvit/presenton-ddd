'use client';

import { CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { StylePreset } from '@/types/style';

interface PresetGalleryProps {
  presets: StylePreset[];
  selectedId: string | null;
  onSelect: (preset: StylePreset) => void;
}

export function PresetGallery({
  presets,
  selectedId,
  onSelect,
}: PresetGalleryProps) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      {presets.map((preset) => {
        const isSelected = selectedId === preset.id;
        const palette = preset.color_palette;

        return (
          <button
            key={preset.id}
            onClick={() => onSelect(preset)}
            className={cn(
              'group relative rounded-xl border-2 overflow-hidden text-left transition-all',
              isSelected
                ? 'border-primary-500 shadow-lg'
                : 'border-slate-200 hover:border-primary-300',
            )}
          >
            {/* Color preview */}
            <div
              className="h-24 w-full"
              style={{ backgroundColor: palette.background }}
            >
              <div className="p-3 space-y-1.5">
                <div
                  className="h-3 w-3/4 rounded"
                  style={{ backgroundColor: palette.primary }}
                />
                <div
                  className="h-2 w-full rounded"
                  style={{ backgroundColor: palette.text_primary, opacity: 0.3 }}
                />
                <div
                  className="h-2 w-2/3 rounded"
                  style={{ backgroundColor: palette.text_secondary, opacity: 0.2 }}
                />
                <div className="flex gap-1 mt-2">
                  <div
                    className="h-4 w-8 rounded"
                    style={{ backgroundColor: palette.primary }}
                  />
                  <div
                    className="h-4 w-8 rounded"
                    style={{ backgroundColor: palette.secondary }}
                  />
                  <div
                    className="h-4 w-8 rounded"
                    style={{ backgroundColor: palette.accent }}
                  />
                </div>
              </div>
            </div>

            {/* Label */}
            <div className="px-3 py-2 bg-white">
              <p className="text-sm font-medium text-slate-800">{preset.name}</p>
              {preset.description && (
                <p className="text-xs text-slate-500 truncate">{preset.description}</p>
              )}
            </div>

            {isSelected && (
              <div className="absolute top-2 right-2">
                <CheckCircle className="h-5 w-5 text-primary-600 bg-white rounded-full" />
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
