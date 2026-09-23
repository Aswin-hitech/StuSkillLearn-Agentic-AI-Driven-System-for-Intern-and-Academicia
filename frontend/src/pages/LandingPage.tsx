import { ArrowRight, BarChart3, BriefcaseBusiness, Building2, GraduationCap, Network, ShieldCheck, Sparkles, UserRound } from 'lucide-react';
import { Link } from 'react-router-dom';

const portals = [
  { title: 'Students', copy: 'Map skills, complete LSRW, close gaps, build an evidence portfolio with explicit verification status and receive explainable opportunity matches.', icon: UserRound, role: 'STUDENT' },
  { title: 'Industry', copy: 'Create internships and placements, review transparent company-wise rank lists, allocate seats and return feedback.', icon: BriefcaseBusiness, role: 'COMPANY' },
  { title: 'Academicians', copy: 'Discover FDP, research and consultancy opportunities while using live hiring signals to improve teaching.', icon: GraduationCap, role: 'ACADEMICIAN' },
  { title: 'Institutions', copy: 'Track readiness, skill gaps, placement continuity and curriculum actions across departments.', icon: Building2, role: 'INSTITUTION' },
];

function AyushBadge({ dark = false }: { dark?: boolean }) {
  if (dark) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-3 py-1.5">
        <Building2 className="h-4 w-4 text-yellow-200" />
        <div className="leading-tight">
          <p className="text-[10px] font-bold uppercase tracking-wide text-yellow-100">Ministry of AYUSH</p>
          <p className="text-[9px] text-yellow-300">Government of India</p>
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 shadow-sm">
      <Building2 className="h-4 w-4 text-blue-700" />
      <div className="leading-tight">
        <p className="text-[10px] font-bold uppercase tracking-wide text-blue-800">Ministry of AYUSH</p>
        <p className="text-[9px] text-blue-500">Government of India</p>
      </div>
    </div>
  );
}

export function LandingPage() {
  return (
    <div className="min-h-screen bg-[#f8f6f0]">
      {/* Sticky header */}
      <header className="sticky top-0 z-50 border-b border-blue-100 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div
              className="grid h-10 w-10 shrink-0 place-items-center bg-blue-700 text-white transition-all duration-300 hover:scale-110 hover:bg-blue-800"
              style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}
            >
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <p className="font-bold tracking-tight text-blue-900">StuSkillLink</p>
            </div>
          </div>

          {/* Ministry badge (center on medium+) */}
          <div className="hidden sm:block">
            <AyushBadge />
          </div>

          {/* CTAs */}
          <div className="flex gap-2">
            <Link className="btn-secondary" to="/login">Sign in</Link>
            <Link className="btn-primary" to="/register/STUDENT">Create account</Link>
          </div>
        </div>
        {/* Mobile: ministry badge below */}
        <div className="flex justify-center border-t border-blue-50 py-2 sm:hidden">
          <AyushBadge />
        </div>
      </header>

      <main>
        {/* Hero */}
        <section className="border-b border-blue-100 bg-gradient-to-b from-white to-[#f8f6f0]">
          <div className="mx-auto grid max-w-7xl gap-12 px-5 py-20 lg:grid-cols-[1.1fr_.9fr] lg:items-center lg:py-28">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-yellow-300/60 bg-yellow-50 px-3 py-1.5 text-xs font-bold text-yellow-800">
                <Network className="h-3.5 w-3.5" /> 7-agent academia–industry collaboration
              </div>
              <h1 className="mt-6 max-w-4xl text-4xl font-bold tracking-tight text-blue-900 sm:text-6xl">
                Right Student. Right Skill. Right Internship. Deserving Opportunity.
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
                A continuous ecosystem for skill-gap mapping, communication readiness, industry-led learning, explainable internship and placement allocation, and curriculum feedback.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link className="btn-primary" to="/login">Get Started <ArrowRight className="h-4 w-4" /></Link>
                <a className="btn-secondary" href="#portals">Explore workspaces</a>
              </div>
              <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-600">
                {['Explainable ranking', 'Preference-aware allocation', 'Automatic reallocation', 'NVIDIA NIM ready'].map((item) => (
                  <span className="flex items-center gap-2" key={item}>
                    <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />{item}
                  </span>
                ))}
              </div>
            </div>

            <div className="surface p-5 shadow-soft sm:p-7">
              <p className="eyebrow">Closed-loop intelligence</p>
              <div className="mt-5 space-y-3">
                {[
                  ['01', 'Skill map', 'Resume + profile evidence becomes a canonical skill profile.'],
                  ['02', 'Readiness', 'LSRW and role requirements reveal actionable gaps.'],
                  ['03', 'Match & allocate', 'Deterministic scores, preferences, seats and transparent tie-breaks.'],
                  ['04', 'Learn & improve', 'Industry learning paths update the digital portfolio.'],
                  ['05', 'Feedback to curriculum', 'Hiring and internship outcomes become institution signals.'],
                ].map(([n, title, copy]) => (
                  <div
                    className="flex gap-4 rounded-xl border border-blue-100 bg-white p-4 transition-all duration-300 hover:border-blue-400 hover:shadow-soft"
                    key={n}
                  >
                    <div className="text-sm font-bold text-blue-500">{n}</div>
                    <div>
                      <p className="font-bold text-blue-900">{title}</p>
                      <p className="mt-1 text-sm leading-6 text-slate-500">{copy}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Portals */}
        <section id="portals" className="mx-auto max-w-7xl px-5 py-20">
          <div className="max-w-2xl">
            <p className="eyebrow">Four focused workspaces</p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-blue-900">One ecosystem, different jobs to be done.</h2>
            <p className="mt-3 text-slate-600">Each role sees only the information and actions required for its workflow.</p>
          </div>
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {portals.map((portal) => (
              <div className="surface surface-hover p-6 group" key={portal.role}>
                <div
                  className="grid h-11 w-11 place-items-center bg-blue-700 text-white transition-all duration-300 group-hover:scale-110 group-hover:bg-blue-800"
                  style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}
                >
                  <portal.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-5 text-lg font-bold text-blue-900">{portal.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">{portal.copy}</p>
                <Link
                  className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-blue-600 transition-colors hover:text-blue-900"
                  to={`/register/${portal.role}`}
                >
                  Create {portal.title.toLowerCase()} account <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            ))}
          </div>
        </section>

        {/* Feature highlights (dark blue section) */}
        <section className="border-y border-blue-900 bg-gradient-to-b from-blue-900 to-[#0f172a] text-slate-100">
          <div className="mx-auto grid max-w-7xl gap-8 px-5 py-16 md:grid-cols-3">
            <div className="transition-all duration-300 hover:scale-[1.02]">
              <ShieldCheck className="h-6 w-6 text-yellow-300" />
              <h3 className="mt-4 font-bold text-white">AI assists, rules decide</h3>
              <p className="mt-2 text-sm leading-6 text-slate-300">NVIDIA NIM supports explanations and recommendations. Eligibility, ranking and seat allocation remain deterministic and auditable.</p>
            </div>
            <div className="transition-all duration-300 hover:scale-[1.02]">
              <BarChart3 className="h-6 w-6 text-yellow-300" />
              <h3 className="mt-4 font-bold text-white">Real curriculum signals</h3>
              <p className="mt-2 text-sm leading-6 text-slate-300">Institution insights are generated from live opportunity requirements, student gaps and company feedback.</p>
            </div>
            <div className="transition-all duration-300 hover:scale-[1.02]">
              <BriefcaseBusiness className="h-6 w-6 text-yellow-300" />
              <h3 className="mt-4 font-bold text-white">Internship to placement continuity</h3>
              <p className="mt-2 text-sm leading-6 text-slate-300">The same portable evidence portfolio and verified outcomes continue into placement matching instead of resetting the student journey.</p>
            </div>
          </div>
          {/* Ministry footer inside dark section */}
          <div className="border-t border-white/10 py-4 px-5">
            <div className="mx-auto flex max-w-7xl items-center justify-center gap-3">
              <span className="text-xs text-slate-400">An initiative under</span>
              <AyushBadge dark />
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
