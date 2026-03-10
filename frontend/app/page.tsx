import { getCompaniesCount, getJobs } from '@/lib/db';
import JobsView from './components/JobsView';

export const dynamic = 'force-dynamic';

export default function Home() {
  const initialJobs = getJobs({ active: '1' });
  const companiesCount = getCompaniesCount();
  return <JobsView initialJobs={initialJobs} companiesCount={companiesCount} />;
}
