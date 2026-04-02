'use client';

import { useState } from 'react';
import { GripVertical } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Slide } from '@/types/presentation';

interface SlideSorterProps {
  slides: Slide[];
  selectedSlideId: string | null;
  onSelectSlide: (slideId: string) => void;
  onReorder: (slideIds: string[]) => void;
}

export function SlideSorter({
  slides,
  selectedSlideId,
  onSelectSlide,
  onReorder,
}: SlideSorterProps) {
  const [dragging, setDragging] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState<string | null>(null);

  const sortedSlides = [...slides].sort((a, b) => a.order - b.order);

  const handleDragStart = (
    e: React.DragEvent<HTMLDivElement>,
    slideId: string,
  ) => {
    setDragging(slideId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (
    e: React.DragEvent<HTMLDivElement>,
    slideId: string,
  ) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOver(slideId);
  };

  const handleDrop = (
    e: React.DragEvent<HTMLDivElement>,
    targetId: string,
  ) => {
    e.preventDefault();
    if (!dragging || dragging === targetId) return;

    const currentOrder = sortedSlides.map((s) => s.id);
    const fromIdx = currentOrder.indexOf(dragging);
    const toIdx = currentOrder.indexOf(targetId);

    const newOrder = [...currentOrder];
    newOrder.splice(fromIdx, 1);
    newOrder.splice(toIdx, 0, dragging);

    onReorder(newOrder);
    setDragging(null);
    setDragOver(null);
  };

  const handleDragEnd = () => {
    setDragging(null);
    setDragOver(null);
  };

  return (
    <div className="flex flex-col gap-2 p-2 overflow-y-auto">
      {sortedSlides.map((slide, idx) => (
        <div
          key={slide.id}
          draggable
          onDragStart={(e) => handleDragStart(e, slide.id)}
          onDragOver={(e) => handleDragOver(e, slide.id)}
          onDrop={(e) => handleDrop(e, slide.id)}
          onDragEnd={handleDragEnd}
          onClick={() => onSelectSlide(slide.id)}
          className={cn(
            'group flex items-center gap-2 rounded-lg border p-2 cursor-pointer transition-all',
            selectedSlideId === slide.id
              ? 'border-primary-400 bg-primary-50'
              : 'border-slate-200 bg-white hover:border-slate-300',
            dragging === slide.id && 'opacity-50',
            dragOver === slide.id && 'border-primary-400 bg-primary-50',
          )}
        >
          <GripVertical className="h-4 w-4 text-slate-300 cursor-grab active:cursor-grabbing shrink-0" />

          <div className="flex-1 min-w-0">
            <div
              className="rounded bg-slate-100 flex items-center justify-center text-xs text-slate-400"
              style={{ aspectRatio: '16/9' }}
            >
              {idx + 1}
            </div>
            <p className="mt-1 text-xs text-slate-600 truncate">
              {slide.title || `Slide ${idx + 1}`}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
