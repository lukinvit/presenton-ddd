import { NextRequest, NextResponse } from 'next/server';

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:8000';

async function proxyRequest(req: NextRequest): Promise<NextResponse> {
  const url = new URL(req.url);
  // Strip /api prefix since it's handled by next.config.mjs rewrites
  const targetUrl = `${GATEWAY_URL}${url.pathname}${url.search}`;

  const headers = new Headers(req.headers);
  // Remove Next.js-specific headers
  headers.delete('host');

  try {
    const response = await fetch(targetUrl, {
      method: req.method,
      headers,
      body:
        req.method !== 'GET' && req.method !== 'HEAD'
          ? req.body
          : undefined,
      // @ts-expect-error - duplex is required for streaming
      duplex: 'half',
    });

    const responseHeaders = new Headers(response.headers);
    // Remove encoding headers that Next.js handles
    responseHeaders.delete('content-encoding');
    responseHeaders.delete('transfer-encoding');

    return new NextResponse(response.body, {
      status: response.status,
      headers: responseHeaders,
    });
  } catch (err) {
    console.error('[proxy] Error:', err);
    return NextResponse.json(
      { error: 'Gateway unavailable' },
      { status: 502 },
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const PATCH = proxyRequest;
export const DELETE = proxyRequest;
export const OPTIONS = proxyRequest;
