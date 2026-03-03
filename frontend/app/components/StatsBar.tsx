import type { Job } from '@/types/job';

interface Props {
  jobs: Job[];
}

export default function StatsBar({ jobs }: Props) {
  const counts = jobs.reduce<Record<string, number>>((acc, job) => {
    acc[job.company] = (acc[job.company] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="flex flex-wrap gap-2 px-4 py-3 bg-white border-b border-gray-200">
      <span className="text-sm text-gray-500 font-medium self-center">
        {jobs.length} jobs
      </span>
      {Object.entries(counts)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([company, count]) => (
          <span
            key={company}
            className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-800"
          >
            {company}: {count}
          </span>
        ))}
    </div>
  );
}
