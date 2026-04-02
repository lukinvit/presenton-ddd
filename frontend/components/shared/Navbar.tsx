'use client';

import Link from 'next/link';
import { useDispatch } from 'react-redux';
import { LogOut, Settings, User } from 'lucide-react';
import { logout } from '@/store/slices/authSlice';
import type { AppDispatch } from '@/store/store';
import { useAuth } from '@/hooks/useAuth';

export function Navbar() {
  const dispatch = useDispatch<AppDispatch>();
  const { user } = useAuth();

  const handleLogout = () => {
    dispatch(logout());
  };

  return (
    <nav className="border-b border-slate-200 bg-white px-6 py-3">
      <div className="flex items-center justify-between">
        <Link href="/presentations" className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">P</span>
          </div>
          <span className="font-semibold text-slate-900">Presenton</span>
        </Link>

        <div className="flex items-center gap-2">
          {user && (
            <span className="text-sm text-slate-500 mr-2">
              {user.email}
            </span>
          )}
          <Link
            href="/settings/profile"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
          >
            <User className="h-4 w-4" />
          </Link>
          <Link
            href="/settings/agents"
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
          >
            <Settings className="h-4 w-4" />
          </Link>
          <button
            onClick={handleLogout}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-red-600"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </nav>
  );
}
