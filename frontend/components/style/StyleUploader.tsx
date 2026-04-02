'use client';

import { useRef, useState } from 'react';
import { Upload, FileImage } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { styleAPI } from '@/lib/api';
import { useDispatch } from 'react-redux';
import type { AppDispatch } from '@/store/store';
import { fetchPresets } from '@/store/slices/styleSlice';

interface StyleUploaderProps {
  onUploaded: () => void;
}

export function StyleUploader({ onUploaded }: StyleUploaderProps) {
  const dispatch = useDispatch<AppDispatch>();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [dragOver, setDragOver] = useState(false);

  const handleFile = async (file: File) => {
    if (!file.type.startsWith('image/') && !file.name.endsWith('.pdf')) {
      setError('Please upload an image or PDF file.');
      return;
    }
    setError('');
    setIsUploading(true);
    try {
      await styleAPI.uploadFile(file);
      dispatch(fetchPresets());
      onUploaded();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div className="space-y-3">
      <div
        onDrop={handleDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => inputRef.current?.click()}
        className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 cursor-pointer transition-colors ${
          dragOver
            ? 'border-primary-400 bg-primary-50'
            : 'border-slate-300 hover:border-primary-300 hover:bg-slate-50'
        }`}
      >
        <FileImage className="h-10 w-10 text-slate-400 mb-3" />
        <p className="text-sm font-medium text-slate-700">
          Drop a brand image or PDF
        </p>
        <p className="text-xs text-slate-500 mt-1">
          or click to browse files
        </p>
        <input
          ref={inputRef}
          type="file"
          accept="image/*,.pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
      </div>

      {isUploading && (
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <Upload className="h-4 w-4 animate-bounce" />
          Uploading and extracting style...
        </div>
      )}
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
}
