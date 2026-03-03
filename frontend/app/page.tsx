import { getJobs } from '@/lib/db';
import JobsView from './components/JobsView';

export default function Home() {
  const initialJobs = getJobs({ active: '1' });
  return <JobsView initialJobs={initialJobs} />;
}
