'use client';

import { useState } from 'react';
import Link from 'next/link';

interface MatchResult {
  rank: number;
  score: number;
  reason: string;
  title: string;
  company: string;
  url: string;
}

export default function MatchPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<MatchResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    setResults(null);

    const formData = new FormData();
    formData.append('resume', file);

    try {
      const res = await fetch('/api/match', { method: 'POST', body: formData });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? 'Unknown error');
      } else {
        setResults(data);
      }
    } catch {
      setError('Request failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="px-4 py-3 bg-gray-900 text-white flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Match CV</h1>
          <p className="text-xs text-gray-400">Rank active jobs against your resume</p>
        </div>
        <Link href="/" className="text-sm text-blue-400 hover:text-blue-300">
          ← Back
        </Link>
      </header>

      <main className="flex-1 p-6 max-w-2xl mx-auto w-full">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 mb-8">
          <label className="text-sm font-medium text-gray-700">
            Resume (.pdf or .docx)
          </label>
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          <button
            type="submit"
            disabled={!file || loading}
            className="self-start px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
          {loading && (
            <p className="text-xs text-gray-500">This takes 30–90 seconds.</p>
          )}
        </form>

        {error && (
          <p className="text-sm text-red-600 mb-6">{error}</p>
        )}

        {results && results.length === 0 && (
          <p className="text-sm text-gray-500">No jobs scored 6 or above for this resume.</p>
        )}

        {results && results.length > 0 && (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-gray-500">{results.length} jobs matched</p>
            {results.map((r) => (
              <div key={r.rank} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div>
                    <span className="text-xs font-medium text-gray-400 mr-2">#{r.rank}</span>
                    <span className="font-semibold text-gray-900">{r.title}</span>
                    <span className="text-gray-500 text-sm ml-1">@ {r.company}</span>
                  </div>
                  <span className="shrink-0 text-xs font-bold bg-blue-100 text-blue-700 px-2 py-1 rounded">
                    {r.score}/10
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1 mb-3">{r.reason}</p>
                <a
                  href={r.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:underline"
                >
                  Apply →
                </a>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
