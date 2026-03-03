'use client';

import { useEffect, useRef, useState } from 'react';

interface Props {
  allCompanies: string[];
  selectedCompanies: string[];
  showActive: boolean;
  onSearchChange: (value: string) => void;
  onCompanyToggle: (company: string) => void;
  onActiveToggle: () => void;
}

export default function Filters({
  allCompanies,
  selectedCompanies,
  showActive,
  onSearchChange,
  onCompanyToggle,
  onActiveToggle,
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
