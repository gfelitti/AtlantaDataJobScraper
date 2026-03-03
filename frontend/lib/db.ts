import Database from 'better-sqlite3';
import path from 'path';
import type { Job } from '@/types/job';

let db: Database.Database | null = null;

function getDb(): Database.Database {
  if (!db) {
    const dbPath = process.env.DB_PATH ?? path.resolve(process.cwd(), '..', 'jobs.db');
    db = new Database(dbPath, { readonly: true });
  }
  return db;
}

interface GetJobsParams {
  company?: string;
  search?: string;
  active?: string;
}

export function getJobById(id: number): Job | null {
  return (getDb().prepare('SELECT id, company, title, location, posted_date, url, is_active, summary FROM jobs WHERE id = ?').get(id) as Job) ?? null;
}

export function getJobs({ company, search, active }: GetJobsParams = {}): Job[] {
  const conditions: string[] = [];
  const params: (string | number)[] = [];

  if (company) {
    conditions.push('company = ?');
    params.push(company);
  }

  if (search) {
    conditions.push('(title LIKE ? OR location LIKE ?)');
    params.push(`%${search}%`, `%${search}%`);
  }

  if (active !== undefined) {
    conditions.push('is_active = ?');
    params.push(active === '1' ? 1 : 0);
  }

  const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
  const sql = `SELECT id, company, title, location, posted_date, url, is_active, summary FROM jobs ${where} ORDER BY posted_date DESC`;

  return getDb().prepare(sql).all(...params) as Job[];
}
