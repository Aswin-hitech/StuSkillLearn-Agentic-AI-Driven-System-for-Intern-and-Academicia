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
    <div className="flex h-full flex-col bg-gradient-to-b from-blue-900 to-[#0f172a] text-slate-100">
      {/* Logo + brand */}
      <div className="border-b border-white/10 px-5 py-5">
        <div className="flex items-center gap-3">
          <div
            className="grid h-10 w-10 shrink-0 place-items-center bg-white/20 text-white transition-all duration-300 hover:scale-110"
            style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}
          >
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p className="font-bold tracking-tight text-white">StuSkillLink</p>
          </div>
        </div>
      </div>

      {/* Ministry of AYUSH in sidebar */}
      <div className="border-b border-white/10 px-5 py-3">
        <div className="flex items-center gap-2 rounded-lg bg-white/10 px-3 py-2">
          <Building2 className="h-4 w-4 text-blue-200 shrink-0" />
          <div className="leading-tight">
            <p className="text-[10px] font-bold uppercase tracking-wide text-blue-200">Ministry of AYUSH</p>
            <p className="text-[9px] text-blue-400">Government of India</p>
          </div>
        </div>
      </div>

      {/* User info */}
      <div className="px-5 py-4">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-yellow-400">{roleLabel[user.role]}</p>
        <p className="mt-1 truncate text-sm text-slate-300">{user.email}</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-5">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-white/15 text-white border border-white/25'
                  : 'text-slate-300 hover:bg-white/10 hover:text-white'
              }`
            }
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Sign out */}
      <div className="border-t border-white/10 p-3">
        <button
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-300 transition-all duration-200 hover:bg-white/10 hover:text-white"
          onClick={signOut}
          type="button"
        >
          <LogOut className="h-4 w-4" /> Sign out
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#f8f6f0] lg:grid lg:grid-cols-[260px_minmax(0,1fr)]">
      {/* Desktop sidebar */}
      <aside className="hidden h-screen lg:sticky lg:top-0 lg:block">{sidebar}</aside>

      {/* Mobile drawer */}
      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            aria-label="Close navigation"
            className="absolute inset-0 bg-blue-900/50 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
            type="button"
          />
          <aside className="relative h-full w-[280px] shadow-2xl">
            <button
              aria-label="Close navigation"
              className="absolute right-3 top-3 z-10 grid h-9 w-9 place-items-center rounded-lg bg-white/20 text-white"
              onClick={() => setMobileOpen(false)}
              type="button"
            >
              <X className="h-4 w-4" />
            </button>
            {sidebar}
          </aside>
        </div>
      ) : null}

      {/* Content area */}
      <div className="min-w-0">
        {/* Top bar */}
        <header className="sticky top-0 z-30 border-b border-blue-100 bg-white/95 backdrop-blur">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              {/* Hamburger – mobile only */}
              <button
                aria-label="Open navigation"
                className="grid h-10 w-10 place-items-center rounded-xl border border-blue-200 text-blue-800 transition-all duration-200 hover:bg-blue-50 lg:hidden"
                onClick={() => setMobileOpen(true)}
                type="button"
              >
                <Menu className="h-5 w-5" />
              </button>
              <div>
                <p className="text-sm font-bold text-blue-900">{roleLabel[user.role]}</p>
                <p className="hidden text-xs text-slate-500 sm:block">Skill mapping · internships · placement continuity</p>
              </div>
            </div>

            {/* Ministry of AYUSH in header */}
            <div className="flex items-center gap-2 rounded-lg border border-blue-100 bg-blue-50 px-3 py-1.5">
              <Building2 className="h-3.5 w-3.5 text-blue-700" />
              <span className="text-xs font-bold text-blue-800 hidden sm:inline">Ministry of AYUSH</span>
              <span className="text-xs font-bold text-blue-800 sm:hidden">AYUSH</span>
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
