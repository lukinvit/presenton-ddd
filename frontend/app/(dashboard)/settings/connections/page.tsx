'use client';

import { useEffect, useRef, useState } from 'react';
import { CheckCircle, Plug, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Dialog, DialogFooter } from '@/components/ui/Dialog';
import { Input } from '@/components/ui/Input';
import { connectionAPI } from '@/lib/api';

interface Connection {
  provider: string;
  label: string;
  description: string;
  icon: string;
  apiKeyPlaceholder: string;
  connected: boolean;
}

const PROVIDERS: Omit<Connection, 'connected'>[] = [
  {
    provider: 'anthropic',
    label: 'Anthropic (Claude)',
    description: 'Connect your Anthropic API key to use Claude models',
    icon: 'A',
    apiKeyPlaceholder: 'sk-ant-...',
  },
  {
    provider: 'openai',
    label: 'OpenAI (GPT)',
    description: 'Connect your OpenAI API key to use GPT models',
    icon: 'O',
    apiKeyPlaceholder: 'sk-...',
  },
];

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<Connection[]>(
    PROVIDERS.map((p) => ({ ...p, connected: false })),
  );
  const [isLoading, setIsLoading] = useState(true);

  // Dialog state
  const [dialogProvider, setDialogProvider] = useState<string | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Disconnect state
  const [disconnecting, setDisconnecting] = useState<string | null>(null);

  useEffect(() => {
    connectionAPI
      .list()
      .then((data) => {
        setConnections((prev) =>
          prev.map((c) => ({
            ...c,
            connected: data.some((d) => d.provider === c.provider && d.connected),
          })),
        );
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  const openDialog = (provider: string) => {
    setDialogProvider(provider);
    setApiKeyInput('');
    setSubmitError(null);
    // Focus input after render
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const closeDialog = () => {
    if (isSubmitting) return;
    setDialogProvider(null);
    setApiKeyInput('');
    setSubmitError(null);
  };

  const handleSubmitApiKey = async () => {
    if (!dialogProvider || !apiKeyInput.trim()) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await connectionAPI.connect(dialogProvider, apiKeyInput.trim());
      setConnections((prev) =>
        prev.map((c) =>
          c.provider === dialogProvider ? { ...c, connected: true } : c,
        ),
      );
      closeDialog();
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to save API key');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDisconnect = async (provider: string) => {
    setDisconnecting(provider);
    try {
      await connectionAPI.disconnect(provider);
      setConnections((prev) =>
        prev.map((c) =>
          c.provider === provider ? { ...c, connected: false } : c,
        ),
      );
    } catch {
      // ignore
    } finally {
      setDisconnecting(null);
    }
  };

  const dialogConn = PROVIDERS.find((p) => p.provider === dialogProvider);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Connections</h1>
        <p className="text-sm text-slate-500 mt-1">
          Connect AI providers to power your presentation generation pipeline
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 max-w-2xl">
        {connections.map((conn) => (
          <Card key={conn.provider}>
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className="h-12 w-12 rounded-xl bg-slate-900 flex items-center justify-center shrink-0">
                  <span className="text-white font-bold text-lg">
                    {conn.icon}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-slate-900">
                      {conn.label}
                    </h3>
                    {conn.connected ? (
                      <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
                        <CheckCircle className="h-3.5 w-3.5" />
                        Connected
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-slate-400 font-medium">
                        <XCircle className="h-3.5 w-3.5" />
                        Not connected
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-500">{conn.description}</p>
                </div>
                <div className="shrink-0 flex gap-2">
                  {conn.connected ? (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openDialog(conn.provider)}
                      >
                        Update key
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        isLoading={disconnecting === conn.provider}
                        onClick={() => handleDisconnect(conn.provider)}
                      >
                        Disconnect
                      </Button>
                    </>
                  ) : (
                    <Button
                      size="sm"
                      onClick={() => openDialog(conn.provider)}
                    >
                      Connect
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {!isLoading && connections.every((c) => !c.connected) && (
        <div className="mt-6 rounded-lg bg-yellow-50 border border-yellow-200 p-4 max-w-2xl">
          <div className="flex items-start gap-3">
            <Plug className="h-5 w-5 text-yellow-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-800">
                No connections configured
              </p>
              <p className="text-sm text-yellow-700 mt-1">
                At least one AI provider must be connected to generate
                presentations.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* API Key Dialog */}
      <Dialog
        open={dialogProvider !== null}
        onClose={closeDialog}
        title={`Connect ${dialogConn?.label ?? ''}`}
        description="Enter your API key. It will be stored encrypted on the server."
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              API Key
            </label>
            <Input
              ref={inputRef}
              type="password"
              placeholder={dialogConn?.apiKeyPlaceholder ?? 'sk-...'}
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSubmitApiKey();
              }}
              disabled={isSubmitting}
            />
          </div>
          {submitError && (
            <p className="text-sm text-red-600">{submitError}</p>
          )}
          <DialogFooter>
            <Button variant="outline" size="sm" onClick={closeDialog} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button
              size="sm"
              isLoading={isSubmitting}
              disabled={!apiKeyInput.trim()}
              onClick={handleSubmitApiKey}
            >
              Save
            </Button>
          </DialogFooter>
        </div>
      </Dialog>
    </div>
  );
}
