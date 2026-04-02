import { createAsyncThunk, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { authAPI } from '@/lib/api';
import type { AuthState, User } from '@/types/auth';

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

export const login = createAsyncThunk(
  'auth/login',
  async (
    { email, password }: { email: string; password: string },
    { rejectWithValue },
  ) => {
    try {
      const tokenData = await authAPI.login(email, password);
      localStorage.setItem('access_token', tokenData.access_token);
      return { token: tokenData.access_token, user: { id: '', email, roles: [] } as User };
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Login failed',
      );
    }
  },
);

export const register = createAsyncThunk(
  'auth/register',
  async (
    data: { email: string; password: string },
    { rejectWithValue, dispatch },
  ) => {
    try {
      const tokenData = await authAPI.register(data);
      localStorage.setItem('access_token', tokenData.access_token);
      return { token: tokenData.access_token, user: { id: '', email: data.email, roles: [] } as User };
    } catch (err) {
      return rejectWithValue(
        err instanceof Error ? err.message : 'Registration failed',
      );
    }
  },
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout(state) {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.error = null;
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token');
      }
    },
    clearError(state) {
      state.error = null;
    },
    setToken(state, action: PayloadAction<string>) {
      state.token = action.payload;
      state.isAuthenticated = true;
    },
    restoreSession(state) {
      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('access_token');
        if (token) {
          state.token = token;
          state.isAuthenticated = true;
        }
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.token = action.payload.token;
        state.user = action.payload.user;
        state.isAuthenticated = true;
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.isLoading = false;
        state.token = action.payload.token;
        state.user = action.payload.user;
        state.isAuthenticated = true;
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { logout, clearError, setToken, restoreSession } = authSlice.actions;
export default authSlice.reducer;
