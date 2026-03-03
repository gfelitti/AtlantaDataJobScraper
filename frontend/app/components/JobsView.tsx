'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Job } from '@/types/job';
import StatsBar from './StatsBar';
import Filters from './Filters';
import JobTable from './JobTable';

interface Props {
  initialJobs: Job[];
}

export default function JobsView({ initialJobs }: Props) {
  const [jobs, setJobs] = useState<Job[]>(initialJobs);
  const [search, setSearch] = useState('');
  const [selectedCompanies, setSelectedCompanies] = useState<string[]>([]);
  const [showActive, setShowActive] = useState(true);

  // Derived from initialJobs — stable, never shrinks as filters change
  const allCompanies = useMemo(
    () => [...new Set(initialJobs.map((j) => j.company))].sort(),
    [initialJobs]
  );

  const isFirstRender = useRef(true);

  useEffect(() => {
    // Skip the first render — we already have initialJobs from SSR
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (selectedCompanies.length === 1) params.set('company', selectedCompanies[0]);
    if (showActive) params.set('active', '1');

    fetch(`/api/jobs?${params.toString()}`)
      .then((r) => r.json())
      .then((data: Job[]) => {
        if (selectedCompanies.length > 1) {
          setJobs(data.filter((j) => selectedCompanies.includes(j.company)));
        } else {
          setJobs(data);
        }
      });
  }, [search, selectedCompanies, showActive]);

  const handleCompanyToggle = useCallback((company: string) => {
    setSelectedCompanies((prev) =>
      prev.includes(company) ? prev.filter((c) => c !== company) : [...prev, company]
    );
  }, []);

  const handleSearchChange = useCallback((value: string) => {
    setSearch(value);
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <header className="px-4 py-3 bg-gray-900 text-white">
        <h1 className="text-lg font-semibold">Job Scraper</h1>
        <p className="text-xs text-gray-400">Data-role postings — 7 Atlanta companies</p>
      </header>

      <StatsBar jobs={jobs} />

      <Filters
        allCompanies={allCompanies}
        selectedCompanies={selectedCompanies}
        showActive={showActive}
        onSearchChange={handleSearchChange}
        onCompanyToggle={handleCompanyToggle}
        onActiveToggle={() => setShowActive((prev) => !prev)}
      />

      <main className="flex-1 overflow-auto">
        <JobTable jobs={jobs} />
      </main>
    </div>
  );
}
