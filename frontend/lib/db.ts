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
  work_authorization?: string;
  max_years?: string;
}

const JOB_COLS = 'id, company, title, location, posted_date, url, is_active, summary, work_authorization, years_experience';

export function getJobById(id: number): Job | null {
  return (getDb().prepare(`SELECT ${JOB_COLS} FROM jobs WHERE id = ?`).get(id) as Job) ?? null;
}

export function getCompaniesCount(): number {
  const row = getDb().prepare("SELECT value FROM settings WHERE key = 'companies_monitored'").get() as { value: string } | undefined;
  if (row) return parseInt(row.value, 10);
  return (getDb().prepare('SELECT COUNT(DISTINCT company) as count FROM jobs').get() as { count: number }).count;
}

export function getJobs({ company, search, active, work_authorization, max_years }: GetJobsParams = {}): Job[] {
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

  if (work_authorization) {
    conditions.push('work_authorization = ?');
    params.push(work_authorization);
  }

  if (max_years) {
    const n = parseInt(max_years, 10);
    if (!isNaN(n)) {
      conditions.push('(years_experience IS NULL OR years_experience <= ?)');
      params.push(n);
    }
  }

  const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
  const sql = `SELECT ${JOB_COLS} FROM jobs ${where} ORDER BY posted_date DESC`;

  return getDb().prepare(sql).all(...params) as Job[];
}
