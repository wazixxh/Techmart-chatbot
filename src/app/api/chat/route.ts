import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const body = await req.json();

    // Use environment variable for production, fallback to localhost for local dev
    const apiUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:8000/api/chat';

    // Proxy the request to our Python FastAPI backend
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: body.messages,
      }),
    });

    if (!response.ok) {
      throw new Error(`Python API responded with status: ${response.status}`);
    }

    // Return the readable stream directly to the client (Vercel AI SDK format)
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
      },
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to the backend AI server.' },
      { status: 500 }
    );
  }
}
