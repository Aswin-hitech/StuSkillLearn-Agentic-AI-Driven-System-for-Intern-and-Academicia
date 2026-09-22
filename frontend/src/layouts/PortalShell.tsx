import {
  Activity,
  BadgeCheck,
  BarChart3,
  BookOpenCheck,
  BriefcaseBusiness,
  Building2,
  CircleUserRound,
  ClipboardList,
  FileBadge2,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  Network,
  SearchCheck,
  ServerCog,
  Settings2,
  ShieldCheck,
  Sparkles,
  Target,
  UsersRound,
  UserCog,
  X,
} from 'lucide-react';
import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';

import { useAuth } from '../features/auth/AuthContext';
import type { UserRole } from '../types/api';

const roleLabel: Record<UserRole, string> = {
  STUDENT: 'Student workspace',
  COMPANY: 'Industry workspace',
  ACADEMICIAN: 'Academician workspace',
  INSTITUTION: 'Institution workspace',
  ADMIN: 'Admin command center',
};

function navigation(role: UserRole) {
  if (role === 'STUDENT') {
    return [
      { to: '/student', label: 'Overview', icon: LayoutDashboard, end: true },
      { to: '/student/profile', label: 'Profile & resume', icon: CircleUserRound },
      { to: '/student/preferences', label: 'Preferences', icon: Target },
      { to: '/student/skill-gap', label: 'Skill gap', icon: Target },
      { to: '/student/lsrw', label: 'LSRW assessment', icon: Activity },
      { to: '/student/learning', label: 'Learning path', icon: BookOpenCheck },
      { to: '/student/portfolio', label: 'Digital portfolio', icon: FileBadge2 },
      { to: '/student/opportunities', label: 'Opportunities', icon: SearchCheck },
      { to: '/student/offers', label: 'Offers & allocation', icon: BriefcaseBusiness },
      { to: '/agents', label: 'Agent activity', icon: Network },
    ];
  }
  if (role === 'COMPANY') {
    return [
      { to: '/company', label: 'Overview', icon: LayoutDashboard, end: true },
      { to: '/company/opportunities', label: 'Opportunities', icon: BriefcaseBusiness },
      { to: '/company/rankings', label: 'Rank lists', icon: UsersRound },
      { to: '/company/allocations', label: 'Allocation & feedback', icon: Target },
      { to: '/company/learning', label: 'Industry learning', icon: GraduationCap },
      { to: '/agents', label: 'Agent activity', icon: Network },
    ];
  }
  if (role === 'ACADEMICIAN') {
    return [
      { to: '/academician', label: 'Overview', icon: LayoutDashboard, end: true },
      { to: '/academician/opportunities', label: 'FDP & research', icon: GraduationCap },
      { to: '/academician/curriculum', label: 'Curriculum signals', icon: BarChart3 },
      { to: '/agents', label: 'Agent activity', icon: Network },
    ];
  }
  if (role === 'INSTITUTION') {
    return [
      { to: '/institution', label: 'Overview', icon: LayoutDashboard, end: true },
      { to: '/institution/readiness', label: 'Student readiness', icon: UsersRound },
      { to: '/institution/curriculum', label: 'Curriculum insights', icon: BarChart3 },
      { to: '/institution/academician-opportunities', label: 'Academician opportunities', icon: GraduationCap },
      { to: '/agents', label: 'Agent activity', icon: Network },
    ];
  }
  return [
    { to: '/admin', label: 'Command center', icon: LayoutDashboard, end: true },
    { to: '/admin/users', label: 'Users & tenancy', icon: UserCog },
    { to: '/admin/organizations', label: 'Organizations', icon: ShieldCheck },
    { to: '/admin/opportunities', label: 'Opportunity moderation', icon: ClipboardList },
    { to: '/admin/governance', label: 'Policy & credentials', icon: Settings2 },
    { to: '/admin/audit', label: 'Audit & allocations', icon: BadgeCheck },
    { to: '/admin/operations', label: 'AI & operations', icon: ServerCog },
  ];
}

export function PortalShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  if (!user) return null;
  const items = navigation(user.role);

  function signOut() {
    void logout();
    navigate('/');
  }

  const sidebar = (
    <div className="flex h-full flex-col bg-slate-950 text-slate-100">
      <div className="border-b border-white/10 px-5 py-5">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-sky-500 text-slate-950"><Sparkles className="h-5 w-5" /></div>
          <div>
            <p className="font-semibold tracking-tight">StuSkillLink</p>
            <p className="text-xs text-slate-400">SIH26044 · CodeRhythm</p>
          </div>
        </div>
      </div>
      <div className="px-5 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{roleLabel[user.role]}</p>
        <p className="mt-1 truncate text-sm text-slate-300">{user.email}</p>
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-5">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive ? 'bg-white text-slate-950' : 'text-slate-300 hover:bg-white/10 hover:text-white'}`}
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-white/10 p-3">
        <button className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-white/10 hover:text-white" onClick={signOut} type="button">
          <LogOut className="h-4 w-4" /> Sign out
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#f6f8fb] lg:grid lg:grid-cols-[260px_minmax(0,1fr)]">
      <aside className="hidden h-screen lg:sticky lg:top-0 lg:block">{sidebar}</aside>
      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button aria-label="Close navigation" className="absolute inset-0 bg-slate-950/50" onClick={() => setMobileOpen(false)} type="button" />
          <aside className="relative h-full w-[280px] shadow-2xl">
            <button aria-label="Close navigation" className="absolute right-3 top-3 z-10 grid h-9 w-9 place-items-center rounded-lg bg-white/10 text-white" onClick={() => setMobileOpen(false)} type="button"><X className="h-4 w-4" /></button>
            {sidebar}
          </aside>
        </div>
      ) : null}
      <div className="min-w-0">
        <header className="sticky top-0 z-30 border-b border-slate-200/90 bg-white/95 backdrop-blur">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <button className="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 text-slate-700 lg:hidden" onClick={() => setMobileOpen(true)} type="button"><Menu className="h-5 w-5" /></button>
              <div>
                <p className="text-sm font-semibold text-slate-900">{roleLabel[user.role]}</p>
                <p className="hidden text-xs text-slate-500 sm:block">Skill mapping · internships · placement continuity</p>
              </div>
            </div>
            <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">
              <Building2 className="h-3.5 w-3.5" /> SIH26044
            </div>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
