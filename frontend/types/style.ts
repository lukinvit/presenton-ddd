export interface StyleColors {
  primary: string;
  secondary: string;
  accent: string[];
  background: string;
  text: string;
}

export interface StyleTypography {
  heading_font: string;
  body_font: string;
  sizes: Record<string, string>;
}

export interface StyleProfileData {
  id: string;
  name: string;
  source: string;
  colors: StyleColors;
  typography: StyleTypography;
  layout: Record<string, unknown>;
  spacing: Record<string, unknown>;
  created_at?: string;
}

export interface StylePreset {
  id: string;
  name: string;
  description?: string;
  is_builtin: boolean;
  profile: StyleProfileData;
}

export interface StyleState {
  presets: StylePreset[];
  currentPreset: StylePreset | null;
  isLoading: boolean;
  error: string | null;
}

// Legacy aliases kept for backward compatibility with editors that may use them
export type ColorPalette = StyleColors;
export type Typography = StyleTypography;
