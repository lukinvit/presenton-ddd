import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { styleAPI } from '@/lib/api';
import type { StylePreset, StyleProfile, StyleState } from '@/types/style';

const initialState: StyleState = {
  presets: [],
  profiles: [],
  currentProfile: null,
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

export const fetchProfiles = createAsyncThunk(
  'style/fetchProfiles',
  async (_, { rejectWithValue }) => {
    try {
      return await styleAPI.listProfiles();
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to fetch profiles',
      );
    }
  },
);

export const createStyleProfile = createAsyncThunk(
  'style/createProfile',
  async (data: Partial<StyleProfile>, { rejectWithValue }) => {
    try {
      return await styleAPI.createProfile(data);
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Failed to create style profile',
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
    setCurrentProfile(state, action: PayloadAction<StyleProfile | null>) {
      state.currentProfile = action.payload;
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPresets.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchPresets.fulfilled, (state, action) => {
        state.isLoading = false;
        state.presets = action.payload as StylePreset[];
      })
      .addCase(fetchPresets.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(fetchProfiles.fulfilled, (state, action) => {
        state.profiles = action.payload as StyleProfile[];
      })
      .addCase(createStyleProfile.fulfilled, (state, action) => {
        state.profiles.push(action.payload as StyleProfile);
        state.currentProfile = action.payload as StyleProfile;
      })
      .addCase(extractStyleFromURL.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(extractStyleFromURL.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentProfile = action.payload as StyleProfile;
      })
      .addCase(extractStyleFromURL.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { setCurrentProfile, clearError } = styleSlice.actions;
export default styleSlice.reducer;
