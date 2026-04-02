'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useDispatch, useSelector } from 'react-redux';
import { ChevronRight, ChevronLeft } from 'lucide-react';
import { createPresentation } from '@/store/slices/presentationSlice';
import { fetchPresets, setCurrentPreset } from '@/store/slices/styleSlice';
import { startPipeline } from '@/store/slices/agentSlice';
import { startRalphLoop } from '@/store/slices/ralphLoopSlice';
import type { AppDispatch, RootState } from '@/store/store';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { PresetGallery } from '@/components/style/PresetGallery';
import { URLStyleExtractor } from '@/components/style/URLStyleExtractor';
import { StyleUploader } from '@/components/style/StyleUploader';
import { PipelineVisualizer } from '@/components/agents/PipelineVisualizer';
import { RalphLoopPanel } from '@/components/agents/RalphLoopPanel';
import { useAgentPipeline } from '@/hooks/useAgentPipeline';
import type { StylePreset } from '@/types/style';
import type { Presentation } from '@/types/presentation';
import { useEffect } from 'react';

type WizardStep = 'topic' | 'style' | 'agents' | 'progress';
type StyleTab = 'presets' | 'url' | 'upload';

const STEPS: { key: WizardStep; label: string }[] = [
  { key: 'topic', label: 'Topic' },
  { key: 'style', label: 'Style' },
  { key: 'agents', label: 'Agents' },
  { key: 'progress', label: 'Progress' },
];

export default function NewPresentationPage() {
  const router = useRouter();
  const dispatch = useDispatch<AppDispatch>();

  const { presets, currentPreset } = useSelector((state: RootState) => state.style);
  const { configs } = useSelector((state: RootState) => state.agent);

  const [step, setStep] = useState<WizardStep>('topic');
  const [topic, setTopic] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [slideCount, setSlideCount] = useState(10);
  const [styleTab, setStyleTab] = useState<StyleTab>('presets');
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [currentPresentationId, setCurrentPresentationId] = useState<string | null>(null);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const { currentRun, wsStatus } = useAgentPipeline(currentRunId);

  useEffect(() => {
    dispatch(fetchPresets());
  }, [dispatch]);

  // When pipeline completes, redirect to editor
  useEffect(() => {
    if (currentRun?.status === 'completed' && currentPresentationId) {
      setTimeout(() => {
        router.push(`/presentations/${currentPresentationId}`);
      }, 1500);
    }
  }, [currentRun?.status, currentPresentationId, router]);

  const canProceedTopic = topic.trim().length > 0;
  const currentStepIdx = STEPS.findIndex((s) => s.key === step);

  const handleNext = () => {
    const nextStep = STEPS[currentStepIdx + 1];
    if (nextStep) setStep(nextStep.key);
  };

  const handleBack = () => {
    const prevStep = STEPS[currentStepIdx - 1];
    if (prevStep) setStep(prevStep.key);
  };

  const handleStart = async () => {
    setIsCreating(true);
    try {
      const presentation = await dispatch(
        createPresentation({
          title: title || topic.slice(0, 60),
          topic,
          description,
          style_profile_id: currentPreset?.id,
          slide_count: slideCount,
        }),
      ).unwrap();

      const pres = presentation as Presentation;
      setCurrentPresentationId(pres.id);

      const run = await dispatch(startPipeline(pres.id)).unwrap();
      setCurrentRunId(run.run_id);

      dispatch(
        startRalphLoop({ runId: run.run_id, maxIterations: 3 }),
      );

      setStep('progress');
    } catch {
      // error handled by redux
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-center gap-2 mb-4">
            <button
              onClick={() => router.push('/presentations')}
              className="text-sm text-slate-500 hover:text-slate-700"
            >
              Dashboard
            </button>
            <ChevronRight className="h-4 w-4 text-slate-400" />
            <span className="text-sm font-medium text-slate-900">
              New Presentation
            </span>
          </div>

          {/* Step indicators */}
          <div className="flex items-center gap-0">
            {STEPS.map((s, idx) => {
              const isDone = idx < currentStepIdx;
              const isCurrent = s.key === step;
              return (
                <div key={s.key} className="flex items-center">
                  <div
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                      isCurrent
                        ? 'bg-primary-100 text-primary-700'
                        : isDone
                          ? 'text-green-700'
                          : 'text-slate-400'
                    }`}
                  >
                    <span
                      className={`h-5 w-5 rounded-full text-xs flex items-center justify-center font-bold ${
                        isCurrent
                          ? 'bg-primary-600 text-white'
                          : isDone
                            ? 'bg-green-500 text-white'
                            : 'bg-slate-200 text-slate-500'
                      }`}
                    >
                      {isDone ? '✓' : idx + 1}
                    </span>
                    {s.label}
                  </div>
                  {idx < STEPS.length - 1 && (
                    <div
                      className={`h-px w-8 ${isDone ? 'bg-green-400' : 'bg-slate-200'}`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-3xl px-6 py-10">
        {/* Step 1: Topic */}
        {step === 'topic' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">
                What&apos;s your presentation about?
              </h2>
              <p className="text-slate-500 mt-1">
                Describe your topic and we&apos;ll generate a complete presentation for you.
              </p>
            </div>

            <div className="space-y-4">
              <Textarea
                label="Topic / Prompt"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g. The future of renewable energy: solar, wind, and battery technology trends for 2025-2030"
                className="min-h-[120px]"
              />
              <Input
                label="Title (optional)"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Will be auto-generated if empty"
              />
              <Input
                label="Description (optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Additional context for the agents"
              />
              <div className="flex items-center gap-4">
                <Input
                  label="Number of Slides"
                  type="number"
                  min={3}
                  max={30}
                  value={slideCount}
                  onChange={(e) => setSlideCount(parseInt(e.target.value))}
                  className="w-32"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                disabled={!canProceedTopic}
                onClick={handleNext}
              >
                Next: Style
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Style */}
        {step === 'style' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">
                Choose a style
              </h2>
              <p className="text-slate-500 mt-1">
                Select a preset, extract from a URL, or upload brand materials.
              </p>
            </div>

            {/* Tab switcher */}
            <div className="flex gap-1 border-b border-slate-200">
              {(['presets', 'url', 'upload'] as StyleTab[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setStyleTab(tab)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors capitalize ${
                    styleTab === tab
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {tab === 'url' ? 'From URL' : tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            {styleTab === 'presets' && (
              <PresetGallery
                presets={presets}
                selectedId={selectedPreset}
                onSelect={(p: StylePreset) => {
                  setSelectedPreset(p.id);
                  dispatch(setCurrentPreset(null));
                }}
              />
            )}
            {styleTab === 'url' && (
              <URLStyleExtractor onExtracted={() => setStyleTab('presets')} />
            )}
            {styleTab === 'upload' && (
              <StyleUploader onUploaded={() => setStyleTab('presets')} />
            )}

            <div className="flex justify-between">
              <Button variant="ghost" onClick={handleBack}>
                <ChevronLeft className="h-4 w-4" />
                Back
              </Button>
              <Button onClick={handleNext}>
                Next: Agents
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Agent config review */}
        {step === 'agents' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">
                Agent configuration
              </h2>
              <p className="text-slate-500 mt-1">
                Review the agents that will create your presentation. You can
                adjust their settings in Settings &gt; Agents.
              </p>
            </div>

            {configs.length === 0 ? (
              <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-4">
                <p className="text-sm text-yellow-800">
                  No agents configured. The pipeline will use default settings.
                </p>
              </div>
            ) : (
              <div className="rounded-lg border border-slate-200 bg-white divide-y divide-slate-100">
                {configs
                  .filter((c) => c.is_active)
                  .map((config) => (
                    <div
                      key={config.id}
                      className="flex items-center justify-between px-4 py-3"
                    >
                      <div>
                        <p className="text-sm font-medium text-slate-900">
                          {config.name}
                        </p>
                        <p className="text-xs text-slate-500">{config.role}</p>
                      </div>
                      <span className="text-xs font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-600">
                        {config.model}
                      </span>
                    </div>
                  ))}
              </div>
            )}

            <div className="flex justify-between">
              <Button variant="ghost" onClick={handleBack}>
                <ChevronLeft className="h-4 w-4" />
                Back
              </Button>
              <Button isLoading={isCreating} onClick={handleStart}>
                Generate Presentation
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 4: Progress */}
        {step === 'progress' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">
                Generating your presentation
              </h2>
              <p className="text-slate-500 mt-1">
                The AI pipeline is running. This usually takes 1-3 minutes.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-6">
              {currentRun ? (
                <PipelineVisualizer run={currentRun} />
              ) : (
                <div className="flex items-center gap-3 text-sm text-slate-500">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary-200 border-t-primary-600" />
                  Initializing pipeline...
                </div>
              )}
            </div>

            <RalphLoopPanel />

            {currentRun?.status === 'completed' && (
              <div className="rounded-lg bg-green-50 border border-green-200 p-4">
                <p className="text-sm font-medium text-green-800">
                  Presentation ready! Redirecting to editor...
                </p>
              </div>
            )}

            {currentRun?.status === 'failed' && (
              <div className="space-y-3">
                <div className="rounded-lg bg-red-50 border border-red-200 p-4">
                  <p className="text-sm font-medium text-red-800">
                    Pipeline failed: {currentRun.error}
                  </p>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => router.push('/presentations')}
                >
                  Back to Dashboard
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
