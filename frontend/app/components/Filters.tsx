'use client';

import { useEffect, useRef, useState } from 'react';

const AUTH_OPTIONS = [
  { value: '', label: 'All' },
  { value: 'sponsorship_provided', label: 'Sponsorship provided' },
  { value: 'opt_accepted', label: 'OPT accepted' },
  { value: 'not_specified', label: 'Not specified' },
  { value: 'citizen_gc_only', label: 'Citizen / GC only' },
];

interface Props {
  allCompanies: string[];
  selectedCompanies: string[];
  showActive: boolean;
  workAuthorization: string;
  maxYears: string;
  onSearchChange: (value: string) => void;
  onCompanyToggle: (company: string) => void;
  onActiveToggle: () => void;
  onWorkAuthChange: (value: string) => void;
  onMaxYearsChange: (value: string) => void;
}

export default function Filters({
  allCompanies,
  selectedCompanies,
  showActive,
  workAuthorization,
  maxYears,
  onSearchChange,
  onCompanyToggle,
  onActiveToggle,
  onWorkAuthChange,
  onMaxYearsChange,
}: Props) {
  const [inputValue, setInputValue] = useState('');
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => onSearchChange(inputValue), 200);
    return () => { if (timer.current) clearTimeout(timer.current); };
  }, [inputValue, onSearchChange]);

  return (
    <div className="flex flex-col gap-4 px-4 py-3 bg-white border-b border-gray-200 sm:flex-row sm:items-start">
      <input
        type="text"
        placeholder="Search title or location..."
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        className="w-full sm:w-64 px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
      />

      <div className="flex flex-col gap-1">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Companies</span>
        <div className="flex flex-wrap gap-x-4 gap-y-1 max-h-28 overflow-y-auto">
          {allCompanies.map((company) => (
            <label key={company} className="flex items-center gap-1.5 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={selectedCompanies.includes(company)}
                onChange={() => onCompanyToggle(company)}
                className="accent-blue-600"
              />
              {company}
            </label>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Work auth</span>
        <select
          value={workAuthorization}
          onChange={(e) => onWorkAuthChange(e.target.value)}
          className="px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {AUTH_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
          Max exp.{maxYears ? ` (≤ ${maxYears} yrs)` : ' (any)'}
        </span>
        <input
          type="range"
          min="0"
          max="10"
          step="1"
          value={maxYears || '10'}
          onChange={(e) => onMaxYearsChange(e.target.value === '10' ? '' : e.target.value)}
          className="w-32 accent-blue-600"
        />
      </div>

      <label className="flex items-center gap-2 text-sm cursor-pointer whitespace-nowrap">
        <input
          type="checkbox"
          checked={showActive}
          onChange={onActiveToggle}
          className="accent-blue-600"
        />
        Active only
      </label>
    </div>
  );
}
