import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import presentationReducer from './slices/presentationSlice';
import agentReducer from './slices/agentSlice';
import styleReducer from './slices/styleSlice';
import ralphLoopReducer from './slices/ralphLoopSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    presentation: presentationReducer,
    agent: agentReducer,
    style: styleReducer,
    ralphLoop: ralphLoopReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
