export interface ColorPalette {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  text_primary: string;
  text_secondary: string;
  success: string;
  warning: string;
  error: string;
}

export interface Typography {
  heading_font: string;
  body_font: string;
  heading_size_scale: number;
  body_size: number;
  line_height: number;
  letter_spacing: number;
}

export interface StylePreset {
  id: string;
  name: string;
  description?: string;
  thumbnail_url?: string;
  color_palette: ColorPalette;
  typography: Typography;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
}

export interface StyleProfile {
  id: string;
  name: string;
  source_url?: string;
  color_palette: ColorPalette;
  typography: Typography;
  preset_id?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface StyleState {
  presets: StylePreset[];
  profiles: StyleProfile[];
  currentProfile: StyleProfile | null;
  isLoading: boolean;
  error: string | null;
}
