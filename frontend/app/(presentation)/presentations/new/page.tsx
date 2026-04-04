'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDispatch, useSelector } from 'react-redux';
import { ChevronRight, ChevronLeft, Send, Sparkles } from 'lucide-react';
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

const STEPS: { key: WizardStep; label: string }[] = [
  { key: 'interview', label: 'Interview' },
  { key: 'style', label: 'Style' },
  { key: 'generate', label: 'Generate' },
  { key: 'results', label: 'Results' },
];

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
  const [generationStatus, setGenerationStatus] = useState('');
  const [generatedSlides, setGeneratedSlides] = useState<GeneratedSlide[]>([]);
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);

  useEffect(() => {
    dispatch(fetchPresets());
  }, [dispatch]);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isChatLoading]);

  // After 4+ user messages, allow generating a brief
  useEffect(() => {
    const userMsgCount = chatMessages.filter((m) => m.role === 'user').length;
    if (userMsgCount >= 3) {
      setBriefReady(true);
    }
  }, [chatMessages]);

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
  // Build brief from conversation
  // ------------------------------------------------------------------

  const buildBrief = (): string => {
    let brief = '';
    for (const msg of chatMessages) {
      if (msg.role === 'user') {
        brief += `User: ${msg.content}\n\n`;
      } else {
        brief += `Consultant: ${msg.content}\n\n`;
      }
    }
    return brief;
  };

  // ------------------------------------------------------------------
  // Generate presentation
  // ------------------------------------------------------------------

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenerationStatus('Generating slide content...');
    setGeneratedSlides([]);
    setStep('generate');

    try {
      const brief = buildBrief();
      const styleGuide = selectedPreset
        ? `Use style preset: ${selectedPreset}`
        : 'Use a clean, modern professional style with dark text on light backgrounds.';

      setGenerationStatus('Calling AI to write content and design slides...');
      const result = await agentAPI.generate(brief, styleGuide, slideCount);

      setGeneratedSlides(result.slides);
      setGenerationStatus(`Done! ${result.slide_count} slides generated.`);
      setStep('results');
    } catch (err) {
      const errMsg =
        err instanceof Error ? err.message : 'Generation failed';
      setGenerationStatus(`Error: ${errMsg}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-4xl">
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
      <div className="mx-auto max-w-4xl px-6 py-10">
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
                The AI pipeline is working. This can take 1-3 minutes depending
                on slide count.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-8">
              <div className="flex flex-col items-center gap-4">
                {isGenerating && (
                  <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
                )}
                <p className="text-sm font-medium text-slate-700">
                  {generationStatus}
                </p>
                {isGenerating && (
                  <div className="w-full max-w-md bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div className="bg-primary-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
                  </div>
                )}
              </div>
            </div>

            {!isGenerating && generationStatus.startsWith('Error') && (
              <div className="space-y-3">
                <div className="rounded-lg bg-red-50 border border-red-200 p-4">
                  <p className="text-sm font-medium text-red-800">
                    {generationStatus}
                  </p>
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
                  {generatedSlides.length} slides generated. Click a slide to
                  preview it.
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={() => router.push('/presentations')}
              >
                Back to Dashboard
              </Button>
            </div>

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
                        <p className="text-xs font-medium text-slate-500 mb-1">
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
