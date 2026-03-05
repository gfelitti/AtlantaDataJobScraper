'use client';

import { useState } from 'react';
import type { Job } from '@/types/job';

type SortKey = 'company' | 'title' | 'posted_date';

interface Props {
  jobs: Job[];
}

interface JobSummary {
  experience: string | null;
  salary: string | null;
  responsibilities: string[];
  benefits: string[];
  arrangement: string | null;
}

function DetailPanel({ job }: { job: Job }) {
  const s: JobSummary | null = (() => {
    try {
      return job.summary ? JSON.parse(job.summary) : null;
    } catch {
      return null;
    }
  })();

  const metaRows: [string, string | null][] = [
    ['Company', job.company],
    ['Location', job.location],
    ['Posted', job.posted_date],
    ['Experience', s?.experience ?? null],
    ['Salary', s?.salary ?? null],
    ['Arrangement', s?.arrangement ?? null],
  ];

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:gap-8">
      <div className="flex flex-col gap-3 flex-1 text-sm">
        <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1">
          {metaRows.map(([label, value]) => {
            if (value === null) return null;
            return (
              <>
                <dt key={`${label}-dt`} className="text-gray-500 font-medium whitespace-nowrap">
                  {label}
                </dt>
                <dd key={`${label}-dd`} className="text-gray-800">{value}</dd>
              </>
            );
          })}
        </dl>
        {s && s.responsibilities.length > 0 && (
          <div>
            <p className="text-gray-500 font-medium mb-1">Responsibilities</p>
            <ul className="list-disc list-inside space-y-0.5 text-gray-800">
              {s.responsibilities.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}
        {s && s.benefits.length > 0 && (
          <div>
            <p className="text-gray-500 font-medium mb-1">Benefits</p>
            <ul className="list-disc list-inside space-y-0.5 text-gray-800">
              {s.benefits.map((b, i) => <li key={i}>{b}</li>)}
            </ul>
          </div>
        )}
      </div>
      <div className="flex flex-col gap-2 sm:ml-auto">
        <a
          href={job.url}
          target="_blank"
          rel="noopener noreferrer"
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 text-center"
        >
          Open full posting →
        </a>
        <p className="text-xs text-gray-400 text-center">Opens on company site</p>
      </div>
    </div>
  );
}

export default function JobTable({ jobs }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('posted_date');
  const [sortAsc, setSortAsc] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc((prev) => !prev);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  }

  const sorted = [...jobs].sort((a, b) => {
    const av = a[sortKey] ?? '';
    const bv = b[sortKey] ?? '';
    const cmp = av.localeCompare(bv);
    return sortAsc ? cmp : -cmp;
  });

  function SortIndicator({ col }: { col: SortKey }) {
    if (sortKey !== col) return <span className="text-gray-300"> ↕</span>;
    return <span>{sortAsc ? ' ↑' : ' ↓'}</span>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th
              className="px-4 py-2 text-left font-medium text-gray-600 cursor-pointer select-none whitespace-nowrap"
              onClick={() => handleSort('company')}
            >
              Company <SortIndicator col="company" />
            </th>
            <th
              className="px-4 py-2 text-left font-medium text-gray-600 cursor-pointer select-none"
              onClick={() => handleSort('title')}
            >
              Title <SortIndicator col="title" />
            </th>
            <th className="px-4 py-2 text-left font-medium text-gray-600">Location</th>
            <th
              className="px-4 py-2 text-left font-medium text-gray-600 whitespace-nowrap cursor-pointer select-none"
              onClick={() => handleSort('posted_date')}
            >
              Posted <SortIndicator col="posted_date" />
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {sorted.length === 0 ? (
            <tr>
              <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                No jobs match your filters.
              </td>
            </tr>
          ) : (
            sorted.map((job) => {
              const isNew = job.posted_date === new Date().toISOString().slice(0, 10);
              return (
              <>
                <tr
                  key={job.id}
                  onClick={() => setExpandedId(expandedId === job.id ? null : job.id)}
                  className={`cursor-pointer ${isNew ? 'bg-green-50 hover:bg-green-100' : 'hover:bg-blue-50'}`}
                >
                  <td className="px-4 py-2 font-medium whitespace-nowrap">{job.company}</td>
                  <td className="px-4 py-2">
                    <span className="flex items-center gap-1">
                      <span className="text-gray-400 text-xs">{expandedId === job.id ? '▼' : '▶'}</span>
                      {job.title}
                      {job.summary && (
                        <span title="AI summary available" className="text-base leading-none">🤖</span>
                      )}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-500 whitespace-nowrap">{job.location ?? '—'}</td>
                  <td className="px-4 py-2 text-gray-500 whitespace-nowrap">{job.posted_date ?? '—'}</td>
                </tr>
                {expandedId === job.id && (
                  <tr key={`${job.id}-detail`}>
                    <td colSpan={4} className="px-6 py-4 bg-blue-50 border-b border-blue-100">
                      <DetailPanel job={job} />
                    </td>
                  </tr>
                )}
              </>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
