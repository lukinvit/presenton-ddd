'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDispatch, useSelector } from 'react-redux';
import { ChevronRight, ChevronLeft, Send, Sparkles, CheckCircle2, Circle, Loader2, Download } from 'lucide-react';
import { fetchPresets, setCurrentPreset } from '@/store/slices/styleSlice';
import type { AppDispatch, RootState } from '@/store/store';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { PresetGallery } from '@/components/style/PresetGallery';
import { URLStyleExtractor } from '@/components/style/URLStyleExtractor';
import { StyleUploader } from '@/components/style/StyleUploader';
import { agentAPI } from '@/lib/api';
import type { StylePreset } from '@/types/style';

type WizardStep = 'interview' | 'style' | 'generate' | 'results';
type StyleTab = 'presets' | 'url' | 'upload';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface GeneratedSlide {
  index: number;
  title: string;
  html: string;
  speaker_notes: string;
}

interface PipelineStageInfo {
  key: string;
  label: string;
  /** Approximate seconds from start when this stage typically begins */
  estimatedStartSec: number;
}

const PIPELINE_STAGES: PipelineStageInfo[] = [
  { key: 'INTAKE',     label: 'Analyzing requirements',   estimatedStartSec: 0   },
  { key: 'INGEST',     label: 'Collecting materials',     estimatedStartSec: 15  },
  { key: 'PARSE',      label: 'Parsing structure',        estimatedStartSec: 30  },
  { key: 'STRATEGY',   label: 'Choosing strategy',        estimatedStartSec: 45  },
  { key: 'BASE',       label: 'Building design system',   estimatedStartSec: 60  },
  { key: 'CONTENT',    label: 'Writing slide content',    estimatedStartSec: 80  },
  { key: 'ASSETS',     label: 'Preparing assets',         estimatedStartSec: 120 },
  { key: 'ENRICHMENT', label: 'Verifying facts',          estimatedStartSec: 150 },
  { key: 'RENDER_QA',  label: 'Rendering & QA',           estimatedStartSec: 180 },
  { key: 'PACKAGE',    label: 'Packaging deliverables',   estimatedStartSec: 220 },
];

const STEPS: { key: WizardStep; label: string }[] = [
  { key: 'interview', label: 'Interview' },
  { key: 'style', label: 'Style' },
  { key: 'generate', label: 'Generate' },
  { key: 'results', label: 'Results' },
];

type StageStatus = 'pending' | 'running' | 'completed';

function getOptimisticStageStatuses(elapsedSec: number): Record<string, StageStatus> {
  const result: Record<string, StageStatus> = {};
  for (let i = 0; i < PIPELINE_STAGES.length; i++) {
    const stage = PIPELINE_STAGES[i];
    const nextStage = PIPELINE_STAGES[i + 1];
    if (elapsedSec < stage.estimatedStartSec) {
      result[stage.key] = 'pending';
    } else if (!nextStage || elapsedSec < nextStage.estimatedStartSec) {
      result[stage.key] = 'running';
    } else {
      result[stage.key] = 'completed';
    }
  }
  return result;
}

export default function NewPresentationPage() {
  const router = useRouter();
  const dispatch = useDispatch<AppDispatch>();

  const { presets } = useSelector((state: RootState) => state.style);

  const [step, setStep] = useState<WizardStep>('interview');
  const [slideCount, setSlideCount] = useState(10);
  const [styleTab, setStyleTab] = useState<StyleTab>('presets');
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [briefReady, setBriefReady] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState('');
  const [generatedSlides, setGeneratedSlides] = useState<GeneratedSlide[]>([]);
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const [presentationId, setPresentationId] = useState<string | null>(null);
  const [outputFiles, setOutputFiles] = useState<string[]>([]);
  const [pipelineState, setPipelineState] = useState<{
    current_stage: string;
    stages: Record<string, { status: string }>;
    quality_gates: Record<string, boolean>;
    decisions: Record<string, string>;
  } | null>(null);

  // Optimistic stage progress
  const [elapsedSec, setElapsedSec] = useState(0);
  const startTimeRef = useRef<number>(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    dispatch(fetchPresets());
  }, [dispatch]);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isChatLoading]);

  // After 3+ user messages, allow generating
  useEffect(() => {
    const userMsgCount = chatMessages.filter((m) => m.role === 'user').length;
    if (userMsgCount >= 3) {
      setBriefReady(true);
    }
  }, [chatMessages]);

  // Tick elapsed time while generating
  useEffect(() => {
    if (isGenerating) {
      startTimeRef.current = Date.now();
      setElapsedSec(0);
      timerRef.current = setInterval(() => {
        setElapsedSec(Math.floor((Date.now() - startTimeRef.current) / 1000));
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isGenerating]);

  const currentStepIdx = STEPS.findIndex((s) => s.key === step);

  const handleNext = () => {
    const nextStep = STEPS[currentStepIdx + 1];
    if (nextStep) setStep(nextStep.key);
  };

  const handleBack = () => {
    const prevStep = STEPS[currentStepIdx - 1];
    if (prevStep) setStep(prevStep.key);
  };

  // ------------------------------------------------------------------
  // Chat with InterviewAgent
  // ------------------------------------------------------------------

  const sendChatMessage = useCallback(async (userText?: string) => {
    const text = userText ?? chatInput.trim();
    if (!text) return;

    const newUserMsg: ChatMessage = { role: 'user', content: text };
    const updatedMessages = [...chatMessages, newUserMsg];
    setChatMessages(updatedMessages);
    setChatInput('');
    setIsChatLoading(true);

    try {
      const resp = await agentAPI.chat('InterviewAgent', updatedMessages);
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: resp.content },
      ]);
    } catch (err) {
      const errMsg =
        err instanceof Error ? err.message : 'Failed to get response';
      setChatMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `I encountered an error: ${errMsg}. Please check that an API key is configured in Settings > Connections, then try again.`,
        },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  }, [chatInput, chatMessages]);

  const handleChatKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  // ------------------------------------------------------------------
  // Generate presentation
  // ------------------------------------------------------------------

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenerationError('');
    setGeneratedSlides([]);
    setPipelineState(null);
    setStep('generate');

    try {
      const styleGuide = selectedPreset
        ? `Use style preset: ${selectedPreset}`
        : 'Use a clean, modern professional style with dark text on light backgrounds.';

      const result = await agentAPI.generate(
        chatMessages,
        slideCount,
        styleGuide,
        null,
        'from_scratch',
      );

      setPresentationId(result.presentation_id);
      setGeneratedSlides(result.slides);
      setPipelineState(result.pipeline_state);
      setOutputFiles(result.output_files ?? []);
      setStep('results');
    } catch (err) {
      const errMsg =
        err instanceof Error ? err.message : 'Generation failed';
      setGenerationError(errMsg);
    } finally {
      setIsGenerating(false);
    }
  };

  // ------------------------------------------------------------------
  // Derive stage statuses for display
  // ------------------------------------------------------------------

  const getStageStatuses = (): Record<string, StageStatus> => {
    // If we have real pipeline state from the server, use it
    if (pipelineState) {
      const result: Record<string, StageStatus> = {};
      for (const stage of PIPELINE_STAGES) {
        const serverStatus = pipelineState.stages[stage.key]?.status;
        if (serverStatus === 'completed') result[stage.key] = 'completed';
        else if (serverStatus === 'running') result[stage.key] = 'running';
        else result[stage.key] = 'pending';
      }
      return result;
    }
    // Otherwise, use optimistic estimate
    return getOptimisticStageStatuses(elapsedSec);
  };

  const stageStatuses = getStageStatuses();

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-5xl">
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
                      {idx + 1}
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
      <div className="mx-auto max-w-5xl px-6 py-10">
        {/* ───────────────────────────────────────────── */}
        {/* Step 1: Interview Chat */}
        {/* ───────────────────────────────────────────── */}
        {step === 'interview' && (
          <div className="space-y-4">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">
                Tell me about your presentation
              </h2>
              <p className="text-slate-500 mt-1">
                Chat with our AI consultant. Describe your topic and answer a
                few questions so we can create the perfect presentation.
              </p>
            </div>

            {/* Chat area */}
            <div className="rounded-xl border border-slate-200 bg-white flex flex-col" style={{ height: '460px' }}>
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {chatMessages.length === 0 && (
                  <div className="text-center text-slate-400 py-16">
                    <Sparkles className="h-8 w-8 mx-auto mb-3 text-primary-400" />
                    <p className="text-sm">
                      Start by describing what your presentation is about.
                    </p>
                    <p className="text-xs mt-1">
                      The AI will ask follow-up questions to understand your
                      needs.
                    </p>
                  </div>
                )}

                {chatMessages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap ${
                        msg.role === 'user'
                          ? 'bg-primary-600 text-white'
                          : 'bg-slate-100 text-slate-800'
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}

                {isChatLoading && (
                  <div className="flex justify-start">
                    <div className="bg-slate-100 rounded-2xl px-4 py-2.5 text-sm text-slate-500">
                      <span className="inline-flex gap-1">
                        <span className="animate-bounce">.</span>
                        <span className="animate-bounce" style={{ animationDelay: '0.1s' }}>.</span>
                        <span className="animate-bounce" style={{ animationDelay: '0.2s' }}>.</span>
                      </span>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Input */}
              <div className="border-t border-slate-200 p-3">
                <div className="flex gap-2">
                  <textarea
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={handleChatKeyDown}
                    placeholder="Describe your presentation topic..."
                    className="flex-1 resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    rows={2}
                    disabled={isChatLoading}
                  />
                  <Button
                    onClick={() => sendChatMessage()}
                    disabled={!chatInput.trim() || isChatLoading}
                    size="sm"
                    className="self-end"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Slide count */}
            <div className="flex items-center gap-4">
              <Input
                label="Number of Slides"
                type="number"
                min={3}
                max={30}
                value={slideCount}
                onChange={(e) => setSlideCount(parseInt(e.target.value) || 10)}
                className="w-32"
              />
            </div>

            <div className="flex justify-between">
              <Button variant="ghost" onClick={() => router.push('/presentations')}>
                Cancel
              </Button>
              <Button
                disabled={chatMessages.length === 0}
                onClick={handleNext}
              >
                {briefReady ? 'Next: Style' : 'Next: Style (keep chatting for better results)'}
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {/* ───────────────────────────────────────────── */}
        {/* Step 2: Style */}
        {/* ───────────────────────────────────────────── */}
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
              <Button onClick={handleGenerate} isLoading={isGenerating}>
                <Sparkles className="h-4 w-4" />
                Generate Presentation
              </Button>
            </div>
          </div>
        )}

        {/* ───────────────────────────────────────────── */}
        {/* Step 3: Generation Progress */}
        {/* ───────────────────────────────────────────── */}
        {step === 'generate' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-slate-900">
                Generating your presentation
              </h2>
              <p className="text-slate-500 mt-1">
                The AI pipeline is working through 10 stages. This takes
                2&ndash;5 minutes &mdash; please keep this tab open.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-6">
              {isGenerating && (
                <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-100">
                  <Loader2 className="h-5 w-5 animate-spin text-primary-600 shrink-0" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-800">
                      Running AI pipeline&hellip;
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Elapsed: {Math.floor(elapsedSec / 60)}m {elapsedSec % 60}s
                    </p>
                  </div>
                </div>
              )}

              <ol className="space-y-3">
                {PIPELINE_STAGES.map((stage, idx) => {
                  const status = stageStatuses[stage.key] ?? 'pending';
                  return (
                    <li key={stage.key} className="flex items-center gap-3">
                      {status === 'completed' ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
                      ) : status === 'running' ? (
                        <Loader2 className="h-5 w-5 animate-spin text-primary-500 shrink-0" />
                      ) : (
                        <Circle className="h-5 w-5 text-slate-300 shrink-0" />
                      )}
                      <span
                        className={`text-sm ${
                          status === 'completed'
                            ? 'text-slate-500 line-through'
                            : status === 'running'
                              ? 'text-slate-900 font-semibold'
                              : 'text-slate-400'
                        }`}
                      >
                        {idx + 1}. {stage.label}
                      </span>
                      {status === 'running' && (
                        <span className="ml-auto text-xs text-primary-500 font-medium">
                          In progress
                        </span>
                      )}
                      {status === 'completed' && (
                        <span className="ml-auto text-xs text-green-500 font-medium">
                          Done
                        </span>
                      )}
                    </li>
                  );
                })}
              </ol>
            </div>

            {!isGenerating && generationError && (
              <div className="space-y-3">
                <div className="rounded-lg bg-red-50 border border-red-200 p-4">
                  <p className="text-sm font-semibold text-red-800 mb-1">
                    Generation failed
                  </p>
                  <p className="text-sm text-red-700">{generationError}</p>
                </div>
                <div className="flex gap-3">
                  <Button variant="secondary" onClick={handleBack}>
                    Back to Style
                  </Button>
                  <Button onClick={handleGenerate}>
                    Retry
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ───────────────────────────────────────────── */}
        {/* Step 4: Results */}
        {/* ───────────────────────────────────────────── */}
        {step === 'results' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">
                  Your Presentation
                </h2>
                <p className="text-slate-500 mt-1">
                  {generatedSlides.length} slides generated.
                  {presentationId && (
                    <span className="ml-2 text-xs text-slate-400">
                      ID: {presentationId}
                    </span>
                  )}
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={() => router.push('/presentations')}
              >
                Back to Dashboard
              </Button>
            </div>

            {/* Quality gates */}
            {pipelineState?.quality_gates && Object.keys(pipelineState.quality_gates).length > 0 && (
              <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 flex flex-wrap gap-x-6 gap-y-1">
                <p className="text-xs font-semibold text-green-700 w-full mb-1">Quality gates</p>
                {Object.entries(pipelineState.quality_gates).map(([gate, passed]) => (
                  <span key={gate} className="flex items-center gap-1 text-xs text-green-700">
                    {passed ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                    ) : (
                      <Circle className="h-3.5 w-3.5 text-slate-400" />
                    )}
                    {gate.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            )}

            {/* Download output files */}
            {outputFiles.length > 0 && presentationId && (
              <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
                <p className="text-xs font-semibold text-slate-600 mb-2">Output files</p>
                <div className="flex flex-wrap gap-2">
                  {outputFiles.map((filename) => (
                    <a
                      key={filename}
                      href={`${process.env.NEXT_PUBLIC_API_URL ?? ''}/api/v1/agents/workspace/${presentationId}/artifact/${filename}`}
                      download={filename}
                      className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
                    >
                      <Download className="h-3.5 w-3.5" />
                      {filename}
                    </a>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-12 gap-6">
              {/* Slide list */}
              <div className="col-span-4 space-y-2 max-h-[600px] overflow-y-auto pr-2">
                {generatedSlides.map((slide, idx) => (
                  <button
                    key={slide.index}
                    onClick={() => setActiveSlideIndex(idx)}
                    className={`w-full text-left rounded-lg border p-3 transition-colors ${
                      activeSlideIndex === idx
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <p className="text-xs text-slate-400 mb-1">
                      Slide {idx + 1}
                    </p>
                    <p className="text-sm font-medium text-slate-800 truncate">
                      {slide.title}
                    </p>
                  </button>
                ))}
              </div>

              {/* Slide preview */}
              <div className="col-span-8">
                {generatedSlides[activeSlideIndex] && (
                  <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
                    <div className="p-3 border-b border-slate-100 flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-slate-700">
                        {generatedSlides[activeSlideIndex].title}
                      </h3>
                      <span className="text-xs text-slate-400">
                        Slide {activeSlideIndex + 1} of{' '}
                        {generatedSlides.length}
                      </span>
                    </div>
                    <div
                      className="relative bg-slate-900"
                      style={{ paddingBottom: '56.25%' }}
                    >
                      <iframe
                        srcDoc={`<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  html,body{margin:0;padding:0;width:1920px;height:1080px;overflow:hidden}
  body{transform-origin:top left;transform:scale(var(--scale));background:#fff}
</style></head><body>
<script>
  var w=document.documentElement.clientWidth||1920;
  document.body.style.setProperty('--scale',w/1920);
</script>
${generatedSlides[activeSlideIndex].html}
</body></html>`}
                        className="absolute inset-0 w-full h-full border-0"
                        sandbox="allow-scripts"
                        title={`Slide ${activeSlideIndex + 1}`}
                      />
                    </div>
                    {generatedSlides[activeSlideIndex].speaker_notes && (
                      <div className="p-3 bg-slate-50 border-t border-slate-100">
                        <p className="text-xs font-semibold text-slate-500 mb-1">
                          Speaker Notes
                        </p>
                        <p className="text-xs text-slate-600 whitespace-pre-wrap">
                          {generatedSlides[activeSlideIndex].speaker_notes}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
