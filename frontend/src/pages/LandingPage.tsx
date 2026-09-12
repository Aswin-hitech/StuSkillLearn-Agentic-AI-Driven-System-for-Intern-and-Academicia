import { ArrowRight, BarChart3, BriefcaseBusiness, Building2, CheckCircle2, GraduationCap, Network, ShieldCheck, Sparkles, UserRound } from 'lucide-react';
import { Link } from 'react-router-dom';

const portals = [
  { title: 'Students', copy: 'Map skills, complete LSRW, close gaps, build a verified portfolio and receive explainable opportunity matches.', icon: UserRound, role: 'STUDENT' },
  { title: 'Industry', copy: 'Create internships and placements, review transparent company-wise rank lists, allocate seats and return feedback.', icon: BriefcaseBusiness, role: 'COMPANY' },
  { title: 'Academicians', copy: 'Discover FDP, research and consultancy opportunities while using live hiring signals to improve teaching.', icon: GraduationCap, role: 'ACADEMICIAN' },
  { title: 'Institutions', copy: 'Track readiness, skill gaps, placement continuity and curriculum actions across departments.', icon: Building2, role: 'INSTITUTION' },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-slate-950 text-sky-400"><Sparkles className="h-5 w-5" /></div>
            <div><p className="font-semibold text-slate-950">StuSkillLink</p><p className="text-xs text-slate-500">SIH26044 · CodeRhythm</p></div>
          </div>
          <div className="flex gap-2"><Link className="btn-secondary" to="/login">Sign in</Link><Link className="btn-primary" to="/register/STUDENT">Create account</Link></div>
        </div>
      </header>

      <main>
        <section className="border-b border-slate-200 bg-[#f7f9fc]">
          <div className="mx-auto grid max-w-7xl gap-12 px-5 py-20 lg:grid-cols-[1.1fr_.9fr] lg:items-center lg:py-28">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3 py-1.5 text-xs font-semibold text-sky-800"><Network className="h-3.5 w-3.5" /> 6-agent academia–industry collaboration</div>
              <h1 className="mt-6 max-w-4xl text-4xl font-semibold tracking-[-0.035em] text-slate-950 sm:text-6xl">Right Student. Right Skill. Right Internship. Deserving Opportunity.</h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">A continuous ecosystem for skill-gap mapping, communication readiness, industry-led learning, explainable internship and placement allocation, and curriculum feedback.</p>
              <div className="mt-8 flex flex-wrap gap-3"><Link className="btn-primary" to="/login">Open demo <ArrowRight className="h-4 w-4" /></Link><a className="btn-secondary" href="#portals">Explore workspaces</a></div>
              <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-slate-600">
                {['Explainable ranking', 'Preference-aware allocation', 'Automatic reallocation', 'NVIDIA NIM ready'].map((item) => <span className="flex items-center gap-2" key={item}><CheckCircle2 className="h-4 w-4 text-emerald-600" />{item}</span>)}
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
                ].map(([n, title, copy]) => <div className="flex gap-4 rounded-xl border border-slate-200 p-4" key={n}><div className="text-sm font-semibold text-sky-700">{n}</div><div><p className="font-semibold text-slate-900">{title}</p><p className="mt-1 text-sm leading-6 text-slate-500">{copy}</p></div></div>)}
              </div>
            </div>
          </div>
        </section>

        <section id="portals" className="mx-auto max-w-7xl px-5 py-20">
          <div className="max-w-2xl"><p className="eyebrow">Four focused workspaces</p><h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">One ecosystem, different jobs to be done.</h2><p className="mt-3 text-slate-600">Each role sees only the information and actions required for its workflow.</p></div>
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {portals.map((portal) => <div className="surface surface-hover p-6" key={portal.role}><div className="grid h-11 w-11 place-items-center rounded-xl bg-slate-100 text-slate-800"><portal.icon className="h-5 w-5" /></div><h3 className="mt-5 text-lg font-semibold text-slate-950">{portal.title}</h3><p className="mt-2 text-sm leading-6 text-slate-600">{portal.copy}</p><Link className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-sky-700" to={`/register/${portal.role}`}>Create {portal.title.toLowerCase()} account <ArrowRight className="h-4 w-4" /></Link></div>)}
          </div>
        </section>

        <section className="border-y border-slate-200 bg-slate-950 text-white">
          <div className="mx-auto grid max-w-7xl gap-8 px-5 py-16 md:grid-cols-3">
            <div><ShieldCheck className="h-6 w-6 text-sky-400" /><h3 className="mt-4 font-semibold">AI assists, rules decide</h3><p className="mt-2 text-sm leading-6 text-slate-400">NVIDIA NIM supports explanations and recommendations. Eligibility, ranking and seat allocation remain deterministic and auditable.</p></div>
            <div><BarChart3 className="h-6 w-6 text-sky-400" /><h3 className="mt-4 font-semibold">Real curriculum signals</h3><p className="mt-2 text-sm leading-6 text-slate-400">Institution insights are generated from live opportunity requirements, student gaps and company feedback.</p></div>
            <div><BriefcaseBusiness className="h-6 w-6 text-sky-400" /><h3 className="mt-4 font-semibold">Internship to placement continuity</h3><p className="mt-2 text-sm leading-6 text-slate-400">The same verified portfolio and outcomes continue into placement matching instead of resetting the student journey.</p></div>
          </div>
        </section>
      </main>
    </div>
  );
}
