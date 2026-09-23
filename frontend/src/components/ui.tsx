import { CheckCircle2, CircleAlert, Loader2 } from 'lucide-react';

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: React.ReactNode }) {
  return (
    <div className="mb-7 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1 className="page-title mt-1">{title}</h1>
        {description ? <p className="page-copy">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
    </div>
  );
}

export function MetricCard({ label, value, detail }: { label: string; value: React.ReactNode; detail?: React.ReactNode }) {
  return (
    <div className="metric">
      <p className="metric-label">{label}</p>
      <div className="metric-value">{value}</div>
      {detail ? <div className="mt-2 text-xs text-slate-500">{detail}</div> : null}
    </div>
  );
}

export function Progress({ value, label }: { value: number; label?: string }) {
  const safe = Math.max(0, Math.min(100, Number.isFinite(value) ? value : 0));
  return (
    <div>
      {label ? <div className="mb-2 flex items-center justify-between text-xs font-medium text-slate-600"><span>{label}</span><span>{safe.toFixed(0)}%</span></div> : null}
      <div className="progress-track"><div className="h-full rounded-full bg-sky-600" style={{ width: `${safe}%` }} /></div>
    </div>
  );
}

export function StatusPill({ value }: { value: string }) {
  const normalized = value.toUpperCase();
  const good = ['ACCEPTED', 'OPEN', 'COMPLETED', 'VERIFIED', 'READY'].some((item) => normalized.includes(item));
  const warn = ['OFFERED', 'PENDING', 'APPLIED', 'DEGRADED'].some((item) => normalized.includes(item));
  const bad = ['FAILED', 'ERROR', 'UNAVAILABLE'].some((item) => normalized.includes(item));
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${good ? 'bg-emerald-50 text-emerald-700' : warn ? 'bg-amber-50 text-amber-700' : bad ? 'bg-rose-50 text-rose-700' : 'bg-slate-100 text-slate-600'}`}>{value.replaceAll('_', ' ')}</span>;
}

export function Loading({ label = 'Loading workspace…' }: { label?: string }) {
  return <div className="surface flex min-h-48 items-center justify-center gap-3 p-8 text-sm text-slate-500"><Loader2 className="h-5 w-5 animate-spin" />{label}</div>;
}

export function Notice({ tone = 'info', children }: { tone?: 'info' | 'success' | 'error'; children: React.ReactNode }) {
  const Icon = tone === 'success' ? CheckCircle2 : tone === 'error' ? CircleAlert : CircleAlert;
  const classes = tone === 'success' ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : tone === 'error' ? 'border-rose-200 bg-rose-50 text-rose-800' : 'border-sky-200 bg-sky-50 text-sky-800';
  return <div className={`flex gap-3 rounded-xl border p-3.5 text-sm ${classes}`}><Icon className="mt-0.5 h-4 w-4 shrink-0" /> <div>{children}</div></div>;
}

export function Empty({ title, description }: { title: string; description: string }) {
  return <div className="surface p-8 text-center"><h3 className="font-semibold text-slate-900">{title}</h3><p className="mx-auto mt-2 max-w-md text-sm text-slate-500">{description}</p></div>;
}
