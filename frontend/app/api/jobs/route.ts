import { NextRequest, NextResponse } from 'next/server';
import { getJobs } from '@/lib/db';

export const dynamic = 'force-dynamic';

export function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const company = searchParams.get('company') ?? undefined;
  const search = searchParams.get('search') ?? undefined;
  const active = searchParams.get('active') ?? undefined;

  const jobs = getJobs({ company, search, active });
  return NextResponse.json(jobs);
}
