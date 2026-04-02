'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useDispatch, useSelector } from 'react-redux';
import {
  ArrowLeft,
  Download,
  Eye,
  Save,
} from 'lucide-react';
import {
  fetchPresentation,
  reorderSlides,
} from '@/store/slices/presentationSlice';
import { slideAPI } from '@/lib/api';
import type { AppDispatch, RootState } from '@/store/store';
import { Button } from '@/components/ui/Button';
import { SlideSorter } from '@/components/presentation/SlideSorter';
import { SlidePreview } from '@/components/presentation/SlidePreview';
import { SlideEditor } from '@/components/presentation/SlideEditor';
import type { Slide } from '@/types/presentation';

export default function PresentationEditorPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const dispatch = useDispatch<AppDispatch>();

  const { currentPresentation, isLoading } = useSelector(
    (state: RootState) => state.presentation,
  );

  const [selectedSlideId, setSelectedSlideId] = useState<string | null>(null);

  useEffect(() => {
    if (params.id) {
      dispatch(fetchPresentation(params.id));
    }
  }, [params.id, dispatch]);

  useEffect(() => {
    if (
      currentPresentation?.slides.length &&
      !selectedSlideId
    ) {
      const first = [...currentPresentation.slides].sort(
        (a, b) => a.order - b.order,
      )[0];
      setSelectedSlideId(first.id);
    }
  }, [currentPresentation, selectedSlideId]);

  const selectedSlide: Slide | null =
    currentPresentation?.slides.find((s) => s.id === selectedSlideId) ?? null;

  const handleReorder = async (slideIds: string[]) => {
    dispatch(reorderSlides(slideIds));
    if (params.id) {
      await slideAPI.reorder(params.id, slideIds);
    }
  };

  if (isLoading && !currentPresentation) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
      </div>
    );
  }

  if (!currentPresentation) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-slate-600 mb-4">Presentation not found</p>
          <Button onClick={() => router.push('/presentations')}>Back to Dashboard</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-slate-100">
      {/* Top bar */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/presentations')}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="font-semibold text-slate-900 text-sm">
              {currentPresentation.title}
            </h1>
            <p className="text-xs text-slate-500">
              {currentPresentation.slides.length} slides
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              router.push(`/presentations/${params.id}/preview`)
            }
          >
            <Eye className="h-4 w-4" />
            Preview
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              router.push(`/presentations/${params.id}/export`)
            }
          >
            <Download className="h-4 w-4" />
            Export
          </Button>
          <Button size="sm">
            <Save className="h-4 w-4" />
            Save
          </Button>
        </div>
      </div>

      {/* Editor layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Slide sorter */}
        <aside className="w-52 shrink-0 border-r border-slate-200 bg-white overflow-y-auto">
          <SlideSorter
            slides={currentPresentation.slides}
            selectedSlideId={selectedSlideId}
            onSelectSlide={setSelectedSlideId}
            onReorder={handleReorder}
          />
        </aside>

        {/* Slide preview area */}
        <main className="flex-1 flex items-center justify-center p-8 overflow-auto">
          {selectedSlide ? (
            <div className="w-full max-w-3xl">
              <SlidePreview slide={selectedSlide} isSelected />
            </div>
          ) : (
            <p className="text-slate-400 text-sm">Select a slide to preview</p>
          )}
        </main>

        {/* Properties panel */}
        <aside className="w-72 shrink-0 border-l border-slate-200 bg-white overflow-y-auto">
          {selectedSlide ? (
            <SlideEditor slide={selectedSlide} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-sm text-slate-400">No slide selected</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
