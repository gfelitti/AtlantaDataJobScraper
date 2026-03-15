import { NextRequest, NextResponse } from 'next/server';
import { getJobs } from '@/lib/db';

export const dynamic = 'force-dynamic';

export function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const company = searchParams.get('company') ?? undefined;
  const search = searchParams.get('search') ?? undefined;
  const active = searchParams.get('active') ?? undefined;
  const work_authorization = searchParams.get('work_authorization') ?? undefined;
  const max_years = searchParams.get('max_years') ?? undefined;

  const jobs = getJobs({ company, search, active, work_authorization, max_years });
  return NextResponse.json(jobs);
}
