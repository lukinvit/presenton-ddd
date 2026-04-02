'use client';

import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchPresets } from '@/store/slices/styleSlice';
import type { AppDispatch, RootState } from '@/store/store';
import { PresetGallery } from '@/components/style/PresetGallery';
import { URLStyleExtractor } from '@/components/style/URLStyleExtractor';
import { StyleUploader } from '@/components/style/StyleUploader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import type { StylePreset } from '@/types/style';

type Tab = 'presets' | 'url' | 'upload';

export default function StylesSettingsPage() {
  const dispatch = useDispatch<AppDispatch>();
  const { presets, isLoading } = useSelector(
    (state: RootState) => state.style,
  );
  const [activeTab, setActiveTab] = useState<Tab>('presets');
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);

  useEffect(() => {
    dispatch(fetchPresets());
  }, [dispatch]);

  const tabs: { key: Tab; label: string }[] = [
    { key: 'presets', label: 'Presets' },
    { key: 'url', label: 'From URL' },
    { key: 'upload', label: 'Upload' },
  ];

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Style Presets</h1>
        <p className="text-sm text-slate-500 mt-1">
          Choose or create a style for your presentations
        </p>
      </div>

      <Card className="max-w-4xl">
        <CardHeader>
          <div className="flex gap-1 border-b border-slate-200 -mx-6 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {activeTab === 'presets' && (
            <>
              {isLoading ? (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                  {[1, 2, 3, 4, 5, 6].map((n) => (
                    <div
                      key={n}
                      className="h-40 rounded-xl border border-slate-200 bg-slate-100 animate-pulse"
                    />
                  ))}
                </div>
              ) : (
                <PresetGallery
                  presets={presets}
                  selectedId={selectedPreset}
                  onSelect={(p: StylePreset) => setSelectedPreset(p.id)}
                />
              )}
            </>
          )}

          {activeTab === 'url' && (
            <div className="max-w-md">
              <p className="text-sm text-slate-600 mb-4">
                Enter a website URL to automatically extract its brand colors
                and typography.
              </p>
              <URLStyleExtractor
                onExtracted={() => setActiveTab('presets')}
              />
            </div>
          )}

          {activeTab === 'upload' && (
            <div className="max-w-md">
              <p className="text-sm text-slate-600 mb-4">
                Upload a brand guideline PDF or image to extract style
                information.
              </p>
              <StyleUploader
                onUploaded={() => setActiveTab('presets')}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
