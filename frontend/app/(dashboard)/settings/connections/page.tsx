'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, ExternalLink, Plug, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { connectionAPI } from '@/lib/api';

interface Connection {
  provider: string;
  label: string;
  description: string;
  icon: string;
  connected: boolean;
  expires_at?: string;
}

const PROVIDERS: Omit<Connection, 'connected'>[] = [
  {
    provider: 'anthropic',
    label: 'Anthropic (Claude)',
    description: 'Connect your Anthropic API key to use Claude models',
    icon: 'A',
  },
  {
    provider: 'openai',
    label: 'OpenAI (GPT)',
    description: 'Connect your OpenAI API key to use GPT models',
    icon: 'O',
  },
];

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<Connection[]>(
    PROVIDERS.map((p) => ({ ...p, connected: false })),
  );
  const [isLoading, setIsLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);

  useEffect(() => {
    connectionAPI
      .list()
      .then((data) => {
        const connected = data as Array<{ provider: string }>;
        setConnections((prev) =>
          prev.map((c) => ({
            ...c,
            connected: connected.some((d) => d.provider === c.provider),
          })),
        );
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  const handleConnect = async (provider: string) => {
    setConnecting(provider);
    try {
      const { auth_url } = await connectionAPI.connect(provider);
      window.location.href = auth_url;
    } catch {
      setConnecting(null);
    }
  };

  const handleDisconnect = async (provider: string) => {
    try {
      await connectionAPI.disconnect(provider);
      setConnections((prev) =>
        prev.map((c) =>
          c.provider === provider ? { ...c, connected: false } : c,
        ),
      );
    } catch {}
  };

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
                <div className="shrink-0">
                  {conn.connected ? (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDisconnect(conn.provider)}
                    >
                      Disconnect
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      isLoading={connecting === conn.provider}
                      onClick={() => handleConnect(conn.provider)}
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
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
    </div>
  );
}
