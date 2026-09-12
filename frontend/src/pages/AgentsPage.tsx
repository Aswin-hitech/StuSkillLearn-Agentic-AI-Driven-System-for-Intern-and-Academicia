import { Bot, Cpu, Database, Network, ShieldCheck, Sparkles } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Loading, Notice, PageHeader, StatusPill } from '../components/ui';
import { useAuth } from '../features/auth/AuthContext';
import { api } from '../services/api';

type Provider = {
  id: string;
  name: string;
  configured: boolean;
  model: string;
  protocol: string;
};

type ProviderStatus = {
  configured: boolean;
  mode: string;
  priority: string[];
  preferred_provider: string | null;
  providers: Provider[];
  last_generation?: { provider?: string; model?: string; mode?: string } | null;
};

type AgentRun = {
  id: number;
  agent_name: string;
  status: string;
  output_data?: {
    reasoning?: string;
    duration_ms?: number;
    orchestration?: string;
    graph_node?: string;
    llm?: { provider?: string; model?: string; mode?: string; attempts?: Array<{ provider: string; status: string; error?: string }> };
  };
};

const definitions = [
  ['Eligibility & Profile Agent', 'Validates profile readiness and deterministic eligibility inputs.'],
  ['Skill & Communication Agent', 'Extracts skills, maps gaps, evaluates LSRW and generates learning actions.'],
  ['Portfolio & Preference Agent', 'Maintains verified portfolio evidence and student preference state.'],
  ['Matching & Allocation Agent', 'Explains matches while deterministic services own ranking, constraints and allocation.'],
  ['Academic Engagement Agent', 'Converts hiring outcomes into curriculum signals and academician opportunities.'],
  ['Monitoring & Reallocation Agent', 'Tracks offers and keeps vacant seats moving through ranked candidates.'],
];

export function AgentsPage() {
  const { token } = useAuth();
  const [runs, setRuns] = useState<AgentRun[] | null>(null);
  const [provider, setProvider] = useState<ProviderStatus | null>(null);
  const [integrations, setIntegrations] = useState<any>(null);

  useEffect(() => {
    if (token) void api<AgentRun[]>('/sih/system/agents', { token }).then(setRuns);
    void api<ProviderStatus>('/sih/system/provider').then(setProvider);
    void api('/sih/system/integrations').then(setIntegrations);
  }, [token]);

  if (!runs || !provider) return <Loading />;
  const langGraphActive = runs.some((run) => run.output_data?.orchestration === 'langgraph');

  return <>
    <PageHeader
      eyebrow="Agentic AI control plane"
      title="Six audited agents, deterministic decisions"
      description="LangGraph orchestrates every domain stage and checkpoints its state. Each node records evidence, duration, reasoning source, provider and model while LLM output remains advisory."
    />

    <div className="mb-5"><Notice tone={langGraphActive ? 'success' : 'info'}>
      {langGraphActive ? 'LangGraph orchestration verified · six checkpointed nodes completed.' : 'Run the six-agent cycle to create the first LangGraph checkpoint.'}
    </Notice></div>

    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {definitions.map(([name, desc]) => {
        const last = runs.find((item) => item.agent_name === name);
        const llm = last?.output_data?.llm;
        return <div className="surface p-5" key={name}>
          <div className="flex items-start justify-between gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-sky-50 text-sky-700"><Bot className="h-5 w-5" /></div>
            {last ? <StatusPill value={last.status} /> : <span className="badge">Ready</span>}
          </div>
          <h2 className="mt-4 font-semibold text-slate-950">{name}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-600">{desc}</p>
          {last?.output_data?.reasoning ? <p className="mt-3 rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-600">{last.output_data.reasoning}</p> : null}
          {last ? <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-slate-500">
            <span>Run #{last.id}</span>
            <span>·</span>
            <span>{last.output_data?.duration_ms ?? 0} ms</span>
            <span>·</span>
            <span>{llm?.mode === 'LIVE' ? `${llm.provider} · ${llm.model}` : 'deterministic fallback'}</span>
            {last.output_data?.graph_node ? <><span>·</span><span>LangGraph · {last.output_data.graph_node}</span></> : null}
          </div> : null}
        </div>;
      })}
    </div>

    <div className="mt-6 grid gap-6 lg:grid-cols-[1.25fr_.75fr]">
      <section className="surface p-6">
        <div className="flex items-center gap-2"><Cpu className="h-5 w-5 text-emerald-600" /><h2 className="section-title">LLM provider failover</h2></div>
        <p className="mt-2 text-sm text-slate-500">Attempt order: {provider.priority.join(' → ')}</p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {provider.providers.map((item) => <div className="rounded-xl border border-slate-200 p-4" key={item.id}>
            <div className="flex items-center justify-between gap-3"><p className="font-semibold text-slate-900">{item.name}</p><StatusPill value={item.configured ? 'CONFIGURED' : 'NOT CONFIGURED'} /></div>
            <p className="mt-2 break-all text-xs text-slate-500">{item.model}</p>
            <p className="mt-1 text-[11px] uppercase tracking-wide text-slate-400">{item.protocol}</p>
          </div>)}
        </div>
        {!provider.configured ? <div className="mt-4"><Notice>No LLM key is configured. Agents still run trusted deterministic checks and are marked degraded.</Notice></div> : null}
        {provider.last_generation?.mode === 'FALLBACK' ? <div className="mt-4"><Notice tone="error">The last model request exhausted all configured providers and used deterministic fallback.</Notice></div> : null}
      </section>

      <section className="surface p-6">
        <div className="flex items-center gap-2"><Network className="h-5 w-5 text-sky-700" /><h2 className="section-title">Protected decision boundary</h2></div>
        <div className="mt-4 space-y-3 text-sm leading-6 text-slate-600">
          <p><ShieldCheck className="mr-2 inline h-4 w-4" />Eligibility, scoring, tie-breaking and allocation remain deterministic.</p>
          <p><Sparkles className="mr-2 inline h-4 w-4" />LLMs explain evidence and recommend learning actions.</p>
          <p><Database className="mr-2 inline h-4 w-4" />Each stage persists facts, provenance, duration and failure state.</p>
        </div>
        {integrations?.mongodb?.configured ? <p className="mt-4 text-xs font-semibold text-emerald-700">MongoDB event mirror configured</p> : null}
      </section>
    </div>
  </>;
}
