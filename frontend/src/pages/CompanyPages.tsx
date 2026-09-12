import { BookOpenCheck, BriefcaseBusiness, CheckCircle2, Plus, RefreshCw, Send, ShieldCheck, Trophy, UsersRound } from 'lucide-react';
import { FormEvent, useEffect, useMemo, useState } from 'react';

import { Empty, Loading, MetricCard, Notice, PageHeader, Progress, StatusPill } from '../components/ui';
import { useAuth } from '../features/auth/AuthContext';
import { api, jsonBody } from '../services/api';
import type { Allocation, Opportunity } from '../types/api';

function useToken(){const {token}=useAuth();if(!token)throw new Error('Missing session');return token;}

type CompanyDashboard={
  profile:{company_name:string;industry:string;website:string;description:string;recruiter_name:string;office_locations:string[];verified:boolean};
  metrics:{opportunities:number;applicants:number;active_allocations:number;learning_programs:number};
  opportunities:Opportunity[];
  learning_programs:Array<{id:number;title:string;skills:string[];provider:string;duration:string;resource_url:string;badge_title:string}>;
};

export function CompanyDashboardPage(){
  const token=useToken();const [data,setData]=useState<CompanyDashboard|null>(null);const [error,setError]=useState('');
  useEffect(()=>{void api<CompanyDashboard>('/sih/company/dashboard',{token}).then(setData).catch(e=>setError(e.message));},[]);
  if(!data&&!error)return <Loading/>;if(!data)return <Notice tone="error">{error}</Notice>;
  return <><PageHeader eyebrow="Industry workspace" title={data.profile.company_name} description="Create opportunities, inspect explainable company-wise rankings, allocate seats and return outcome feedback to academia."/>
  <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><MetricCard label="Open opportunities" value={data.metrics.opportunities}/><MetricCard label="Applicants" value={data.metrics.applicants}/><MetricCard label="Active allocations" value={data.metrics.active_allocations}/><MetricCard label="Learning programs" value={data.metrics.learning_programs}/></div>
  <div className="mt-6 grid gap-6 xl:grid-cols-[1.25fr_.75fr]"><section className="surface p-6"><div className="flex items-center justify-between"><div><h2 className="section-title">Opportunity portfolio</h2><p className="mt-1 text-sm text-slate-500">Internships and placements share the same auditable pipeline.</p></div><BriefcaseBusiness className="h-5 w-5 text-sky-700"/></div><div className="mt-5 space-y-3">{data.opportunities.map(o=><div className="rounded-xl border border-slate-200 p-4" key={o.id}><div className="flex items-start justify-between gap-4"><div><div className="flex flex-wrap gap-2"><span className="badge">{o.opportunity_type}</span><StatusPill value={o.status}/></div><p className="mt-2 font-semibold text-slate-950">{o.title}</p><p className="mt-1 text-sm text-slate-500">{o.location} · {o.work_mode} · {o.seats} seats</p></div><div className="text-right text-xs text-slate-500">Min CGPA<br/><span className="text-lg font-semibold text-slate-900">{o.min_cgpa}</span></div></div></div>)}</div></section>
  <section className="surface p-6"><div className="flex items-center gap-2"><ShieldCheck className="h-5 w-5 text-emerald-600"/><h2 className="section-title">Decision boundary</h2></div><p className="mt-4 text-sm leading-6 text-slate-600">AI can extract, recommend and explain. Eligibility, company ranking, reservation handling, tie-breaking and allocation remain deterministic and auditable.</p><div className="mt-5 rounded-xl bg-slate-50 p-4 text-sm text-slate-600"><p className="font-semibold text-slate-900">Company-wise ranking uses</p><p className="mt-2">Skill fit · required coverage · LSRW · projects · academics · location · preferences · verified portfolio</p></div></section></div></>;
}

const emptyOpp={opportunity_type:'INTERNSHIP',title:'',domain:'',description:'',required_skills:'',preferred_skills:'',seats:1,stipend:0,location:'',work_mode:'HYBRID',min_cgpa:0,duration:'8 weeks',deadline:'',reservation_category:'',reservation_seats:0};
export function CompanyOpportunitiesPage(){
  const token=useToken();const [data,setData]=useState<CompanyDashboard|null>(null);const [form,setForm]=useState({...emptyOpp});const [message,setMessage]=useState('');const [error,setError]=useState('');
  const load=()=>api<CompanyDashboard>('/sih/company/dashboard',{token}).then(setData);useEffect(()=>{void load()},[]);
  async function submit(e:FormEvent){e.preventDefault();setError('');const policy:Record<string,number>={};if(form.reservation_category.trim()&&form.reservation_seats>0)policy[form.reservation_category.trim().toUpperCase()]=Number(form.reservation_seats);try{await api('/sih/company/opportunities',{method:'POST',token,body:jsonBody({opportunity_type:form.opportunity_type,title:form.title,domain:form.domain,description:form.description,required_skills:form.required_skills.split(',').map(x=>x.trim()).filter(Boolean),preferred_skills:form.preferred_skills.split(',').map(x=>x.trim()).filter(Boolean),seats:Number(form.seats),stipend:Number(form.stipend),location:form.location,work_mode:form.work_mode,min_cgpa:Number(form.min_cgpa),duration:form.duration,deadline:form.deadline,reservation_policy:policy})});setForm({...emptyOpp});setMessage('Opportunity published. Student matches and company-wise rankings can now update from this role definition.');await load();}catch(e:any){setError(e.message)}}
  if(!data)return <Loading/>;
  return <><PageHeader eyebrow="Opportunity management" title="Internships & placements" description="Publish structured role requirements so skill-gap analysis, semantic relevance and deterministic ranking all use the same evidence."/>{message?<div className="mb-5"><Notice tone="success">{message}</Notice></div>:null}{error?<div className="mb-5"><Notice tone="error">{error}</Notice></div>:null}
  <div className="grid gap-6 xl:grid-cols-[.82fr_1.18fr]"><form className="surface p-6" onSubmit={submit}><div className="flex items-center gap-2"><Plus className="h-5 w-5 text-sky-700"/><h2 className="section-title">Create opportunity</h2></div><div className="mt-5 grid gap-4 sm:grid-cols-2"><label><span className="label">Type</span><select className="input" value={form.opportunity_type} onChange={e=>setForm({...form,opportunity_type:e.target.value})}><option>INTERNSHIP</option><option>PLACEMENT</option></select></label><label><span className="label">Domain</span><input required className="input" value={form.domain} onChange={e=>setForm({...form,domain:e.target.value})} placeholder="AI / Backend / Data"/></label><label className="sm:col-span-2"><span className="label">Title</span><input required className="input" value={form.title} onChange={e=>setForm({...form,title:e.target.value})}/></label><label className="sm:col-span-2"><span className="label">Description</span><textarea required className="input min-h-24" value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label><label className="sm:col-span-2"><span className="label">Required skills · comma-separated</span><input className="input" value={form.required_skills} onChange={e=>setForm({...form,required_skills:e.target.value})} placeholder="Python, FastAPI, Docker"/></label><label className="sm:col-span-2"><span className="label">Preferred skills</span><input className="input" value={form.preferred_skills} onChange={e=>setForm({...form,preferred_skills:e.target.value})}/></label><label><span className="label">Seats</span><input className="input" type="number" min="1" value={form.seats} onChange={e=>setForm({...form,seats:Number(e.target.value)})}/></label><label><span className="label">Min CGPA</span><input className="input" type="number" step="0.1" min="0" max="10" value={form.min_cgpa} onChange={e=>setForm({...form,min_cgpa:Number(e.target.value)})}/></label><label><span className="label">Location</span><input className="input" value={form.location} onChange={e=>setForm({...form,location:e.target.value})}/></label><label><span className="label">Work mode</span><select className="input" value={form.work_mode} onChange={e=>setForm({...form,work_mode:e.target.value})}><option>ONSITE</option><option>HYBRID</option><option>REMOTE</option></select></label><label><span className="label">Stipend / month</span><input className="input" type="number" min="0" value={form.stipend} onChange={e=>setForm({...form,stipend:Number(e.target.value)})}/></label><label><span className="label">Duration</span><input className="input" value={form.duration} onChange={e=>setForm({...form,duration:e.target.value})}/></label><label><span className="label">Deadline</span><input className="input" value={form.deadline} onChange={e=>setForm({...form,deadline:e.target.value})} placeholder="2026-10-15"/></label><div></div><label><span className="label">Optional category slot</span><input className="input" value={form.reservation_category} onChange={e=>setForm({...form,reservation_category:e.target.value})} placeholder="e.g. OBC"/></label><label><span className="label">Category seats</span><input className="input" type="number" min="0" value={form.reservation_seats} onChange={e=>setForm({...form,reservation_seats:Number(e.target.value)})}/></label></div><p className="mt-3 text-xs leading-5 text-slate-500">No statutory quota is hard-coded. The prototype accepts an institution/company policy as a configurable constraint and records the category slot in the audit trail.</p><button className="btn-primary mt-5 w-full" type="submit"><Send className="h-4 w-4"/>Publish opportunity</button></form>
  <section className="surface p-6"><h2 className="section-title">Published roles</h2><div className="mt-4 space-y-3">{data.opportunities.length?data.opportunities.map(o=><div className="rounded-xl border border-slate-200 p-4" key={o.id}><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="flex gap-2"><span className="badge">{o.opportunity_type}</span><span className="badge">{o.domain}</span></div><p className="mt-2 font-semibold text-slate-950">{o.title}</p><p className="mt-1 text-sm text-slate-500">{o.location} · {o.work_mode}</p></div><span className="text-sm font-semibold text-slate-700">{o.seats} seats</span></div><div className="mt-3 flex flex-wrap gap-2">{o.required_skills.map(s=><span className="badge" key={s}>{s}</span>)}</div></div>):<Empty title="No opportunities yet" description="Publish the first internship or placement role."/>}</div></section></div></>;
}

export function CompanyRankingsPage(){
  const token=useToken();const [dash,setDash]=useState<CompanyDashboard|null>(null);const [selected,setSelected]=useState<number|null>(null);const [rows,setRows]=useState<any[]|null>(null);const [notice,setNotice]=useState('');
  useEffect(()=>{void api<CompanyDashboard>('/sih/company/dashboard',{token}).then(d=>{setDash(d);if(d.opportunities[0])setSelected(d.opportunities[0].id)})},[]);
  useEffect(()=>{if(selected)void api<any[]>(`/sih/company/opportunities/${selected}/rankings`,{token}).then(setRows)},[selected]);
  async function allocate(){if(!selected)return;const result=await api<any[]>(`/sih/company/opportunities/${selected}/allocate`,{method:'POST',token});setNotice(`${result.length} active seat allocation(s) confirmed for this role. Existing offers are never duplicated.`);setRows(await api<any[]>(`/sih/company/opportunities/${selected}/rankings`,{token}));}
  if(!dash)return <Loading/>;const opp=dash.opportunities.find(x=>x.id===selected);
  return <><PageHeader eyebrow="Explainable ranking" title="Company-wise rank lists" description="Every candidate score is decomposed into visible evidence. Stable tie-breaking uses score, preference rank, application time and application ID." actions={<button className="btn-primary" disabled={!selected} onClick={()=>void allocate()} type="button"><Trophy className="h-4 w-4"/>Allocate seats</button>}/>{notice?<div className="mb-5"><Notice tone="success">{notice}</Notice></div>:null}
  <div className="surface p-4"><label className="flex flex-col gap-2 sm:flex-row sm:items-center"><span className="text-sm font-semibold text-slate-700">Role</span><select className="input max-w-xl" value={selected??''} onChange={e=>setSelected(Number(e.target.value))}>{dash.opportunities.map(o=><option key={o.id} value={o.id}>{o.title} · {o.opportunity_type}</option>)}</select></label>{opp?<p className="mt-3 text-xs text-slate-500">{opp.seats} seats · required: {opp.required_skills.join(', ')||'No structured skills'}</p>:null}</div>
  <div className="mt-5 space-y-4">{rows===null?<Loading label="Building deterministic rank list…"/>:rows.length?rows.map(r=><div className="surface p-5 sm:p-6" key={r.application_id}><div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between"><div className="flex gap-4"><div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-slate-950 font-semibold text-white">#{r.rank}</div><div><h2 className="font-semibold text-slate-950">{r.student.name}</h2><p className="mt-1 text-sm text-slate-500">{r.student.degree} · {r.student.department} · CGPA {r.student.cgpa}</p><div className="mt-3 flex flex-wrap gap-2">{r.student.skills.slice(0,8).map((s:string)=><span className="badge" key={s}>{s}</span>)}</div></div></div><div className="min-w-32 text-left lg:text-right"><div className="text-3xl font-semibold text-slate-950">{r.match.total_score}%</div><p className="text-xs text-slate-500">overall fit</p><span className="mt-2 inline-flex rounded-full bg-sky-50 px-2.5 py-1 text-[11px] font-semibold text-sky-800">{String(r.match.explanation?.tier??'TIER').replaceAll('_',' ')}</span></div></div><div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[['Skills',r.match.skill_score],['Required coverage',r.match.required_coverage],['Communication',r.match.communication_score],['Projects',r.match.project_score],['Academics',r.match.academic_score],['Location',r.match.location_score],['Preference',r.match.preference_score],['Portfolio',r.match.portfolio_score]].map(([label,value])=><div className="rounded-xl bg-slate-50 p-3" key={String(label)}><Progress label={String(label)} value={Number(value)}/></div>)}</div><div className="mt-4 rounded-xl border border-slate-200 p-4 text-sm text-slate-600"><p className="font-semibold text-slate-900">Why this rank</p><p className="mt-1">{r.match.explanation.summary}</p>{r.match.explanation.missing_required?.length?<p className="mt-2 text-amber-700">Missing required: {r.match.explanation.missing_required.join(', ')}</p>:null}<p className="mt-2 text-xs text-slate-500">Student preference rank: {r.preference_rank??'general pool'}</p></div></div>):<Empty title="No ranked applicants" description="Candidates appear here after applying to this opportunity."/>}</div></>;
}

export function CompanyAllocationsPage(){
  const token=useToken();
  const [items,setItems]=useState<Allocation[]|null>(null);
  const [message,setMessage]=useState('');
  const [activeId,setActiveId]=useState<number|null>(null);
  const [feedbackForm,setFeedbackForm]=useState({rating:5,strengths:'Role skill fit, Communication',improvement_skills:'Cloud deployment',comments:'',recommend_for_placement:true});
  const load=()=>api<Allocation[]>('/sih/company/allocations',{token}).then(setItems);
  useEffect(()=>{void load()},[]);

  async function feedback(id:number){
    await api(`/sih/company/allocations/${id}/feedback`,{
      method:'POST',token,
      body:jsonBody({
        rating:Number(feedbackForm.rating),
        strengths:feedbackForm.strengths.split(',').map(x=>x.trim()).filter(Boolean),
        improvement_skills:feedbackForm.improvement_skills.split(',').map(x=>x.trim()).filter(Boolean),
        comments:feedbackForm.comments,
        recommend_for_placement:feedbackForm.recommend_for_placement,
      }),
    });
    setMessage('Company feedback saved. Placement continuity and curriculum signals have been refreshed.');
    setActiveId(null);
    await load();
  }

  if(!items)return <Loading/>;
  return <>
    <PageHeader eyebrow="Continuous allocation" title="Allocation & feedback" description="Track each offer round, category slot and response. Capture real internship outcomes so placement continuity and curriculum insight use verified company feedback."/>
    {message?<div className="mb-5"><Notice tone="success">{message}</Notice></div>:null}
    <div className="space-y-4">
      {items.length?items.map(x=><div className="surface p-5 sm:p-6" key={x.id}>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2"><h2 className="font-semibold text-slate-950">{x.student_name}</h2><StatusPill value={x.status}/></div>
            <p className="mt-1 text-sm text-slate-500">{x.title}</p>
            <div className="mt-3 flex flex-wrap gap-2"><span className="badge">Rank #{x.rank}</span><span className="badge">Round {x.round}</span><span className="badge">{x.category_slot} slot</span></div>
          </div>
          <button className="btn-secondary" onClick={()=>setActiveId(activeId===x.id?null:x.id)} type="button"><CheckCircle2 className="h-4 w-4"/>{activeId===x.id?'Close feedback':'Add feedback'}</button>
        </div>
        {activeId===x.id?<div className="mt-5 border-t border-slate-200 pt-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <label><span className="label">Rating (1-5)</span><input className="input" type="number" min="1" max="5" value={feedbackForm.rating} onChange={e=>setFeedbackForm({...feedbackForm,rating:Number(e.target.value)})}/></label>
            <label className="flex items-end gap-3 rounded-xl border border-slate-200 p-3"><input checked={feedbackForm.recommend_for_placement} onChange={e=>setFeedbackForm({...feedbackForm,recommend_for_placement:e.target.checked})} type="checkbox"/><span className="text-sm font-medium text-slate-700">Recommend for placement continuity</span></label>
            <label><span className="label">Strengths · comma-separated</span><input className="input" value={feedbackForm.strengths} onChange={e=>setFeedbackForm({...feedbackForm,strengths:e.target.value})}/></label>
            <label><span className="label">Improvement skills</span><input className="input" value={feedbackForm.improvement_skills} onChange={e=>setFeedbackForm({...feedbackForm,improvement_skills:e.target.value})}/></label>
            <label className="sm:col-span-2"><span className="label">Comments</span><textarea className="input min-h-24" value={feedbackForm.comments} onChange={e=>setFeedbackForm({...feedbackForm,comments:e.target.value})} placeholder="Evidence-based internship / placement feedback…"/></label>
          </div>
          <button className="btn-primary mt-4" onClick={()=>void feedback(x.id)} type="button"><Send className="h-4 w-4"/>Save feedback</button>
        </div>:null}
      </div>):<Empty title="No allocations" description="Open a company-wise rank list and allocate seats."/>}
    </div>
  </>;
}

export function CompanyLearningPage(){
  const token=useToken();const [dash,setDash]=useState<CompanyDashboard|null>(null);const [title,setTitle]=useState('Backend API Readiness Sprint');const [skills,setSkills]=useState('FastAPI, Docker, PostgreSQL');const [message,setMessage]=useState('');const load=()=>api<CompanyDashboard>('/sih/company/dashboard',{token}).then(setDash);useEffect(()=>{void load()},[]);
  async function create(e:FormEvent){e.preventDefault();await api('/sih/company/learning-programs',{method:'POST',token,body:jsonBody({title,skills:skills.split(',').map(x=>x.trim()).filter(Boolean),provider:dash?.profile.company_name??'Industry',duration:'2 weeks',resource_url:'https://swayam.gov.in/explorer',badge_title:`${title} Completion`})});setMessage('Industry-led learning program added. Students can use program outcomes as portfolio evidence.');await load()}
  if(!dash)return <Loading/>;
  return <><PageHeader eyebrow="Industry-led learning" title="Turn hiring gaps into readiness programs" description="Create targeted learning programs around skills your company repeatedly needs, with verifiable badge intent built into the digital portfolio model."/>{message?<div className="mb-5"><Notice tone="success">{message}</Notice></div>:null}<div className="grid gap-6 lg:grid-cols-[.7fr_1.3fr]"><form className="surface p-6" onSubmit={create}><BookOpenCheck className="h-6 w-6 text-sky-700"/><h2 className="mt-3 section-title">New program</h2><label className="mt-5 block"><span className="label">Program title</span><input className="input" value={title} onChange={e=>setTitle(e.target.value)} required/></label><label className="mt-4 block"><span className="label">Skills</span><input className="input" value={skills} onChange={e=>setSkills(e.target.value)}/></label><button className="btn-primary mt-5 w-full" type="submit"><Plus className="h-4 w-4"/>Create program</button></form><section className="surface p-6"><h2 className="section-title">Active programs</h2><div className="mt-4 space-y-3">{dash.learning_programs.map(x=><div className="rounded-xl border border-slate-200 p-4" key={x.id}><p className="font-semibold text-slate-950">{x.title}</p><p className="mt-1 text-sm text-slate-500">{x.provider} · {x.duration}</p><div className="mt-3 flex flex-wrap gap-2">{x.skills.map(s=><span className="badge" key={s}>{s}</span>)}</div></div>)}</div></section></div></>;
}
