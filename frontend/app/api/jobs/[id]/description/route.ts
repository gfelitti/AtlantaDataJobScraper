import { NextRequest, NextResponse } from 'next/server';
import { getJobById } from '@/lib/db';

export const dynamic = 'force-dynamic';

const HEADERS = {
  'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  Accept: 'text/html,application/xhtml+xml',
};

interface JobDetail {
  addressLocality: string | null;
  datePosted: string | null;
  reqId: string | null;
}

function extractJsonLd(html: string): JobDetail {
  const match = html.match(/<script[^>]+application\/ld\+json[^>]*>([\s\S]*?)<\/script>/);
  if (!match) return { addressLocality: null, datePosted: null, reqId: null };

  try {
    const data = JSON.parse(match[1]);
    return {
      addressLocality: data?.jobLocation?.address?.addressLocality ?? null,
      datePosted: data?.datePosted ?? null,
      reqId: data?.identifier?.value ?? null,
    };
  } catch {
    return { addressLocality: null, datePosted: null, reqId: null };
  }
}

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const job = getJobById(parseInt(id));
  if (!job) return NextResponse.json({ error: 'Not found' }, { status: 404 });

  try {
    const resp = await fetch(job.url, { headers: HEADERS });
    if (!resp.ok) return NextResponse.json({ detail: null });
    const html = await resp.text();
    const detail = extractJsonLd(html);
    return NextResponse.json({ detail });
  } catch {
    return NextResponse.json({ detail: null });
  }
}
