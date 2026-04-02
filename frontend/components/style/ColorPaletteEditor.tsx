'use client';

import type { StyleColors } from '@/types/style';

interface ColorPaletteEditorProps {
  colors: StyleColors;
  onChange: (colors: StyleColors) => void;
}

const COLOR_FIELDS: { key: keyof Omit<StyleColors, 'accent'>; label: string }[] = [
  { key: 'primary', label: 'Primary' },
  { key: 'secondary', label: 'Secondary' },
  { key: 'background', label: 'Background' },
  { key: 'text', label: 'Text' },
];

export function ColorPaletteEditor({
  colors,
  onChange,
}: ColorPaletteEditorProps) {
  const handleChange = (key: keyof Omit<StyleColors, 'accent'>, value: string) => {
    onChange({ ...colors, [key]: value });
  };

  const handleAccentChange = (index: number, value: string) => {
    const newAccent = [...colors.accent];
    newAccent[index] = value;
    onChange({ ...colors, accent: newAccent });
  };

  return (
    <div className="grid grid-cols-2 gap-3">
      {COLOR_FIELDS.map(({ key, label }) => (
        <div key={key} className="flex items-center gap-2">
          <input
            type="color"
            value={colors[key] as string}
            onChange={(e) => handleChange(key, e.target.value)}
            className="h-8 w-8 rounded border border-slate-300 cursor-pointer shrink-0"
          />
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-700">{label}</p>
            <p className="text-xs text-slate-400 font-mono">{colors[key] as string}</p>
          </div>
        </div>
      ))}
      {colors.accent.map((accentColor, index) => (
        <div key={`accent-${index}`} className="flex items-center gap-2">
          <input
            type="color"
            value={accentColor}
            onChange={(e) => handleAccentChange(index, e.target.value)}
            className="h-8 w-8 rounded border border-slate-300 cursor-pointer shrink-0"
          />
          <div className="min-w-0">
            <p className="text-xs font-medium text-slate-700">
              {colors.accent.length > 1 ? `Accent ${index + 1}` : 'Accent'}
            </p>
            <p className="text-xs text-slate-400 font-mono">{accentColor}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
