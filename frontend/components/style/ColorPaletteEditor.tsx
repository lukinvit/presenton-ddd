'use client';

import type { ColorPalette } from '@/types/style';

interface ColorPaletteEditorProps {
  palette: ColorPalette;
  onChange: (palette: ColorPalette) => void;
}

const PALETTE_FIELDS: { key: keyof ColorPalette; label: string }[] = [
  { key: 'primary', label: 'Primary' },
  { key: 'secondary', label: 'Secondary' },
  { key: 'accent', label: 'Accent' },
  { key: 'background', label: 'Background' },
  { key: 'surface', label: 'Surface' },
  { key: 'text_primary', label: 'Text Primary' },
  { key: 'text_secondary', label: 'Text Secondary' },
  { key: 'success', label: 'Success' },
  { key: 'warning', label: 'Warning' },
  { key: 'error', label: 'Error' },
];

export function ColorPaletteEditor({
  palette,
  onChange,
}: ColorPaletteEditorProps) {
  const handleChange = (key: keyof ColorPalette, value: string) => {
    onChange({ ...palette, [key]: value });
  };

  return (
    <div className="grid grid-cols-2 gap-3">
      {PALETTE_FIELDS.map(({ key, label }) => (
        <div key={key} className="flex items-center gap-2">
          <input
            type="color"
            value={palette[key]}
            onChange={(e) => handleChange(key, e.target.value)}
            className="h-8 w-8 rounded border border-slate-300 cursor-pointer shrink-0"
          />
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-700">{label}</p>
            <p className="text-xs text-slate-400 font-mono">{palette[key]}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
