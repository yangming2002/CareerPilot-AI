import client from './client'

// ---------- Auth ----------
export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: number
  username: string
  email: string
}

export interface UserResponse {
  id: number
  email: string
  username: string
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return client.post('/api/v1/auth/login', { email, password }).then((r) => r.data)
}

export function register(email: string, username: string, password: string): Promise<TokenResponse> {
  return client.post('/api/v1/auth/register', { email, username, password }).then((r) => r.data)
}

export function getMe(): Promise<UserResponse> {
  return client.get('/api/v1/auth/me').then((r) => r.data)
}

// ---------- Analysis ----------
export interface JDMatchRequest {
  resume_text: string
  jd_text: string
  company?: string
  position?: string
}

export interface JDMatchResponse {
  id: number | null
  match_score: number
  skill_gaps: SkillGap[]
  keyword_coverage: KeywordCoverage[]
  suggestions: SuggestionItem[]
  integrity_checks: IntegrityCheckItem[]
  jd_summary: string
  resume_summary: string
  degraded: boolean
  degraded_reason: string
  progress_log: string[]
  revised_resume: string
  session_id: string
  nlp_score: number
  tfidf_score: number
  keyword_score: number
}

export interface ProgressData {
  steps: string[]
  done: boolean
}

export function getProgress(sessionId: string): Promise<ProgressData> {
  return client.get(`/api/v1/analysis/progress/${sessionId}`).then((r) => r.data)
}

export interface SkillGap {
  skill: string
  required: boolean
  user_has: boolean
  note: string
}

export interface KeywordCoverage {
  keyword: string
  in_resume: boolean
  in_jd: boolean
}

export interface SuggestionItem {
  category: string
  original: string
  suggestion: string
  confidence: string
}

export interface IntegrityCheckItem {
  severity: string
  category: string
  description: string
  detail: string
}

export function runJDMatch(
  data: JDMatchRequest,
  options: { signal?: AbortSignal } = {},
): Promise<JDMatchResponse> {
  return client.post('/api/v1/analysis/jd-match', data, {
    signal: options.signal,
    timeout: 90000,
  }).then((r) => r.data)
}

// ---------- Applications ----------
export interface ApplicationRecord {
  id: number
  company: string
  position: string
  channel: string | null
  application_date: string | null
  resume_version: string | null
  status: string
  notes: string | null
  created_at: string
  updated_at: string | null
  status_history: StatusHistoryItem[]
}

export interface StatusHistoryItem {
  id: number
  old_status: string | null
  new_status: string
  changed_at: string
}

export interface ApplicationCreate {
  company: string
  position: string
  channel?: string
  application_date?: string
  resume_version?: string
  status?: string
  notes?: string
}

export interface CooldownInfo {
  company: string
  has_active_application: boolean
  last_application_date: string | null
  last_status: string | null
  in_cooldown: boolean
  cooldown_message: string
}

export function createApplication(data: ApplicationCreate): Promise<ApplicationRecord> {
  return client.post('/api/v1/applications', data).then((r) => r.data)
}

export function listApplications(): Promise<ApplicationRecord[]> {
  return client.get('/api/v1/applications').then((r) => r.data)
}

export function updateApplicationStatus(appId: number, status: string): Promise<ApplicationRecord> {
  return client.patch(`/api/v1/applications/${appId}/status`, { status }).then((r) => r.data)
}

export function deleteApplication(appId: number): Promise<void> {
  return client.delete(`/api/v1/applications/${appId}`)
}

export function checkCooldown(appId: number): Promise<CooldownInfo> {
  return client.get(`/api/v1/applications/${appId}/cooldown`).then((r) => r.data)
}

// ---------- Interviews ----------
export interface InterviewRecord {
  id: number
  company: string
  position: string | null
  round: string
  interview_date: string | null
  questions: Record<string, unknown>[] | null
  weak_points: string | null
  coaching_suggestions: string[] | null
  result: string | null
  created_at: string
}

export interface InterviewCreate {
  company: string
  position?: string
  round: string
  interview_date?: string
  questions?: Record<string, unknown>[]
  weak_points?: string
  result?: string
}

export function createInterview(data: InterviewCreate): Promise<InterviewRecord> {
  return client.post('/api/v1/interviews/reviews', data).then((r) => r.data)
}

export function listInterviews(): Promise<InterviewRecord[]> {
  return client.get('/api/v1/interviews/reviews').then((r) => r.data)
}

// ---------- Written Tests ----------
export interface WrittenTestRecord {
  id: number
  company: string
  position: string | null
  test_date: string | null
  problem_type: string | null
  difficulty: string | null
  solved: boolean
  stuck_point: string | null
  knowledge_tags: string[] | null
  created_at: string
}

export interface WrittenTestCreate {
  company: string
  position?: string
  test_date?: string
  problem_type?: string
  difficulty?: string
  solved?: boolean
  stuck_point?: string
  knowledge_tags?: string[]
}

export function createWrittenTest(data: WrittenTestCreate): Promise<WrittenTestRecord> {
  return client.post('/api/v1/written-tests/reviews', data).then((r) => r.data)
}

export function listWrittenTests(): Promise<WrittenTestRecord[]> {
  return client.get('/api/v1/written-tests/reviews').then((r) => r.data)
}

// ---------- Skill Profile ----------
export interface SkillProfile {
  total_applications: number
  total_interviews: number
  total_written_tests: number
  weak_skill_areas: string[]
  interview_weak_points_summary: string[]
  written_test_weak_tags: string[]
  recent_suggestions: string[]
}

export function getSkillProfile(): Promise<SkillProfile> {
  return client.get('/api/v1/skill-profile').then((r) => r.data)
}

// ---------- Resume Parsing ----------
export interface ParsedResumeFields {
  name: string
  email: string
  phone: string
  education: Record<string, string>[]
  skills: string[]
  projects: { name: string; role: string; description: string }[]
  internships: Record<string, string>[]
  campus_experience: Record<string, string>[]
  self_evaluation: string
  raw_summary: string
}

export function uploadAndParseResume(file: File): Promise<ParsedResumeFields> {
  const form = new FormData()
  form.append('file', file)
  return client.post('/api/v1/analysis/parse-resume', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  }).then((r) => r.data)
}

