'use client';

import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch, RootState } from '@/store/store';
import { fetchCurrentUser, logout } from '@/store/slices/authSlice';

export function useAuth() {
  const dispatch = useDispatch<AppDispatch>();
  const auth = useSelector((state: RootState) => state.auth);

  useEffect(() => {
    const token =
      typeof window !== 'undefined'
        ? localStorage.getItem('access_token')
        : null;
    if (token && !auth.isAuthenticated) {
      dispatch(fetchCurrentUser());
    }
  }, [dispatch, auth.isAuthenticated]);

  const handleLogout = () => {
    dispatch(logout());
  };

  return {
    user: auth.user,
    token: auth.token,
    isAuthenticated: auth.isAuthenticated,
    isLoading: auth.isLoading,
    error: auth.error,
    logout: handleLogout,
  };
}
