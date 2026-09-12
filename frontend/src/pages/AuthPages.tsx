import { ArrowLeft, Building2, GraduationCap, Sparkles, UserRound } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthContext';
import { api, jsonBody } from '../services/api';
import type { AuthResponse, UserRole } from '../types/api';
import { Notice } from '../components/ui';

const demoAccounts: Array<{ role: UserRole; email: string; label: string }> = [
  { role: 'STUDENT', email: 'student@stuskilllink.demo', label: 'Student' },
  { role: 'COMPANY', email: 'industry@stuskilllink.demo', label: 'Industry' },
  { role: 'ACADEMICIAN', email: 'academician@stuskilllink.demo', label: 'Academician' },
  { role: 'INSTITUTION', email: 'institution@stuskilllink.demo', label: 'Institution' },
];

function pathForRole(role: UserRole) { return `/${role.toLowerCase()}`; }

function AuthShell({ children }: { children: React.ReactNode }) {
  return <div className="min-h-screen bg-[#f6f8fb] px-4 py-8 sm:py-14"><div className="mx-auto max-w-md"><Link to="/" className="mb-6 inline-flex items-center gap-2 text-sm font-medium text-slate-600"><ArrowLeft className="h-4 w-4" /> Back to home</Link><div className="surface p-6 shadow-soft sm:p-8"><div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-slate-950 text-sky-400"><Sparkles className="h-5 w-5" /></div><div><p className="font-semibold text-slate-950">StuSkillLink</p><p className="text-xs text-slate-500">SIH26044</p></div></div>{children}</div></div></div>;
}

export function LoginPage() {
  const { setSession } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('student@stuskilllink.demo');
  const [password, setPassword] = useState('Demo@123');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try { const result = await api<AuthResponse>('/auth/login', { method: 'POST', body: jsonBody({ email, password }) }); setSession(result); navigate(pathForRole(result.user.role)); }
    catch (err) { setError(err instanceof Error ? err.message : 'Unable to sign in'); }
    finally { setBusy(false); }
  }

  async function demo(account: typeof demoAccounts[number]) {
    setBusy(true); setError(''); setEmail(account.email); setPassword('Demo@123');
    try { const result = await api<AuthResponse>('/auth/login', { method: 'POST', body: jsonBody({ email: account.email, password: 'Demo@123' }) }); setSession(result); navigate(pathForRole(result.user.role)); }
    catch (err) { setError(err instanceof Error ? err.message : 'Unable to sign in'); }
    finally { setBusy(false); }
  }

  return <AuthShell><div className="mt-7"><h1 className="text-2xl font-semibold tracking-tight text-slate-950">Sign in to your workspace</h1><p className="mt-2 text-sm leading-6 text-slate-500">Use a demo role below or your own StuSkillLink account.</p></div><div className="mt-6 grid grid-cols-2 gap-2">{demoAccounts.map((account) => <button type="button" onClick={() => void demo(account)} disabled={busy} className="btn-secondary px-3" key={account.role}>{account.label}</button>)}</div><div className="my-6 flex items-center gap-3"><div className="h-px flex-1 bg-slate-200" /><span className="text-xs font-medium text-slate-400">or</span><div className="h-px flex-1 bg-slate-200" /></div>{error ? <Notice tone="error">{error}</Notice> : null}<form className="mt-5 space-y-4" onSubmit={submit}><label><span className="label">Email</span><input className="input" value={email} onChange={(e) => setEmail(e.target.value)} type="email" /></label><label><span className="label">Password</span><input className="input" value={password} onChange={(e) => setPassword(e.target.value)} type="password" /></label><button className="btn-primary w-full" disabled={busy} type="submit">{busy ? 'Signing in…' : 'Sign in'}</button></form><p className="mt-6 text-center text-sm text-slate-500">Need an account? <Link className="font-semibold text-sky-700" to="/register/STUDENT">Register</Link></p></AuthShell>;
}

export function RegisterPage() {
  const { role = 'STUDENT' } = useParams();
  const normalized = (['STUDENT','COMPANY','ACADEMICIAN','INSTITUTION'].includes(role.toUpperCase()) ? role.toUpperCase() : 'STUDENT') as UserRole;
  const { setSession } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const icons = { STUDENT: UserRound, COMPANY: Building2, ACADEMICIAN: GraduationCap, INSTITUTION: Building2 };
  const Icon = icons[normalized];
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setError(''); try { const result = await api<AuthResponse>(`/auth/register/${normalized}`, { method: 'POST', body: jsonBody({ email, password }) }); setSession(result); navigate(pathForRole(result.user.role)); } catch (err) { setError(err instanceof Error ? err.message : 'Unable to register'); } finally { setBusy(false); } }
  return <AuthShell><div className="mt-7 flex items-start gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-sky-50 text-sky-700"><Icon className="h-5 w-5" /></div><div><h1 className="text-2xl font-semibold tracking-tight text-slate-950">Create {normalized.toLowerCase()} account</h1><p className="mt-1 text-sm text-slate-500">You can complete the role profile after registration.</p></div></div><div className="mt-5 flex flex-wrap gap-2">{demoAccounts.map((item) => <Link key={item.role} className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold ${item.role === normalized ? 'bg-slate-950 text-white' : 'bg-slate-100 text-slate-600'}`} to={`/register/${item.role}`}>{item.label}</Link>)}</div>{error ? <div className="mt-5"><Notice tone="error">{error}</Notice></div> : null}<form className="mt-6 space-y-4" onSubmit={submit}><label><span className="label">Email</span><input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label><label><span className="label">Password</span><input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required /><span className="mt-1 block text-xs text-slate-400">At least 8 characters.</span></label><button className="btn-primary w-full" disabled={busy} type="submit">{busy ? 'Creating account…' : 'Create account'}</button></form></AuthShell>;
}
