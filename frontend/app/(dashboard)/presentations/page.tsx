'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useDispatch, useSelector } from 'react-redux';
import { Plus, Presentation, Trash2, MoreVertical } from 'lucide-react';
import {
  fetchPresentations,
  deletePresentation,
} from '@/store/slices/presentationSlice';
import type { AppDispatch, RootState } from '@/store/store';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Dialog, DialogFooter } from '@/components/ui/Dialog';
import { formatDate, truncate } from '@/lib/utils';
import type { Presentation as PresentationType } from '@/types/presentation';

const statusColors = {
  draft: 'bg-slate-100 text-slate-600',
  generating: 'bg-yellow-100 text-yellow-700',
  ready: 'bg-green-100 text-green-700',
  exporting: 'bg-blue-100 text-blue-700',
  error: 'bg-red-100 text-red-700',
};

function PresentationCard({
  presentation,
  onDelete,
}: {
  presentation: PresentationType;
  onDelete: (id: string) => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  return (
    <>
      <Card hover className="relative group">
        <CardContent className="pt-6">
          <div className="flex items-start justify-between gap-2">
            <Link
              href={`/presentations/${presentation.id}`}
              className="flex-1 min-w-0"
            >
              <div className="flex items-center gap-3 mb-3">
                <div className="h-10 w-10 rounded-lg bg-primary-100 flex items-center justify-center shrink-0">
                  <Presentation className="h-5 w-5 text-primary-600" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-slate-900 truncate">
                    {presentation.title}
                  </h3>
                  <span
                    className={`inline-block mt-0.5 rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[presentation.status]}`}
                  >
                    {presentation.status}
                  </span>
                </div>
              </div>

              {presentation.topic && (
                <p className="text-sm text-slate-500 mb-3">
                  {truncate(presentation.topic, 80)}
                </p>
              )}

              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span>{presentation.slide_count} slides</span>
                <span>{formatDate(presentation.updated_at)}</span>
              </div>
            </Link>

            <div className="relative">
              <button
                onClick={(e) => {
                  e.preventDefault();
                  setMenuOpen((v) => !v);
                }}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                <MoreVertical className="h-4 w-4" />
              </button>
              {menuOpen && (
                <div className="absolute right-0 top-8 z-10 w-36 rounded-lg border border-slate-200 bg-white shadow-lg py-1">
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      setDeleteOpen(true);
                    }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </button>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Delete Presentation"
        description={`Are you sure you want to delete "${presentation.title}"? This action cannot be undone.`}
      >
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDeleteOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={() => {
              onDelete(presentation.id);
              setDeleteOpen(false);
            }}
          >
            Delete
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
}

export default function DashboardPage() {
  const dispatch = useDispatch<AppDispatch>();
  const { presentations, isLoading } = useSelector(
    (state: RootState) => state.presentation,
  );

  useEffect(() => {
    dispatch(fetchPresentations());
  }, [dispatch]);

  const handleDelete = (id: string) => {
    dispatch(deletePresentation(id));
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Presentations</h1>
          <p className="text-sm text-slate-500 mt-1">
            {presentations.length} presentation{presentations.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Link href="/presentations/new">
          <Button>
            <Plus className="h-4 w-4" />
            New Presentation
          </Button>
        </Link>
      </div>

      {isLoading && presentations.length === 0 ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-40 rounded-xl border border-slate-200 bg-white animate-pulse"
            />
          ))}
        </div>
      ) : presentations.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-300 py-20">
          <Presentation className="h-12 w-12 text-slate-300 mb-4" />
          <h3 className="text-lg font-semibold text-slate-700 mb-1">
            No presentations yet
          </h3>
          <p className="text-sm text-slate-500 mb-6">
            Create your first AI-powered presentation
          </p>
          <Link href="/presentations/new">
            <Button>
              <Plus className="h-4 w-4" />
              New Presentation
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {presentations.map((p) => (
            <PresentationCard
              key={p.id}
              presentation={p}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
