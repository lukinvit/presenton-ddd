'use client';

import { Input } from '@/components/ui/Input';
import type { Typography } from '@/types/style';

interface TypographyPickerProps {
  typography: Typography;
  onChange: (typography: Typography) => void;
}

const GOOGLE_FONTS = [
  'Inter',
  'Roboto',
  'Open Sans',
  'Lato',
  'Montserrat',
  'Raleway',
  'Poppins',
  'Playfair Display',
  'Merriweather',
  'Source Sans Pro',
];

export function TypographyPicker({ typography, onChange }: TypographyPickerProps) {
  const update = <K extends keyof Typography>(key: K, value: Typography[K]) => {
    onChange({ ...typography, [key]: value });
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-700">
          Heading Font
        </label>
        <select
          value={typography.heading_font}
          onChange={(e) => update('heading_font', e.target.value)}
          className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
          style={{ fontFamily: typography.heading_font }}
        >
          {GOOGLE_FONTS.map((f) => (
            <option key={f} value={f} style={{ fontFamily: f }}>
              {f}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-700">Body Font</label>
        <select
          value={typography.body_font}
          onChange={(e) => update('body_font', e.target.value)}
          className="block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
          style={{ fontFamily: typography.body_font }}
        >
          {GOOGLE_FONTS.map((f) => (
            <option key={f} value={f} style={{ fontFamily: f }}>
              {f}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Input
          label="Body Size (px)"
          type="number"
          min={8}
          max={24}
          value={typography.body_size}
          onChange={(e) => update('body_size', parseFloat(e.target.value))}
        />
        <Input
          label="Heading Scale"
          type="number"
          min={1}
          max={3}
          step={0.1}
          value={typography.heading_size_scale}
          onChange={(e) =>
            update('heading_size_scale', parseFloat(e.target.value))
          }
        />
        <Input
          label="Line Height"
          type="number"
          min={1}
          max={3}
          step={0.1}
          value={typography.line_height}
          onChange={(e) => update('line_height', parseFloat(e.target.value))}
        />
        <Input
          label="Letter Spacing"
          type="number"
          min={-2}
          max={10}
          step={0.1}
          value={typography.letter_spacing}
          onChange={(e) =>
            update('letter_spacing', parseFloat(e.target.value))
          }
        />
      </div>

      {/* Preview */}
      <div
        className="rounded-lg border border-slate-200 p-4 bg-white"
        style={{
          fontFamily: typography.body_font,
          fontSize: typography.body_size,
          lineHeight: typography.line_height,
          letterSpacing: typography.letter_spacing,
        }}
      >
        <p
          className="font-bold mb-1"
          style={{
            fontFamily: typography.heading_font,
            fontSize: typography.body_size * typography.heading_size_scale,
          }}
        >
          Heading Preview
        </p>
        <p className="text-slate-600">
          Body text preview. The quick brown fox jumps over the lazy dog.
        </p>
      </div>
    </div>
  );
}
