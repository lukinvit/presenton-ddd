'use client';

import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { formatDateTime } from '@/lib/utils';

export default function ProfilePage() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Profile</h1>
        <p className="text-sm text-slate-500 mt-1">
          Manage your account settings
        </p>
      </div>

      <div className="space-y-4 max-w-lg">
        <Card>
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4 pb-4 border-b border-slate-100">
                <div className="h-16 w-16 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                  <span className="text-primary-700 font-bold text-2xl uppercase">
                    {(user.full_name ?? user.username)[0]}
                  </span>
                </div>
                <div>
                  <p className="font-semibold text-slate-900">
                    {user.full_name ?? user.username}
                  </p>
                  <p className="text-sm text-slate-500">{user.email}</p>
                  <p className="text-xs text-slate-400 mt-1">
                    Member since {formatDateTime(user.created_at)}
                  </p>
                </div>
              </div>

              <Input label="Full Name" defaultValue={user.full_name ?? ''} />
              <Input label="Username" defaultValue={user.username} disabled />
              <Input label="Email" defaultValue={user.email} disabled />

              <Button variant="secondary" size="sm">
                Save Changes
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Danger Zone</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <p className="text-sm text-slate-600">
                Sign out of your account on this device.
              </p>
              <Button variant="danger" size="sm" onClick={logout}>
                Sign Out
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
