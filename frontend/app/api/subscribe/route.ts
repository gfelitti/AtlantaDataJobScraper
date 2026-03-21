import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { email } = await req.json();

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ error: 'Invalid email.' }, { status: 400 });
  }

  const apiKey = process.env.RESEND_API_KEY;
  const audienceId = process.env.RESEND_AUDIENCE_ID;

  if (!apiKey || !audienceId) {
    return NextResponse.json({ error: 'Server misconfigured.' }, { status: 500 });
  }

  const res = await fetch(`https://api.resend.com/audiences/${audienceId}/contacts`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    return NextResponse.json({ error: body.message || 'Failed to subscribe.' }, { status: 500 });
  }

  return NextResponse.json({ ok: true });
}
