'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Download, FileType, File } from 'lucide-react';
import { presentationAPI } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';

type ExportFormat = 'pptx' | 'pdf';

interface FormatOption {
  format: ExportFormat;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const FORMAT_OPTIONS: FormatOption[] = [
  {
    format: 'pptx',
    label: 'PowerPoint (.pptx)',
    description: 'Editable PowerPoint file compatible with Microsoft Office and Google Slides',
    icon: <FileType className="h-8 w-8 text-orange-500" />,
  },
  {
    format: 'pdf',
    label: 'PDF (.pdf)',
    description: 'Non-editable PDF for sharing and printing',
    icon: <File className="h-8 w-8 text-red-500" />,
  },
];

export default function ExportPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('pptx');
  const [isExporting, setIsExporting] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState('');

  const handleExport = async () => {
    setIsExporting(true);
    setError('');
    try {
      const { download_url } = await presentationAPI.export(
        params.id,
        selectedFormat,
      );
      setDownloadUrl(download_url);
      // Trigger download
      const a = document.createElement('a');
      a.href = download_url;
      a.download = `presentation.${selectedFormat}`;
      a.click();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-lg">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 mb-6"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Editor
        </button>

        <h1 className="text-2xl font-bold text-slate-900 mb-2">
          Export Presentation
        </h1>
        <p className="text-slate-500 mb-6">
          Choose a format to export your presentation.
        </p>

        <div className="space-y-3 mb-6">
          {FORMAT_OPTIONS.map((opt) => (
            <button
              key={opt.format}
              onClick={() => setSelectedFormat(opt.format)}
              className={`w-full flex items-start gap-4 rounded-xl border-2 p-4 text-left transition-all ${
                selectedFormat === opt.format
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-slate-200 bg-white hover:border-primary-300'
              }`}
            >
              {opt.icon}
              <div>
                <p className="font-semibold text-slate-900">{opt.label}</p>
                <p className="text-sm text-slate-500">{opt.description}</p>
              </div>
            </button>
          ))}
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 p-3 mb-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {downloadUrl && !isExporting && (
          <div className="rounded-lg bg-green-50 border border-green-200 p-3 mb-4">
            <p className="text-sm text-green-700 font-medium">
              Export ready!{' '}
              <a
                href={downloadUrl}
                className="underline"
                download
              >
                Click here to download
              </a>
            </p>
          </div>
        )}

        <Button
          isLoading={isExporting}
          onClick={handleExport}
          className="w-full"
        >
          <Download className="h-4 w-4" />
          Export as {selectedFormat.toUpperCase()}
        </Button>
      </div>
    </div>
  );
}
