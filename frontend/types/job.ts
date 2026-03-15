export interface Job {
  id: number;
  company: string;
  title: string;
  location: string | null;
  posted_date: string | null;
  url: string;
  is_active: number;
  summary: string | null;
  work_authorization: string | null;
  years_experience: number | null;
}
