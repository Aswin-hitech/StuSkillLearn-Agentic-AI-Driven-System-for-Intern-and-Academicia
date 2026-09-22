import {
  Activity,
  BadgeCheck,
  Bot,
  Building2,
  CheckCircle2,
  CircleSlash2,
  Database,
  FileClock,
  GraduationCap,
  Play,
  RefreshCw,
  Save,
  ServerCog,
  ShieldCheck,
  UserCog,
  UsersRound,
} from 'lucide-react';
import { FormEvent, useEffect, useMemo, useState } from 'react';

import { Empty, Loading, MetricCard, Notice, PageHeader, StatusPill } from '../components/ui';
import { useAuth } from '../features/auth/AuthContext';
import { api, jsonBody } from '../services/api';
import type { Opportunity, UserRole } from '../types/api';

function useToken() {
  return useAuth().token;
}

function fmt(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

type AdminDashboard = {
  metrics: {
    roles: Record<UserRole, number>;
    pending_companies: number;
    pending_institutions: number;
    pending_opportunities: number;
    allocations: Record<string, number>;
  };
  provider: any;
  integrations: Record<string, any>;
  recent_audit: AuditRow[];
};

type AuditRow = {
  id: number;
  actor_role: string;
  actor_user_id?: number | null;
  event_type: string;
  entity_type: string;
  entity_id?: number | null;
  institution_profile_id?: number | null;
  company_profile_id?: number | null;
  student_profile_id?: number | null;
  request_id?: string;
  details?: Record<string, unknown>;
  created_at: string;
};

type AdminUser = {
  id: number;
  public_id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  email_verified: boolean;
  profile_status?: string | null;
  display_name: string;
  institution_profile_id?: number | null;
  created_at: string;
  last_login_at?: string | null;
};

type Institution = {
  id: number;
  institution_name: string;
  institution_code: string;
  city: string;
  state: string;
  verified: boolean;
  verification_status: string;
  verification_notes: string;
  created_at: string;
};

type Company = {
  id: number;
  company_name: string;
  industry: string;
  website: string;
  verified: boolean;
  verification_status: string;
  verification_notes: string;
  user_id: number;
  created_at: string;
};

type AdminStudent = {
  id: number;
  email: string;
  is_active: boolean;
  email_verified: boolean;
  name: string;
  degree: string;
  department: string;
  current_year: number;
  cgpa: number;
  profile_completion: number;
  institution_profile_id?: number | null;
  institution_name: string;
  reservation_category: string;
  reservation_status: string;
  reservation_source: string;
  created_at: string;
};

type AdminAcademician = {
  id: number;
  email: string;
  is_active: boolean;
  name: string;
  department: string;
  designation: string;
  institution_profile_id?: number | null;
  institution_name: string;
  expertise: string[];
  created_at: string;
};

type AdminBadge = {
  id: number;
  student_profile_id: number;
  student_name: string;
  title: string;
  issuer: string;
  verified: boolean;
  verification_status: string;
  verification_notes: string;
  reviewed_at?: string | null;
  reviewed_by_user_id?: number | null;
  credential_url: string;
  evidence_url: string;
  credential_id: string;
  standards: Record<string, unknown>;
  created_at: string;
};

type PlatformPolicy = {
  policy_version: string;
  reservation_policy: Record<string, number>;
  allow_reserved_seat_conversion: boolean;
  minimum_profile_completion: number;
  minimum_required_skill_coverage: number;
};

type AdminAllocation = {
  id: number;
  student_name: string;
  opportunity_title: string;
  company_name: string;
  rank: number;
  round: number;
  status: string;
  category_slot: string;
  algorithm_version: string;
  policy_version: string;
  created_at: string;
  completed_at?: string | null;
};

type AdminAgent = {
  id: number;
  agent_name: string;
  responsibility: string;
  status: string;
  student_profile_id?: number | null;
  company_profile_id?: number | null;
  institution_profile_id?: number | null;
  output_data?: Record<string, any>;
  created_at: string;
};

export function AdminDashboardPage() {
  const token = useToken();
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('');

  const load = () => api<AdminDashboard>('/sih/admin/dashboard', { token }).then(setData);
  useEffect(() => { void load().catch((e) => setError(e.message)); }, []);

  async function action(kind: 'agents' | 'curriculum') {
    setBusy(kind); setError(''); setMessage('');
    try {
      if (kind === 'agents') {
        const rows = await api<any[]>('/sih/admin/agents/run-ecosystem', { method: 'POST', token });
        setMessage(`Seven-agent ecosystem cycle completed with ${rows.length} audited stages.`);
      } else {
        const result = await api<{ generated: number }>('/sih/admin/curriculum/refresh', { method: 'POST', token });
        setMessage(`Curriculum framing refresh completed: ${result.generated} insight records generated.`);
      }
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Admin action failed'); }
    finally { setBusy(''); }
  }

  if (!data && !error) return <Loading label="Loading platform command center…" />;
  if (!data) return <Notice tone="error">{error}</Notice>;
  const roleTotal = Object.values(data.metrics.roles).reduce((a, b) => a + Number(b || 0), 0);
  const activeAllocations = ['OFFERED', 'ACCEPTED', 'IN_PROGRESS'].reduce((sum, key) => sum + Number(data.metrics.allocations[key] || 0), 0);

  return <>
    <PageHeader
      eyebrow="Platform administration"
      title="StuSkillLink command center"
      description="Global governance for organizations, users, policies, opportunities, agents, credentials, allocations, integrations and audit evidence."
      actions={<>
        <button className="btn-secondary" disabled={Boolean(busy)} onClick={() => void action('curriculum')} type="button"><RefreshCw className={`h-4 w-4 ${busy === 'curriculum' ? 'animate-spin' : ''}`} />Refresh curriculum</button>
        <button className="btn-primary" disabled={Boolean(busy)} onClick={() => void action('agents')} type="button"><Play className="h-4 w-4" />Run 7-agent cycle</button>
      </>}
    />
    {message ? <div className="mb-5"><Notice tone="success">{message}</Notice></div> : null}
    {error ? <div className="mb-5"><Notice tone="error">{error}</Notice></div> : null}

    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard label="Platform accounts" value={roleTotal} detail={`${data.metrics.roles.STUDENT ?? 0} students · ${data.metrics.roles.COMPANY ?? 0} companies`} />
      <MetricCard label="Pending organizations" value={data.metrics.pending_companies + data.metrics.pending_institutions} detail={`${data.metrics.pending_companies} companies · ${data.metrics.pending_institutions} institutions`} />
      <MetricCard label="Pending opportunities" value={data.metrics.pending_opportunities} detail="Admin moderation queue" />
      <MetricCard label="Active allocations" value={activeAllocations} detail={`${data.metrics.allocations.COMPLETED ?? 0} completed`} />
    </div>

    <div className="mt-6 grid gap-6 xl:grid-cols-[1.25fr_.75fr]">
      <section className="surface p-6">
        <div className="flex items-center justify-between"><div><h2 className="section-title">Recent platform audit</h2><p className="mt-1 text-sm text-slate-500">Global administrative and workflow evidence.</p></div><FileClock className="h-5 w-5 text-sky-700" /></div>
        <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[720px] text-left text-sm"><thead className="text-xs uppercase tracking-wide text-slate-400"><tr><th className="pb-3">Event</th><th className="pb-3">Actor</th><th className="pb-3">Entity</th><th className="pb-3">Time</th></tr></thead><tbody>{data.recent_audit.map((row) => <tr className="border-t border-slate-100" key={row.id}><td className="py-3 font-medium text-slate-800">{row.event_type.replaceAll('_', ' ')}</td><td className="py-3"><StatusPill value={row.actor_role || 'SYSTEM'} /></td><td className="py-3 text-slate-500">{row.entity_type || '—'} {row.entity_id ? `#${row.entity_id}` : ''}</td><td className="py-3 text-xs text-slate-500">{fmt(row.created_at)}</td></tr>)}</tbody></table></div>
      </section>
      <section className="surface p-6">
        <div className="flex items-center gap-2"><ServerCog className="h-5 w-5 text-emerald-600" /><h2 className="section-title">Platform health</h2></div>
        <div className="mt-5 space-y-3">
          <div className="rounded-xl border border-slate-200 p-4"><div className="flex items-center justify-between"><span className="font-medium text-slate-800">LLM gateway</span><StatusPill value={data.provider?.configured ? 'CONFIGURED' : 'DEGRADED'} /></div><p className="mt-2 text-xs text-slate-500">Priority: {(data.provider?.priority ?? []).join(' → ') || 'deterministic only'}</p></div>
          {Object.entries(data.integrations ?? {}).map(([name, status]: any) => <div className="rounded-xl border border-slate-200 p-4" key={name}><div className="flex items-center justify-between"><span className="font-medium capitalize text-slate-800">{name}</span><StatusPill value={status?.configured ? 'CONFIGURED' : status?.mode ?? 'OPTIONAL'} /></div></div>)}
        </div>
      </section>
    </div>
  </>;
}

export function AdminUsersPage() {
  const token = useToken();
  const currentUser = useAuth().user;
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [students, setStudents] = useState<AdminStudent[]>([]);
  const [academicians, setAcademicians] = useState<AdminAcademician[]>([]);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [role, setRole] = useState('ALL');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [reservationDrafts, setReservationDrafts] = useState<Record<number, { category: string; status: string; source: string }>>({});

  const load = async () => {
    const [u, s, a, i] = await Promise.all([
      api<AdminUser[]>('/sih/admin/users?limit=500', { token }),
      api<AdminStudent[]>('/sih/admin/students?limit=500', { token }),
      api<AdminAcademician[]>('/sih/admin/academicians?limit=500', { token }),
      api<Institution[]>('/sih/admin/institutions', { token }),
    ]);
    setUsers(u); setStudents(s); setAcademicians(a); setInstitutions(i);
    setReservationDrafts(Object.fromEntries(s.map((row) => [row.id, { category: row.reservation_category, status: row.reservation_status, source: row.reservation_source ?? '' }])));
  };
  useEffect(() => { void load().catch((e) => setError(e.message)); }, []);

  const filtered = useMemo(() => users?.filter((u) => role === 'ALL' || u.role === role) ?? [], [users, role]);

  async function setActive(item: AdminUser) {
    setError('');
    try {
      await api(`/sih/admin/users/${item.id}/status`, { method: 'PATCH', token, body: jsonBody({ active: !item.is_active }) });
      setMessage(`${item.email} ${item.is_active ? 'suspended' : 'reactivated'}.`); await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Unable to update account'); }
  }

  async function assign(kind: 'students' | 'academicians', id: number, institution_profile_id: string) {
    try {
      await api(`/sih/admin/${kind}/${id}/institution`, { method: 'PATCH', token, body: jsonBody({ institution_profile_id: institution_profile_id ? Number(institution_profile_id) : null }) });
      setMessage('Institution assignment updated and tenant boundary will apply immediately.'); await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Tenant assignment failed'); }
  }

  async function verifyReservation(studentId: number) {
    const draft = reservationDrafts[studentId]; if (!draft) return;
    try {
      await api(`/sih/admin/students/${studentId}/reservation`, { method: 'PATCH', token, body: jsonBody(draft) });
      setMessage('Reservation/category evidence status updated.'); await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Reservation verification failed'); }
  }

  if (!users) return <Loading label="Loading account governance…" />;
  return <>
    <PageHeader eyebrow="Identity & tenancy" title="Users and membership" description="Activate or suspend accounts, assign institution tenants, and verify protected category evidence from the administrative trust boundary." />
    {message ? <div className="mb-5"><Notice tone="success">{message}</Notice></div> : null}
    {error ? <div className="mb-5"><Notice tone="error">{error}</Notice></div> : null}

    <section className="surface p-5 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="section-title">Account registry</h2><p className="mt-1 text-sm text-slate-500">ADMIN accounts are not publicly registrable.</p></div><select className="input sm:max-w-52" value={role} onChange={(e) => setRole(e.target.value)}><option value="ALL">All roles</option>{['STUDENT','COMPANY','ACADEMICIAN','INSTITUTION','ADMIN'].map((x) => <option key={x}>{x}</option>)}</select></div>
      <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[860px] text-left text-sm"><thead className="text-xs uppercase tracking-wide text-slate-400"><tr><th className="pb-3">Account</th><th className="pb-3">Role</th><th className="pb-3">Verification</th><th className="pb-3">Created</th><th className="pb-3 text-right">Control</th></tr></thead><tbody>{filtered.map((item) => <tr className="border-t border-slate-100" key={item.id}><td className="py-3"><p className="font-medium text-slate-900">{item.display_name || item.email}</p><p className="text-xs text-slate-500">{item.email}</p></td><td className="py-3"><StatusPill value={item.role} /></td><td className="py-3"><div className="flex flex-wrap gap-2"><StatusPill value={item.is_active ? 'ACTIVE' : 'SUSPENDED'} />{item.profile_status ? <StatusPill value={item.profile_status} /> : null}</div></td><td className="py-3 text-xs text-slate-500">{fmt(item.created_at)}</td><td className="py-3 text-right"><button className="btn-secondary px-3 py-2" disabled={item.public_id === currentUser?.public_id && item.is_active} onClick={() => void setActive(item)} type="button">{item.is_active ? <CircleSlash2 className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}{item.is_active ? 'Suspend' : 'Activate'}</button></td></tr>)}</tbody></table></div>
    </section>

    <section className="surface mt-6 p-5 sm:p-6">
      <div className="flex items-center gap-2"><GraduationCap className="h-5 w-5 text-sky-700" /><h2 className="section-title">Student governance</h2></div>
      <div className="mt-5 space-y-4">{students.length ? students.map((student) => { const draft = reservationDrafts[student.id] ?? { category: student.reservation_category, status: student.reservation_status, source: student.reservation_source }; return <div className="rounded-xl border border-slate-200 p-4" key={student.id}><div className="grid gap-4 xl:grid-cols-[1.1fr_.9fr_1.4fr]"><div><p className="font-semibold text-slate-900">{student.name}</p><p className="mt-1 text-xs text-slate-500">{student.email} · {student.degree} {student.department} · CGPA {student.cgpa}</p><p className="mt-2 text-xs text-slate-500">Profile {student.profile_completion}% · <StatusPill value={student.is_active ? 'ACTIVE' : 'SUSPENDED'} /></p></div><label><span className="label">Institution tenant</span><select className="input" value={student.institution_profile_id ?? ''} onChange={(e) => void assign('students', student.id, e.target.value)}><option value="">Unassigned</option>{institutions.map((i) => <option key={i.id} value={i.id}>{i.institution_name}</option>)}</select></label><div className="grid gap-2 sm:grid-cols-[.65fr_.8fr_1.2fr_auto]"><label><span className="label">Category</span><input className="input" value={draft.category} onChange={(e) => setReservationDrafts({ ...reservationDrafts, [student.id]: { ...draft, category: e.target.value } })} /></label><label><span className="label">Evidence status</span><select className="input" value={draft.status} onChange={(e) => setReservationDrafts({ ...reservationDrafts, [student.id]: { ...draft, status: e.target.value } })}><option>UNVERIFIED</option><option>VERIFIED</option><option>REJECTED</option></select></label><label><span className="label">Evidence source</span><input className="input" value={draft.source} onChange={(e) => setReservationDrafts({ ...reservationDrafts, [student.id]: { ...draft, source: e.target.value } })} placeholder="Institution record / certificate ref" /></label><button className="btn-secondary self-end px-3" onClick={() => void verifyReservation(student.id)} type="button"><ShieldCheck className="h-4 w-4" />Save</button></div></div></div>; }) : <Empty title="No students" description="Student accounts will appear here after registration." />}</div>
    </section>

    <section className="surface mt-6 p-5 sm:p-6">
      <div className="flex items-center gap-2"><UserCog className="h-5 w-5 text-sky-700" /><h2 className="section-title">Academician tenancy</h2></div>
      <div className="mt-5 grid gap-3 lg:grid-cols-2">{academicians.map((item) => <div className="rounded-xl border border-slate-200 p-4" key={item.id}><p className="font-semibold text-slate-900">{item.name}</p><p className="mt-1 text-xs text-slate-500">{item.email} · {item.designation || 'Academician'} · {item.department || 'Department not set'}</p><label className="mt-3 block"><span className="label">Institution tenant</span><select className="input" value={item.institution_profile_id ?? ''} onChange={(e) => void assign('academicians', item.id, e.target.value)}><option value="">Unassigned</option>{institutions.map((i) => <option key={i.id} value={i.id}>{i.institution_name}</option>)}</select></label></div>)}</div>
    </section>
  </>;
}

export function AdminOrganizationsPage() {
  const token = useToken();
  const [companies, setCompanies] = useState<Company[] | null>(null);
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [message, setMessage] = useState(''); const [error, setError] = useState('');
  const load = async () => { const [c, i] = await Promise.all([api<Company[]>('/sih/admin/companies', { token }), api<Institution[]>('/sih/admin/institutions', { token })]); setCompanies(c); setInstitutions(i); };
  useEffect(() => { void load().catch((e) => setError(e.message)); }, []);

  async function verify(kind: 'companies' | 'institutions', id: number, status: string) {
    try { await api(`/sih/admin/${kind}/${id}/verification`, { method: 'PATCH', token, body: jsonBody({ status, notes: `Administrative review: ${status}` }) }); setMessage(`${kind === 'companies' ? 'Company' : 'Institution'} status changed to ${status}.`); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Verification update failed'); }
  }

  if (!companies) return <Loading label="Loading organization trust registry…" />;
  return <><PageHeader eyebrow="Trust & organizations" title="Company and institution verification" description="Only administratively verified organizations can exercise privileged platform workflows." />{message ? <div className="mb-5"><Notice tone="success">{message}</Notice></div> : null}{error ? <div className="mb-5"><Notice tone="error">{error}</Notice></div> : null}
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="surface p-6"><div className="flex items-center gap-2"><Building2 className="h-5 w-5 text-sky-700" /><h2 className="section-title">Industry partners</h2></div><div className="mt-4 space-y-3">{companies.map((item) => <div className="rounded-xl border border-slate-200 p-4" key={item.id}><div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-slate-900">{item.company_name}</p><p className="mt-1 text-xs text-slate-500">{item.industry || 'Industry not provided'} · {item.website || 'No website'}</p></div><StatusPill value={item.verification_status} /></div><div className="mt-4 flex flex-wrap gap-2">{['VERIFIED','REJECTED','SUSPENDED','PENDING'].map((status) => <button className="btn-secondary px-3 py-2" key={status} onClick={() => void verify('companies', item.id, status)} type="button">{status.replaceAll('_',' ')}</button>)}</div></div>)}</div></section>
      <section className="surface p-6"><div className="flex items-center gap-2"><GraduationCap className="h-5 w-5 text-emerald-600" /><h2 className="section-title">Institutions</h2></div><div className="mt-4 space-y-3">{institutions.map((item) => <div className="rounded-xl border border-slate-200 p-4" key={item.id}><div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-slate-900">{item.institution_name}</p><p className="mt-1 text-xs text-slate-500">{item.institution_code} · {[item.city,item.state].filter(Boolean).join(', ') || 'Location not provided'}</p></div><StatusPill value={item.verification_status} /></div><div className="mt-4 flex flex-wrap gap-2">{['VERIFIED','REJECTED','SUSPENDED','PENDING'].map((status) => <button className="btn-secondary px-3 py-2" key={status} onClick={() => void verify('institutions', item.id, status)} type="button">{status.replaceAll('_',' ')}</button>)}</div></div>)}</div></section>
    </div>
  </>;
}

export function AdminOpportunitiesPage() {
  const token = useToken();
  const [items, setItems] = useState<Opportunity[] | null>(null);
  const [drafts, setDrafts] = useState<Record<number, { moderation_status: string; status: string; reservation_policy: string; reservation_policy_approved: boolean }>>({});
  const [message, setMessage] = useState(''); const [error, setError] = useState('');
  const load = async () => { const rows = await api<Opportunity[]>('/sih/admin/opportunities', { token }); setItems(rows); setDrafts(Object.fromEntries(rows.map((x) => [x.id, { moderation_status: x.moderation_status ?? 'PENDING', status: x.status, reservation_policy: JSON.stringify(x.reservation_policy ?? {}, null, 0), reservation_policy_approved: Boolean(x.reservation_policy_approved) }]))); };
  useEffect(() => { void load().catch((e) => setError(e.message)); }, []);

  async function save(item: Opportunity) {
    const draft = drafts[item.id]; if (!draft) return;
    setError('');
    try {
      let policy: Record<string, number> = {};
      try { policy = JSON.parse(draft.reservation_policy || '{}'); } catch { throw new Error('Reservation policy must be valid JSON, e.g. {"OBC":1}'); }
      await api(`/sih/admin/opportunities/${item.id}/moderation`, { method: 'PATCH', token, body: jsonBody({ ...draft, reservation_policy: policy }) });
      setMessage(`${item.title} moderation and lifecycle state saved.`); await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Opportunity moderation failed'); }
  }
  if (!items) return <Loading label="Loading moderation queue…" />;
  return <><PageHeader eyebrow="Marketplace governance" title="Opportunity moderation" description="Admin approval controls publication, lifecycle state and any policy-based seat constraints before student applications can rely on the role." />{message ? <div className="mb-5"><Notice tone="success">{message}</Notice></div> : null}{error ? <div className="mb-5"><Notice tone="error">{error}</Notice></div> : null}<div className="space-y-4">{items.length ? items.map((item) => { const d = drafts[item.id]; if (!d) return null; return <div className="surface p-5 sm:p-6" key={item.id}><div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between"><div><div className="flex flex-wrap gap-2"><span className="badge">{item.opportunity_type}</span><StatusPill value={item.moderation_status ?? 'PENDING'} /><StatusPill value={item.status} /></div><h2 className="mt-3 font-semibold text-slate-950">{item.title}</h2><p className="mt-1 text-sm text-slate-500">{item.company_name} · {item.domain} · {item.seats} seats · deadline {fmt(item.deadline)}</p></div><button className="btn-primary" onClick={() => void save(item)} type="button"><Save className="h-4 w-4" />Save moderation</button></div><div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4"><label><span className="label">Moderation</span><select className="input" value={d.moderation_status} onChange={(e) => setDrafts({ ...drafts, [item.id]: { ...d, moderation_status: e.target.value } })}><option>PENDING</option><option>APPROVED</option><option>REJECTED</option></select></label><label><span className="label">Lifecycle</span><select className="input" value={d.status} onChange={(e) => setDrafts({ ...drafts, [item.id]: { ...d, status: e.target.value } })}><option>DRAFT</option><option>OPEN</option><option>PAUSED</option><option>CLOSED</option><option>CANCELLED</option></select></label><label><span className="label">Reservation policy JSON</span><input className="input font-mono text-xs" value={d.reservation_policy} onChange={(e) => setDrafts({ ...drafts, [item.id]: { ...d, reservation_policy: e.target.value } })} /></label><label className="flex items-end"><span className="flex min-h-11 w-full items-center gap-3 rounded-xl border border-slate-200 px-3"><input checked={d.reservation_policy_approved} onChange={(e) => setDrafts({ ...drafts, [item.id]: { ...d, reservation_policy_approved: e.target.checked } })} type="checkbox" /><span className="text-sm font-medium text-slate-700">Policy approved</span></span></label></div></div>; }) : <Empty title="No opportunities" description="Company-submitted roles will enter this moderation queue." />}</div></>;
}

export function AdminGovernancePage() {
  const token = useToken();
  const [policy, setPolicy] = useState<PlatformPolicy | null>(null);
  const [badges, setBadges] = useState<AdminBadge[]>([]);
  const [policyJson, setPolicyJson] = useState('{}');
  const [badgeNotes, setBadgeNotes] = useState<Record<number, string>>({});
  const [message, setMessage] = useState(''); const [error, setError] = useState('');
  const load = async () => { const [p, b] = await Promise.all([api<PlatformPolicy>('/sih/admin/policy', { token }), api<AdminBadge[]>('/sih/admin/badges?limit=500', { token })]); setPolicy(p); setPolicyJson(JSON.stringify(p.reservation_policy ?? {})); setBadges(b); setBadgeNotes(Object.fromEntries(b.map((item) => [item.id, item.verification_notes ?? '']))); };
  useEffect(() => { void load().catch((e) => setError(e.message)); }, []);

  async function savePolicy(e: FormEvent) {
    e.preventDefault(); if (!policy) return;
    try { const reservation_policy = JSON.parse(policyJson || '{}'); await api('/sih/admin/policy', { method: 'PUT', token, body: jsonBody({ ...policy, reservation_policy }) }); setMessage(`Policy ${policy.policy_version} saved and will be snapshotted into new allocation decisions.`); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Policy update failed'); }
  }
  async function verifyBadge(id: number, status: string) {
    try { await api(`/sih/admin/badges/${id}/verification`, { method: 'PATCH', token, body: jsonBody({ status, notes: badgeNotes[id] ?? '' }) }); setMessage(`Credential #${id} changed to ${status}.`); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Credential verification failed'); }
  }
  if (!policy) return <Loading label="Loading governance policy…" />;
  return <><PageHeader eyebrow="Rules & credentials" title="Governance policy" description="Version allocation policy and verify portfolio credentials without giving companies direct control over protected student attributes." />{message ? <div className="mb-5"><Notice tone="success">{message}</Notice></div> : null}{error ? <div className="mb-5"><Notice tone="error">{error}</Notice></div> : null}
    <div className="grid gap-6 xl:grid-cols-[.8fr_1.2fr]">
      <form className="surface p-6" onSubmit={savePolicy}><div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-sky-700" /><h2 className="section-title">Allocation policy</h2></div><div className="mt-5 space-y-4"><label><span className="label">Policy version</span><input className="input" value={policy.policy_version} onChange={(e) => setPolicy({ ...policy, policy_version: e.target.value })} /></label><label><span className="label">Minimum profile completion</span><input className="input" type="number" min="0" max="100" value={policy.minimum_profile_completion} onChange={(e) => setPolicy({ ...policy, minimum_profile_completion: Number(e.target.value) })} /></label><label><span className="label">Minimum required-skill coverage</span><input className="input" type="number" min="0" max="100" value={policy.minimum_required_skill_coverage} onChange={(e) => setPolicy({ ...policy, minimum_required_skill_coverage: Number(e.target.value) })} /></label><label><span className="label">Default reservation policy JSON</span><textarea className="input min-h-24 font-mono text-xs" value={policyJson} onChange={(e) => setPolicyJson(e.target.value)} /></label><label className="flex items-center gap-3 rounded-xl border border-slate-200 p-3"><input checked={policy.allow_reserved_seat_conversion} onChange={(e) => setPolicy({ ...policy, allow_reserved_seat_conversion: e.target.checked })} type="checkbox" /><span className="text-sm font-medium text-slate-700">Allow explicit reserved-seat conversion when the configured policy permits it</span></label><button className="btn-primary w-full" type="submit"><Save className="h-4 w-4" />Save versioned policy</button></div></form>
      <section className="surface p-6"><div className="flex items-center justify-between"><div><h2 className="section-title">Digital credential review</h2><p className="mt-1 text-sm text-slate-500">Completion is not verification. Evidence must pass this trust step.</p></div><BadgeCheck className="h-5 w-5 text-emerald-600" /></div><div className="mt-5 space-y-3">{badges.length ? badges.map((badge) => <div className="rounded-xl border border-slate-200 p-4" key={badge.id}><div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-slate-900">{badge.title}</p><p className="mt-1 text-xs text-slate-500">{badge.student_name} · {badge.issuer}</p>{badge.credential_id ? <p className="mt-1 text-xs text-slate-400">Credential ID: {badge.credential_id}</p> : null}{badge.verification_notes ? <p className="mt-2 text-xs leading-5 text-slate-500">Review note: {badge.verification_notes}</p> : null}{badge.reviewed_at ? <p className="mt-1 text-xs text-slate-400">Reviewed {fmt(badge.reviewed_at)}</p> : null}</div><StatusPill value={badge.verification_status} /></div><label className="mt-4 block"><span className="label">Internal review note</span><textarea className="input min-h-20" value={badgeNotes[badge.id] ?? ''} onChange={(e) => setBadgeNotes({ ...badgeNotes, [badge.id]: e.target.value })} placeholder="Evidence checked, issuer reference, reason for rejection…" /></label><div className="mt-4 flex flex-wrap gap-2">{['VERIFIED','REJECTED','PENDING','SELF_REPORTED'].map((status) => <button className="btn-secondary px-3 py-2" key={status} onClick={() => void verifyBadge(badge.id, status)} type="button">{status.replaceAll('_',' ')}</button>)}</div></div>) : <Empty title="No credentials" description="Student badges and industry completion credentials will appear here." />}</div></section>
    </div>
  </>;
}

export function AdminAuditPage() {
  const token = useToken();
  const [events, setEvents] = useState<AuditRow[] | null>(null);
  const [allocations, setAllocations] = useState<AdminAllocation[]>([]);
  const [query, setQuery] = useState('');
  useEffect(() => { void Promise.all([api<AuditRow[]>('/sih/admin/audit?limit=500', { token }), api<AdminAllocation[]>('/sih/admin/allocations?limit=500', { token })]).then(([a, b]) => { setEvents(a); setAllocations(b); }); }, []);
  const filtered = useMemo(() => (events ?? []).filter((row) => !query || `${row.event_type} ${row.actor_role} ${row.entity_type} ${JSON.stringify(row.details ?? {})}`.toLowerCase().includes(query.toLowerCase())), [events, query]);
  if (!events) return <Loading label="Loading immutable decision evidence…" />;
  return <><PageHeader eyebrow="Audit & explainability" title="Platform evidence trail" description="Search global administrative/domain events and inspect the algorithm and policy versions attached to allocation records." /><section className="surface p-5 sm:p-6"><div className="flex items-center gap-3"><Activity className="h-5 w-5 text-sky-700" /><input className="input max-w-xl" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search audit events, actors or details…" /></div><div className="mt-5 overflow-x-auto"><table className="w-full min-w-[980px] text-left text-sm"><thead className="text-xs uppercase tracking-wide text-slate-400"><tr><th className="pb-3">ID</th><th className="pb-3">Event</th><th className="pb-3">Actor</th><th className="pb-3">Entity</th><th className="pb-3">Request</th><th className="pb-3">Time</th></tr></thead><tbody>{filtered.map((row) => <tr className="border-t border-slate-100" key={row.id}><td className="py-3 text-slate-400">#{row.id}</td><td className="py-3 font-medium text-slate-900">{row.event_type.replaceAll('_',' ')}</td><td className="py-3"><StatusPill value={row.actor_role || 'SYSTEM'} /></td><td className="py-3 text-slate-500">{row.entity_type} {row.entity_id ? `#${row.entity_id}` : ''}</td><td className="py-3 font-mono text-xs text-slate-400">{row.request_id || '—'}</td><td className="py-3 text-xs text-slate-500">{fmt(row.created_at)}</td></tr>)}</tbody></table></div></section><section className="surface mt-6 p-5 sm:p-6"><div className="flex items-center gap-2"><Database className="h-5 w-5 text-emerald-600" /><h2 className="section-title">Allocation decision registry</h2></div><div className="mt-5 overflow-x-auto"><table className="w-full min-w-[900px] text-left text-sm"><thead className="text-xs uppercase tracking-wide text-slate-400"><tr><th className="pb-3">Student</th><th className="pb-3">Role</th><th className="pb-3">State</th><th className="pb-3">Rank/Round</th><th className="pb-3">Slot</th><th className="pb-3">Versions</th></tr></thead><tbody>{allocations.map((row) => <tr className="border-t border-slate-100" key={row.id}><td className="py-3"><p className="font-medium text-slate-900">{row.student_name}</p><p className="text-xs text-slate-500">{row.company_name}</p></td><td className="py-3 text-slate-600">{row.opportunity_title}</td><td className="py-3"><StatusPill value={row.status} /></td><td className="py-3 text-slate-600">#{row.rank} / R{row.round}</td><td className="py-3"><span className="badge">{row.category_slot}</span></td><td className="py-3 text-xs text-slate-500">{row.algorithm_version}<br/>{row.policy_version}</td></tr>)}</tbody></table></div></section></>;
}

const agentDefinitions = [
  'Intake & Eligibility Agent',
  'Skill & Communication Intelligence Agent',
  'Portfolio & Preference Agent',
  'Matching & Allocation Agent',
  'Academician Engagement Agent',
  'Monitoring, Notification & Escalation Agent',
  'Curriculum Framing Agent',
];

export function AdminOperationsPage() {
  const token = useToken();
  const [runs, setRuns] = useState<AdminAgent[] | null>(null);
  const [dashboard, setDashboard] = useState<AdminDashboard | null>(null);
  const [message, setMessage] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const load = async () => { const [a, d] = await Promise.all([api<AdminAgent[]>('/sih/admin/agents?limit=300', { token }), api<AdminDashboard>('/sih/admin/dashboard', { token })]); setRuns(a); setDashboard(d); };
  useEffect(() => { void load().catch((e) => setError(e.message)); }, []);
  async function run() { setBusy(true); try { const rows = await api<any[]>('/sih/admin/agents/run-ecosystem', { method: 'POST', token }); setMessage(`Completed ${rows.length} agent stages.`); await load(); } catch (e) { setError(e instanceof Error ? e.message : 'Agent run failed'); } finally { setBusy(false); } }
  if (!runs || !dashboard) return <Loading label="Loading platform operations…" />;
  return <><PageHeader eyebrow="AI & system operations" title="Seven-agent operations" description="Observe every specialized agent, provider failover state and integration boundary from the administrative control plane." actions={<button className="btn-primary" disabled={busy} onClick={() => void run()} type="button"><Play className="h-4 w-4" />{busy ? 'Running…' : 'Run ecosystem cycle'}</button>} />{message ? <div className="mb-5"><Notice tone="success">{message}</Notice></div> : null}{error ? <div className="mb-5"><Notice tone="error">{error}</Notice></div> : null}
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{agentDefinitions.map((name) => { const last = runs.find((run) => run.agent_name === name); return <div className="surface p-5" key={name}><div className="flex items-start justify-between"><div className="grid h-10 w-10 place-items-center rounded-xl bg-sky-50 text-sky-700"><Bot className="h-5 w-5" /></div>{last ? <StatusPill value={last.status} /> : <span className="badge">READY</span>}</div><h2 className="mt-4 font-semibold text-slate-950">{name}</h2><p className="mt-2 text-sm leading-6 text-slate-500">{last?.responsibility || 'Specialized audited stage in the StuSkillLink orchestration graph.'}</p>{last ? <p className="mt-3 text-xs text-slate-400">Run #{last.id} · {fmt(last.created_at)}</p> : null}</div>; })}</div>
    <div className="mt-6 grid gap-6 lg:grid-cols-2"><section className="surface p-6"><div className="flex items-center gap-2"><ServerCog className="h-5 w-5 text-sky-700" /><h2 className="section-title">LLM routing</h2></div><p className="mt-3 text-sm text-slate-600">Provider order: {(dashboard.provider?.priority ?? []).join(' → ') || 'No live provider configured'}</p><div className="mt-4 grid gap-3 sm:grid-cols-2">{(dashboard.provider?.providers ?? []).map((p: any) => <div className="rounded-xl border border-slate-200 p-4" key={p.id}><div className="flex items-center justify-between"><p className="font-semibold text-slate-900">{p.name}</p><StatusPill value={p.configured ? 'CONFIGURED' : 'OPTIONAL'} /></div><p className="mt-2 break-all text-xs text-slate-500">{p.model}</p></div>)}</div></section><section className="surface p-6"><div className="flex items-center gap-2"><Database className="h-5 w-5 text-emerald-600" /><h2 className="section-title">Integrations</h2></div><div className="mt-4 space-y-3">{Object.entries(dashboard.integrations ?? {}).map(([key, value]: any) => <div className="flex items-center justify-between rounded-xl border border-slate-200 p-4" key={key}><span className="font-medium capitalize text-slate-800">{key}</span><StatusPill value={value?.configured ? 'CONFIGURED' : value?.mode ?? 'OPTIONAL'} /></div>)}</div></section></div>
  </>;
}
