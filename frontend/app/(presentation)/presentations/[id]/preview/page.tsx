'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useDispatch, useSelector } from 'react-redux';
import { ArrowLeft, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { fetchPresentation } from '@/store/slices/presentationSlice';
import type { AppDispatch, RootState } from '@/store/store';
import { SlidePreview } from '@/components/presentation/SlidePreview';
import { Button } from '@/components/ui/Button';
import type { Slide } from '@/types/presentation';

export default function PresentationPreviewPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const dispatch = useDispatch<AppDispatch>();

  const { currentPresentation } = useSelector(
    (state: RootState) => state.presentation,
  );

  const [currentIdx, setCurrentIdx] = useState(0);

  useEffect(() => {
    if (params.id) dispatch(fetchPresentation(params.id));
  }, [params.id, dispatch]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        setCurrentIdx((i) => Math.min(i + 1, slides.length - 1));
      }
      if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        setCurrentIdx((i) => Math.max(i - 1, 0));
      }
      if (e.key === 'Escape') {
        router.back();
      }
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  });

  const slides: Slide[] = currentPresentation
    ? [...currentPresentation.slides].sort((a, b) => a.order - b.order)
    : [];

  const currentSlide = slides[currentIdx];

  return (
    <div className="flex h-screen flex-col bg-slate-900">
      {/* Controls */}
      <div className="flex items-center justify-between px-4 py-3 bg-slate-800 text-white">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Editor
        </button>
        <div className="flex items-center gap-3 text-sm text-slate-400">
          <span>
            {currentIdx + 1} / {slides.length}
          </span>
        </div>
        <button
          onClick={() => router.back()}
          className="text-slate-400 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Slide area */}
      <div className="flex flex-1 items-center justify-center p-8">
        {currentSlide && (
          <div className="w-full max-w-5xl">
            <SlidePreview slide={currentSlide} isSelected />
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-center gap-4 py-4 bg-slate-800">
        <Button
          variant="ghost"
          size="sm"
          disabled={currentIdx === 0}
          onClick={() => setCurrentIdx((i) => Math.max(i - 1, 0))}
          className="text-white hover:text-white hover:bg-slate-700"
        >
          <ChevronLeft className="h-5 w-5" />
          Previous
        </Button>

        <div className="flex gap-1">
          {slides.map((_, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentIdx(idx)}
              className={`h-1.5 rounded-full transition-all ${
                idx === currentIdx
                  ? 'w-6 bg-primary-400'
                  : 'w-1.5 bg-slate-600 hover:bg-slate-500'
              }`}
            />
          ))}
        </div>

        <Button
          variant="ghost"
          size="sm"
          disabled={currentIdx === slides.length - 1}
          onClick={() =>
            setCurrentIdx((i) => Math.min(i + 1, slides.length - 1))
          }
          className="text-white hover:text-white hover:bg-slate-700"
        >
          Next
          <ChevronRight className="h-5 w-5" />
        </Button>
      </div>
    </div>
  );
}
