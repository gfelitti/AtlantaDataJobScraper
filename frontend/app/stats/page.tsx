import Database from 'better-sqlite3';
import path from 'path';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

function getDb() {
  const dbPath = process.env.DB_PATH ?? path.resolve(process.cwd(), '..', 'jobs.db');
  return new Database(dbPath, { readonly: true });
}

export default function StatsPage() {
  const db = getDb();

  const totalActive = (db.prepare('SELECT COUNT(*) as n FROM jobs WHERE is_active=1').get() as { n: number }).n;
  const totalAll = (db.prepare('SELECT COUNT(*) as n FROM jobs').get() as { n: number }).n;
  const totalInactive = totalAll - totalActive;
  const totalCompanies = (db.prepare('SELECT COUNT(DISTINCT company) as n FROM jobs WHERE is_active=1').get() as { n: number }).n;

  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  const newThisWeek = (db.prepare(
    "SELECT COUNT(*) as n FROM jobs WHERE is_active=1 AND posted_date >= ?"
  ).get(sevenDaysAgo) as { n: number }).n;

  const byCompany = db.prepare(
    'SELECT company, COUNT(*) as n FROM jobs WHERE is_active=1 GROUP BY company ORDER BY n DESC'
  ).all() as { company: string; n: number }[];

  const maxCompanyCount = byCompany[0]?.n ?? 1;

  // Jobs by posted_date — last 30 days
  const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  const byDate = db.prepare(
    `SELECT posted_date as date, COUNT(*) as n
     FROM jobs WHERE is_active=1 AND posted_date >= ?
     GROUP BY posted_date ORDER BY posted_date ASC`
  ).all(thirtyDaysAgo) as { date: string; n: number }[];

  const maxDateCount = Math.max(...byDate.map(r => r.n), 1);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="px-4 py-3 bg-gray-900 text-white flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Job Scraper</h1>
          <p className="text-xs text-gray-400">Scraper stats</p>
        </div>
        <Link href="/" className="text-sm text-blue-400 hover:text-blue-300">← Jobs</Link>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-8">

        {/* Summary cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Active jobs', value: totalActive },
            { label: 'Companies', value: totalCompanies },
            { label: 'New this week', value: newThisWeek },
            { label: 'Deactivated', value: totalInactive },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white rounded-lg border border-gray-200 p-4 text-center">
              <p className="text-3xl font-bold text-gray-900">{value}</p>
              <p className="text-xs text-gray-500 mt-1">{label}</p>
            </div>
          ))}
        </div>

        {/* Jobs by company */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Active jobs by company</h2>
          <div className="space-y-2">
            {byCompany.map(({ company, n }) => (
              <div key={company} className="flex items-center gap-3">
                <span className="w-40 text-xs text-gray-600 truncate text-right shrink-0">{company}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div
                    className="bg-blue-500 h-4 rounded-full"
                    style={{ width: `${(n / maxCompanyCount) * 100}%` }}
                  />
                </div>
                <span className="w-6 text-xs text-gray-500 text-right shrink-0">{n}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Jobs by posted date */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Jobs by posted date (last 30 days)</h2>
          {byDate.length === 0 ? (
            <p className="text-sm text-gray-400">No data</p>
          ) : (
            <div className="flex items-end gap-1 h-32">
              {byDate.map(({ date, n }) => (
                <div key={date} className="flex-1 h-full flex flex-col justify-end group relative">
                  <div
                    className="w-full bg-blue-500 rounded-t"
                    style={{ height: `${(n / maxDateCount) * 100}%` }}
                  />
                  {/* Tooltip */}
                  <div className="absolute bottom-full mb-1 hidden group-hover:block bg-gray-800 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
                    {date}: {n} job{n !== 1 ? 's' : ''}
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="flex justify-between mt-2 text-xs text-gray-400">
            <span>{byDate[0]?.date ?? ''}</span>
            <span>{byDate[byDate.length - 1]?.date ?? ''}</span>
          </div>
        </div>

      </main>
    </div>
  );
}
