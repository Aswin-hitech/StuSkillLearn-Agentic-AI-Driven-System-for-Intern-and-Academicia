export type UserRole = 'STUDENT' | 'COMPANY' | 'ACADEMICIAN' | 'INSTITUTION' | 'ADMIN';

export type User = {
  public_id: string;
  email: string;
  role: UserRole;
  email_verified?: boolean;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  expires_in?: number;
  user: User;
};

export type StudentProfile = {
  id: number;
  name: string;
  college: string;
  university: string;
  degree: string;
  department: string;
  current_year: number;
  cgpa: number;
  city: string;
  state: string;
  reservation_category: string;
  skills: string[];
  projects: Array<Record<string, unknown>>;
  certifications: Array<Record<string, unknown>>;
  preferences: Record<string, unknown>;
  general_pool_opt_in: boolean;
  profile_completion: number;
};

export type Match = {
  id: number;
  opportunity_id: number;
  skill_score: number;
  required_coverage: number;
  communication_score: number;
  project_score: number;
  academic_score: number;
  location_score: number;
  preference_score: number;
  portfolio_score: number;
  total_score: number;
  explanation: {
    eligible?: boolean;
    tier?: 'TIER_1' | 'TIER_2' | 'TIER_3' | 'TIER_4' | 'NOT_ELIGIBLE';
    tier_definition?: Record<string, string>;
    matched_required?: string[];
    missing_required?: string[];
    matched_preferred?: string[];
    preference_rank?: number | null;
    summary?: string;
    tie_break_order?: string[];
  };
};

export type Opportunity = {
  id: number;
  company_id: number;
  company_name: string;
  opportunity_type: string;
  title: string;
  domain: string;
  description: string;
  required_skills: string[];
  preferred_skills: string[];
  seats: number;
  stipend: number;
  location: string;
  work_mode: string;
  min_cgpa: number;
  status: string;
  moderation_status?: string;
  reservation_policy_approved?: boolean;
  duration: string;
  deadline: string;
  reservation_policy: Record<string, number>;
  match?: Match | null;
  applied?: boolean;
};

export type LSRW = {
  id: number;
  listening: number;
  speaking: number;
  reading: number;
  writing: number;
  overall: number;
  details: Record<string, unknown>;
};

export type LearningRecommendation = {
  id: number;
  skill: string;
  reason: string;
  action: string;
  resource_url: string;
  priority: string;
  completed: boolean;
};

export type Allocation = {
  id: number;
  opportunity_id: number;
  student_id: number;
  student_name: string;
  title: string;
  company_name: string;
  rank: number;
  round: number;
  status: string;
  category_slot: string;
  explanation: Record<string, unknown>;
};

export type StudentDashboard = {
  profile: StudentProfile;
  readiness: number;
  communication: LSRW | null;
  top_matches: Array<Match & { opportunity?: Opportunity }>;
  learning: LearningRecommendation[];
  applications: Array<Record<string, unknown>>;
  offers: Allocation[];
  badges: Array<Record<string, unknown>>;
};
