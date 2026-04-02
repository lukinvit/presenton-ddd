import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { styleAPI } from '@/lib/api';
import type { StylePreset, StyleState } from '@/types/style';

const initialState: StyleState = {
  presets: [],
  currentPreset: null,
  isLoading: false,
  error: null,
};

export const fetchPresets = createAsyncThunk(
  'style/fetchPresets',
  async (_, { rejectWithValue }) => {
    try {
      return await styleAPI.listPresets();
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to fetch presets',
      );
    }
  },
);

export const extractStyleFromURL = createAsyncThunk(
  'style/extractFromURL',
  async (url: string, { rejectWithValue }) => {
    try {
      return await styleAPI.extractFromURL(url);
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to extract style',
      );
    }
  },
);

const styleSlice = createSlice({
  name: 'style',
  initialState,
  reducers: {
    setCurrentPreset(state, action: PayloadAction<StylePreset | null>) {
      state.currentPreset = action.payload;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPresets.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPresets.fulfilled, (state, action) => {
        state.isLoading = false;
        state.presets = action.payload as StylePreset[];
      })
      .addCase(fetchPresets.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(extractStyleFromURL.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(extractStyleFromURL.fulfilled, (state) => {
        state.isLoading = false;
      })
      .addCase(extractStyleFromURL.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { setCurrentPreset, clearError } = styleSlice.actions;
export default styleSlice.reducer;
