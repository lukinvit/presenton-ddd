'use client';

import { useState } from 'react';
import { Link, Loader } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useDispatch } from 'react-redux';
import type { AppDispatch } from '@/store/store';
import { extractStyleFromURL } from '@/store/slices/styleSlice';

interface URLStyleExtractorProps {
  onExtracted: () => void;
}

export function URLStyleExtractor({ onExtracted }: URLStyleExtractorProps) {
  const dispatch = useDispatch<AppDispatch>();
  const [url, setUrl] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState('');

  const handleExtract = async () => {
    if (!url) return;
    setError('');
    setIsExtracting(true);
    try {
      await dispatch(extractStyleFromURL(url)).unwrap();
      onExtracted();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to extract style');
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Link className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleExtract()}
            placeholder="https://example.com"
            className="block w-full rounded-lg border border-slate-300 pl-9 pr-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <Button
          isLoading={isExtracting}
          disabled={!url}
          onClick={handleExtract}
          size="sm"
        >
          {isExtracting ? <Loader className="h-4 w-4 animate-spin" /> : 'Extract'}
        </Button>
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
      <p className="text-xs text-slate-500">
        Extract brand colors and typography from any website URL.
      </p>
    </div>
  );
}
