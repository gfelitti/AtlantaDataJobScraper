import { NextRequest, NextResponse } from 'next/server';
import { execFile } from 'child_process';
import { promisify } from 'util';
import { writeFile } from 'fs/promises';
import path from 'path';
import { randomUUID } from 'crypto';

const execFileAsync = promisify(execFile);

export async function POST(req: NextRequest) {
  const formData = await req.formData();
  const file = formData.get('resume') as File | null;

  if (!file) {
    return NextResponse.json({ error: 'No resume file provided' }, { status: 400 });
  }

  const ext = path.extname(file.name).toLowerCase();
  if (ext !== '.pdf' && ext !== '.docx') {
    return NextResponse.json({ error: 'Only .pdf and .docx files are supported' }, { status: 400 });
  }

  const tempPath = `/tmp/cv_${randomUUID()}${ext}`;
  const matchScriptPath = path.resolve(process.cwd(), '..', 'match_cv.py');
  const dbPath = process.env.DB_PATH ?? path.resolve(process.cwd(), '..', 'jobs.db');

  try {
    const bytes = await file.arrayBuffer();
    await writeFile(tempPath, Buffer.from(bytes));

    const { stdout } = await execFileAsync(
      'python3',
      [matchScriptPath, tempPath, '--db', dbPath, '--format', 'json'],
      { timeout: 120_000, env: process.env }
    );

    const results = JSON.parse(stdout);
    return NextResponse.json(results);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
