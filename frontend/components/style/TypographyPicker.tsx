'use client';

import type { StyleTypography } from '@/types/style';

interface TypographyPickerProps {
  typography: StyleTypography;
  onChange: (typography: StyleTypography) => void;
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
  const update = <K extends keyof StyleTypography>(key: K, value: StyleTypography[K]) => {
    onChange({ ...typography, [key]: value });
  };

  const bodySize = typography.sizes?.body ?? '16px';
  const h1Size = typography.sizes?.h1 ?? '40px';

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

      {/* Preview */}
      <div
        className="rounded-lg border border-slate-200 p-4 bg-white"
        style={{
          fontFamily: typography.body_font,
          fontSize: bodySize,
        }}
      >
        <p
          className="font-bold mb-1"
          style={{
            fontFamily: typography.heading_font,
            fontSize: h1Size,
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
