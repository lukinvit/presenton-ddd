import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { presentationAPI, slideAPI } from '@/lib/api';
import type {
  Presentation,
  PresentationCreateRequest,
  PresentationState,
  Slide,
} from '@/types/presentation';

const initialState: PresentationState = {
  presentations: [],
  currentPresentation: null,
  isLoading: false,
  error: null,
};

export const fetchPresentations = createAsyncThunk(
  'presentation/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      return await presentationAPI.list();
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to fetch presentations',
      );
    }
  },
);

export const fetchPresentation = createAsyncThunk(
  'presentation/fetchOne',
  async (id: string, { rejectWithValue }) => {
    try {
      return await presentationAPI.get(id);
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to fetch presentation',
      );
    }
  },
);

export const createPresentation = createAsyncThunk(
  'presentation/create',
  async (data: PresentationCreateRequest, { rejectWithValue }) => {
    try {
      return await presentationAPI.create(data);
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to create presentation',
      );
    }
  },
);

export const updatePresentation = createAsyncThunk(
  'presentation/update',
  async (
    { id, data }: { id: string; data: Partial<Presentation> },
    { rejectWithValue },
  ) => {
    try {
      return await presentationAPI.update(id, data);
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to update presentation',
      );
    }
  },
);

export const deletePresentation = createAsyncThunk(
  'presentation/delete',
  async (id: string, { rejectWithValue }) => {
    try {
      await presentationAPI.delete(id);
      return id;
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to delete presentation',
      );
    }
  },
);

export const updateSlide = createAsyncThunk(
  'presentation/updateSlide',
  async (
    {
      presentationId,
      slideId,
      data,
    }: { presentationId: string; slideId: string; data: Partial<Slide> },
    { rejectWithValue },
  ) => {
    try {
      return await slideAPI.update(presentationId, slideId, data);
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to update slide',
      );
    }
  },
);

const presentationSlice = createSlice({
  name: 'presentation',
  initialState,
  reducers: {
    setCurrentPresentation(
      state,
      action: PayloadAction<Presentation | null>,
    ) {
      state.currentPresentation = action.payload;
    },
    clearError(state) {
      state.error = null;
    },
    reorderSlides(state, action: PayloadAction<string[]>) {
      if (!state.currentPresentation) return;
      const orderedSlides = action.payload
        .map((id) =>
          state.currentPresentation!.slides.find((s) => s.id === id),
        )
        .filter(Boolean) as Slide[];
      state.currentPresentation.slides = orderedSlides.map((s, i) => ({
        ...s,
        order: i,
      }));
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPresentations.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPresentations.fulfilled, (state, action) => {
        state.isLoading = false;
        state.presentations = action.payload as Presentation[];
      })
      .addCase(fetchPresentations.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchPresentation.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPresentation.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentPresentation = action.payload as Presentation;
      })
      .addCase(fetchPresentation.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(createPresentation.fulfilled, (state, action) => {
        state.presentations.unshift(action.payload as Presentation);
      })
      .addCase(deletePresentation.fulfilled, (state, action) => {
        state.presentations = state.presentations.filter(
          (p) => p.id !== action.payload,
        );
        if (state.currentPresentation?.id === action.payload) {
          state.currentPresentation = null;
        }
      })
      .addCase(updatePresentation.fulfilled, (state, action) => {
        const updated = action.payload as Presentation;
        const idx = state.presentations.findIndex((p) => p.id === updated.id);
        if (idx !== -1) state.presentations[idx] = updated;
        if (state.currentPresentation?.id === updated.id) {
          state.currentPresentation = updated;
        }
      })
      .addCase(updateSlide.fulfilled, (state, action) => {
        const updatedSlide = action.payload as Slide;
        if (!state.currentPresentation) return;
        const idx = state.currentPresentation.slides.findIndex(
          (s) => s.id === updatedSlide.id,
        );
        if (idx !== -1) {
          state.currentPresentation.slides[idx] = updatedSlide;
        }
      });
  },
});

export const { setCurrentPresentation, clearError, reorderSlides } =
  presentationSlice.actions;
export default presentationSlice.reducer;
