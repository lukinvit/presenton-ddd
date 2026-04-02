'use client';

import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { updateSlide } from '@/store/slices/presentationSlice';
import type { AppDispatch } from '@/store/store';
import type { Slide } from '@/types/presentation';

interface SlideEditorProps {
  slide: Slide;
}

export function SlideEditor({ slide }: SlideEditorProps) {
  const dispatch = useDispatch<AppDispatch>();
  const [title, setTitle] = useState(slide.title);
  const [notes, setNotes] = useState(slide.speaker_notes ?? '');
  const [isSaving, setIsSaving] = useState(false);

  const hasChanges =
    title !== slide.title || notes !== (slide.speaker_notes ?? '');

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await dispatch(
        updateSlide({
          presentationId: slide.presentation_id,
          slideId: slide.id,
          data: { title, speaker_notes: notes },
        }),
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-700 mb-3">
          Slide Properties
        </h3>
        <div className="space-y-3">
          <Input
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <Textarea
            label="Speaker Notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add speaker notes..."
            className="min-h-[100px]"
          />
        </div>
      </div>

      {slide.elements.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-3">
            Elements ({slide.elements.length})
          </h3>
          <div className="space-y-2">
            {[...slide.elements]
              .sort((a, b) => a.order - b.order)
              .map((el) => (
                <div
                  key={el.id}
                  className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2"
                >
                  <span className="text-xs font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                    {el.type}
                  </span>
                  <p className="text-xs text-slate-500 truncate flex-1">
                    {typeof el.content === 'string'
                      ? el.content.slice(0, 50)
                      : JSON.stringify(el.content).slice(0, 50)}
                  </p>
                </div>
              ))}
          </div>
        </div>
      )}

      {hasChanges && (
        <Button isLoading={isSaving} onClick={handleSave} size="sm">
          Save Changes
        </Button>
      )}
    </div>
  );
}
