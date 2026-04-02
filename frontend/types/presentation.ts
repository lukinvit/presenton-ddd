export type SlideElementType =
  | 'text'
  | 'heading'
  | 'image'
  | 'chart'
  | 'table'
  | 'list'
  | 'quote'
  | 'infographic';

export interface SlideElementStyle {
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  fontSize?: number;
  fontWeight?: string;
  color?: string;
  backgroundColor?: string;
  textAlign?: 'left' | 'center' | 'right';
  padding?: number;
  borderRadius?: number;
}

export interface SlideElement {
  id: string;
  type: SlideElementType;
  content: unknown;
  style: SlideElementStyle;
  order: number;
}

export interface Slide {
  id: string;
  presentation_id: string;
  title: string;
  layout: string;
  elements: SlideElement[];
  speaker_notes?: string;
  order: number;
  created_at: string;
  updated_at: string;
}

export type PresentationStatus =
  | 'draft'
  | 'generating'
  | 'ready'
  | 'exporting'
  | 'error';

export interface Presentation {
  id: string;
  title: string;
  topic: string;
  description?: string;
  status: PresentationStatus;
  slide_count: number;
  style_profile_id?: string;
  agent_run_id?: string;
  slides: Slide[];
  created_at: string;
  updated_at: string;
  owner_id: string;
}

export interface PresentationCreateRequest {
  title: string;
  topic: string;
  description?: string;
  style_profile_id?: string;
  slide_count?: number;
}

export interface PresentationState {
  presentations: Presentation[];
  currentPresentation: Presentation | null;
  isLoading: boolean;
  error: string | null;
}
