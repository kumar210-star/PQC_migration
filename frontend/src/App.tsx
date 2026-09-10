import { useEffect, useMemo, useState } from 'react'
import { Activity, Archive, Atom, BookOpen, CheckCircle2, ClipboardList, FileText, Fingerprint, Gauge, KeyRound, LayoutDashboard, Menu, Network, Play, Radar, RefreshCw, ShieldAlert, ShieldCheck, Sparkles, X } from 'lucide-react'
import { api } from './api'
import type { Finding, Recommendation, RiskSummary, Task } from './types'

const views = [
  ['Dashboard', LayoutDashboard], ['Inventory', Archive], ['Risk Analysis', ShieldAlert],
  ['PQC Recommendations', Sparkles], ['Migration Plan', ClipboardList], ['Crypto-Agility', Network],
  ['Migration Demo', Play], ['Reports', FileText], ['Documentation', BookOpen]
] as const

const riskClass = (value: string) => `pill ${value.toLowerCase().replace(' ', '-')}`

function App() {
  const [view, setView] = useState('Dashboard')
  const [inventory, setInventory] = useState<Finding[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [risk, setRisk] = useState<RiskSummary>({ total: 0, quantum_vulnerable: 0, counts: {}, note: '' })
  const [profile, setProfile] = useState('LEGACY')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('Ready to inspect Citizen Secure Records.')
  const [report, setReport] = useState('')
  const [menu, setMenu] = useState(false)

  const refresh = async () => {
    const [i, r, t, p, recs] = await Promise.all([
      api<Finding[]>('/api/inventory'), api<RiskSummary>('/api/risk-summary'),
      api<Task[]>('/api/migration-plan'), api<{profile:string}>('/api/crypto/profile'),
      api<Recommendation[]>('/api/recommendations')
    ])
    setInventory(i); setRisk(r); setTasks(t); setProfile(p.profile); setRecommendations(recs)
  }
  useEffect(() => { refresh().catch(() => setNotice('Backend unavailable. Start the FastAPI service, then refresh.')) }, [])

  const scan = async () => {
    setBusy(true); setNotice('Scanning source and configuration files…')
    try {
      const result = await api<{findings: Finding[]; scanned_files:number}>('/api/scan', { method: 'POST', body: '{}' })
      await refresh(); setNotice(`Scan complete: ${result.findings.length} findings across ${result.scanned_files} files.`)
    } catch (e) { setNotice((e as Error).message) } finally { setBusy(false) }
  }
  const switchProfile = async (next: string) => {
    setBusy(true)
    try {
      await api('/api/crypto/profile', { method: 'POST', body: JSON.stringify({ profile: next }) })
      await refresh(); setNotice(`Crypto profile switched to ${next}. Application interfaces stayed unchanged.`)
    } catch (e) { setNotice((e as Error).message) } finally { setBusy(false) }
  }
  const runVerification = async () => {
    setBusy(true); setNotice('Running provider-level key establishment and signature checks…')
    try {
      const signed = await api<any>('/api/demo/sign', { method:'POST', body: JSON.stringify({message:'Citizen Secure Records verification challenge'}) })
      const verified = await api<any>('/api/demo/verify', { method:'POST', body: JSON.stringify({...signed.data, algorithm:signed.algorithm}) })
      const exchanged = await api<any>('/api/demo/key-exchange', { method:'POST', body:'{}' })
      await refresh(); setNotice(`${signed.algorithm}: signature ${verified.success ? 'verified' : 'failed'}; ${exchanged.algorithm}: shared secret ${exchanged.success ? 'matched' : 'failed'}.`)
    } catch (e) { setNotice((e as Error).message) } finally { setBusy(false) }
  }
  const generateReport = async () => {
    try { const result = await api<{markdown:string}>('/api/report'); setReport(result.markdown); setView('Reports') } catch (e) { setNotice((e as Error).message) }
  }
  const downloadReport = () => {
    const url = URL.createObjectURL(new Blob([report], {type:'text/markdown'})); const a = document.createElement('a')
    a.href=url; a.download='UC-024-migration-report.md'; a.click(); URL.revokeObjectURL(url)
  }
  const progress = tasks.length ? Math.round(tasks.filter(t => t.status === 'Verified').length / tasks.length * 100) : 0
  const ready = inventory.filter(x => x.risk === 'LOWER').length

  const content = useMemo(() => {
    if (view === 'Dashboard') return <Dashboard inventory={inventory} risk={risk} tasks={tasks} progress={progress} ready={ready} scan={scan} busy={busy} />
    if (view === 'Inventory') return <Inventory inventory={inventory} />
    if (view === 'Risk Analysis') return <RiskView inventory={inventory} risk={risk} />
    if (view === 'PQC Recommendations') return <Recommendations recommendations={recommendations} />
    if (view === 'Migration Plan') return <Migration tasks={tasks} refresh={refresh} />
    if (view === 'Crypto-Agility') return <Agility profile={profile} switchProfile={switchProfile} busy={busy} />
    if (view === 'Migration Demo') return <Demo profile={profile} tasks={tasks} switchProfile={switchProfile} verify={runVerification} busy={busy} />
    if (view === 'Reports') return <Reports report={report} generate={generateReport} download={downloadReport} />
    return <Documentation />
  }, [view, inventory, tasks, recommendations, risk, profile, busy, report, progress, ready])

  return <div className="app-shell">
    <aside className={menu ? 'sidebar open' : 'sidebar'}>
      <div className="brand"><div className="brand-mark"><Atom size={21}/></div><div><strong>QUANTUM<span>//</span>SHIFT</strong><small>UC-024 COMMAND CENTER</small></div></div>
      <button className="mobile-close" onClick={() => setMenu(false)} aria-label="Close navigation"><X/></button>
      <nav>{views.map(([name, Icon]) => <button key={name} className={view === name ? 'active' : ''} onClick={() => {setView(name);setMenu(false)}}><Icon size={18}/><span>{name}</span></button>)}</nav>
      <div className="sidebar-foot"><span className="live-dot"/>SYSTEM ONLINE<small>Educational prototype</small></div>
    </aside>
    <main>
      <header><button className="mobile-menu" onClick={() => setMenu(true)} aria-label="Open navigation"><Menu/></button><div><p>Citizen Secure Records</p><h1>{view}</h1></div><div className="header-actions"><span className={`profile-badge ${profile.toLowerCase()}`}><KeyRound size={15}/>{profile}</span><button className="icon-button" onClick={() => refresh()} aria-label="Refresh data"><RefreshCw size={17}/></button></div></header>
      <div className="status-line"><Activity size={15}/><span>{notice}</span></div>
      <div className="page">{content}</div>
      <footer>Educational Prototype — Not a Production Government Security Assessment</footer>
    </main>
  </div>
}

function Dashboard({inventory,risk,tasks,progress,ready,scan,busy}:any) {
  const cards = [
    ['Total Findings', inventory.length, Radar, 'All detected crypto references'],
    ['Quantum-Vulnerable', risk.quantum_vulnerable, ShieldAlert, 'Public-key uses requiring action'],
    ['Critical', risk.counts.CRITICAL || 0, Gauge, 'Highest migration priority'],
    ['Retain / Lower', ready, ShieldCheck, 'Strong symmetric and hash uses'],
  ]
  return <><section className="command-banner"><div><span className="eyebrow">DISCOVER → ASSESS → MIGRATE → VERIFY</span><h2>Cryptographic migration, under control.</h2><p>Map legacy dependencies, choose replacements by cryptographic role, and change providers without rewriting the application.</p></div><button className="primary" onClick={scan} disabled={busy}><Radar size={18}/>{busy?'Scanning…':'Scan Demo Government System'}</button></section>
    <section className="metric-grid">{cards.map(([label,value,Icon,note]:any)=><article className="metric" key={label}><div className="metric-icon"><Icon size={20}/></div><span>{label}</span><strong>{value}</strong><small>{note}</small></article>)}</section>
    <section className="two-col"><article className="panel"><div className="panel-title"><div><span className="eyebrow">RISK POSTURE</span><h3>Exposure by classification</h3></div><span className="micro">RULE-BASED</span></div><RiskBars counts={risk.counts}/></article>
    <article className="panel progress-panel"><div className="panel-title"><div><span className="eyebrow">MIGRATION</span><h3>Readiness trajectory</h3></div><strong>{progress}%</strong></div><div className="progress-ring" style={{'--progress':`${progress*3.6}deg`} as any}><div><strong>{tasks.filter((x:any)=>x.status==='Verified').length}</strong><span>of {tasks.length}<br/>verified</span></div></div><p>{progress===100?'All planned provider migrations passed verification.':'Switch to PQC and run the verification suite to advance tasks.'}</p></article></section>
    <article className="panel"><div className="panel-title"><div><span className="eyebrow">LIVE INVENTORY</span><h3>Citizen Secure Records</h3></div><span className="micro">{inventory.length} FINDINGS</span></div><InventoryTable items={inventory.slice(0,8)}/></article></>
}

function Inventory({inventory}:{inventory:Finding[]}) { return <section><PageIntro label="DISCOVERY" title="Cryptographic inventory" text="Source and configuration evidence with exact file and line provenance."/><article className="panel"><InventoryTable items={inventory}/>{!inventory.length&&<Empty/>}</article></section> }
function InventoryTable({items}:{items:Finding[]}) { return <div className="table-wrap"><table><thead><tr><th>Asset / source</th><th>Algorithm</th><th>Role</th><th>Risk</th><th>Recommendation</th><th>Status</th></tr></thead><tbody>{items.map(x=><tr key={x.id}><td><strong>{x.asset}</strong><small>{x.file}:{x.line}</small></td><td>{x.algorithm}</td><td>{x.role}</td><td><span className={riskClass(x.risk)}>{x.risk}</span></td><td className="target">{x.recommended_replacement}</td><td><span className="status">{x.status}</span></td></tr>)}</tbody></table></div> }
function RiskView({inventory,risk}:{inventory:Finding[];risk:RiskSummary}) { return <><PageIntro label="ASSESS" title="Quantum-risk analysis" text="Transparent classifications distinguish public-key exposure from symmetric encryption and hashing."/><section className="two-col"><article className="panel"><h3>Portfolio distribution</h3><RiskBars counts={risk.counts}/><p className="callout"><ShieldAlert size={18}/>{risk.note}</p></article><article className="panel"><h3>Why the categories differ</h3><div className="explain-list"><div><KeyRound/><p><strong>Public key</strong><span>RSA, ECDH, and ECDSA are threatened by Shor’s algorithm.</span></p></div><div><ShieldCheck/><p><strong>Symmetric</strong><span>AES requires quantum-aware key-length review, not replacement with a KEM.</span></p></div><div><Fingerprint/><p><strong>Hashing</strong><span>SHA-2 remains useful; its role is neither encryption nor signatures.</span></p></div></div></article></section><article className="panel findings-list">{inventory.map(x=><div key={x.id}><span className={riskClass(x.risk)}>{x.risk}</span><p><strong>{x.algorithm} · {x.role}</strong><span>{x.risk_reason}</span></p></div>)}</article></> }
function RiskBars({counts}:{counts:Record<string,number>}) { const max=Math.max(1,...Object.values(counts)); return <div className="risk-bars">{[['CRITICAL','Critical'],['HIGH','High'],['REVIEW','Review'],['LOWER','Lower / retain']].map(([key,label])=><div key={key}><span>{label}</span><div><i className={key.toLowerCase()} style={{width:`${((counts[key]||0)/max)*100}%`}}/></div><strong>{counts[key]||0}</strong></div>)}</div> }
function Recommendations({recommendations}:{recommendations:Recommendation[]}) { return <><PageIntro label="RECOMMEND" title="Role-aware PQC recommendations" text="A KEM replaces key establishment; a signature scheme replaces signatures. Symmetric encryption and hashing remain separate."/><div className="recommend-grid">{recommendations.map(x=><article className="recommend" key={x.inventory_id}><div><span className={riskClass(x.risk)}>{x.priority}</span><small>{x.cryptographic_role}</small></div><div className="mapping"><strong>{x.current_algorithm}</strong><span>→</span><strong>{x.recommended_algorithm}</strong></div><p>{x.reason}</p>{x.alternative_algorithms.length>0&&<p className="alternative">Alternative signature option: {x.alternative_algorithms.join(', ')}</p>}<details><summary>Migration action</summary><p>{x.migration_action}</p></details></article>)}</div>{!recommendations.length&&<Empty/>}</> }
function Migration({tasks,refresh}:{tasks:Task[];refresh:()=>Promise<void>}) { const update=async(id:number,status:string)=>{await api(`/api/migration/${id}`,{method:'PATCH',body:JSON.stringify({status})});await refresh()}; return <><PageIntro label="PLAN" title="Migration plan" text="Prioritized work items maintain dependencies and evidence-backed status."/><div className="task-list">{tasks.map(t=><article className="task" key={t.id}><div className="task-index">{String(t.id).padStart(2,'0')}</div><div className="task-body"><div><span className={riskClass(t.priority)}>{t.priority}</span><span className="micro">{t.asset}</span></div><h3>{t.current_algorithm} <span>→</span> {t.target_algorithm}</h3><p>{t.cryptographic_role} · {t.reason}</p><small>Dependencies: {t.dependencies.join(' • ')}</small></div><select value={t.status} onChange={e=>update(t.id,e.target.value)} aria-label={`Status for ${t.current_algorithm}`}>{['Not Started','Planned','In Progress','Migrated','Verified'].map(s=><option key={s}>{s}</option>)}</select></article>)}</div>{!tasks.length&&<Empty/>}</> }
function Agility({profile,switchProfile,busy}:any) { return <><PageIntro label="ARCHITECTURE" title="Crypto-agility layer" text="Business code depends on stable interfaces. Central configuration selects vetted provider implementations."/><article className="panel architecture"><div className="architecture-flow"><Node icon={LayoutDashboard} title="Citizen Secure Records" note="Application operations"/><b>↓</b><div className="interfaces"><Node icon={Fingerprint} title="SignatureProvider" note="sign • verify"/><Node icon={KeyRound} title="KeyExchangeProvider" note="encapsulate • decapsulate"/></div><b>↓</b><div className="interfaces"><Node icon={Archive} title="Legacy providers" note="ECDSA • ECDH"/><Node icon={Atom} title="PQC providers" note="ML-DSA • ML-KEM"/></div></div><div className="profile-control"><span className="eyebrow">CURRENT PROFILE</span><h3>{profile}</h3><p>Changing this setting swaps the provider factory output. No application-level code changes.</p><ProfileSelector profile={profile} onChange={switchProfile} busy={busy}/><div className="callout"><ShieldCheck size={18}/><span>HYBRID is a real composition: both algorithms run, key secrets are combined with HKDF-SHA-256, and both signatures must verify.</span></div></div></article></> }
function Node({icon:Icon,title,note}:any){return <div className="node"><Icon size={21}/><strong>{title}</strong><span>{note}</span></div>}
function ProfileSelector({profile,onChange,busy}:any){return <div className="segmented" role="group" aria-label="Crypto profile">{['LEGACY','HYBRID','PQC'].map(x=><button key={x} className={profile===x?'selected':''} onClick={()=>onChange(x)} disabled={busy}>{x}</button>)}</div>}
function Demo({profile,tasks,switchProfile,verify,busy}:any){const verified=tasks.length>0&&tasks.every((x:any)=>x.status==='Verified');return <><PageIntro label="MIGRATE + VERIFY" title="Provider migration demonstration" text="Run the exact UC-024 before-and-after scenario against real cryptographic providers."/><div className="demo-flow"><article className="phase before"><span>BEFORE</span><h3>Legacy environment</h3><p>Authentication <b>ECDSA P-256</b></p><p>Key establishment <b>ECDH P-256</b></p><div className="danger-label">HIGH QUANTUM RISK</div></article><div className="flow-arrow">→</div><article className="phase"><span>MIGRATION PLAN</span><h3>Role-aligned change</h3><p>ECDSA <b>ML-DSA-65</b></p><p>ECDH <b>ML-KEM-768</b></p><div className="neutral-label">PROVIDER FACTORY</div></article><div className="flow-arrow">→</div><article className={`phase after ${verified?'done':''}`}><span>AFTER</span><h3>Crypto-agile system</h3><p>Authentication <b>ML-DSA-65</b></p><p>Key establishment <b>ML-KEM-768</b></p><div className="safe-label">{verified?'VERIFIED':'AWAITING VERIFICATION'}</div></article></div><article className="panel demo-console"><div><span className="eyebrow">ACTIVE PROVIDER PROFILE</span><h3>{profile}</h3><ProfileSelector profile={profile} onChange={switchProfile} busy={busy}/></div><div className="console-log"><span>$ provider.verify --scope all</span><p>{verified?'✓ ML-DSA signature valid\n✓ ML-KEM shared secrets match\n✓ Migration tasks VERIFIED':'Switch to PQC, then run cryptographic verification.'}</p></div><button className="primary" onClick={verify} disabled={busy||profile!=='PQC'}><CheckCircle2 size={18}/>{busy?'Verifying…':'Run Verification Tests'}</button></article></>}
function Reports({report,generate,download}:any){return <><PageIntro label="REPORT" title="Migration assessment report" text="Generate an auditable snapshot of inventory, risk, recommendations, progress, verification, remaining risks, and limitations."/><article className="panel report-panel">{report?<><div className="report-actions"><span className="safe-label">GENERATED</span><button className="secondary" onClick={download}>Download .md</button></div><pre>{report}</pre></>:<div className="empty"><FileText size={40}/><h3>No report generated</h3><p>Complete a scan and generate the current assessment.</p><button className="primary" onClick={generate}>Generate Migration Report</button></div>}</article></>}
function Documentation(){return <><PageIntro label="LEARN" title="PQC migration field guide" text="The essential concepts behind UC-024, in operational language."/><div className="docs-grid"><Doc title="The quantum threat"><p>A sufficiently capable fault-tolerant quantum computer could use Shor’s algorithm to solve the mathematical problems protecting RSA and elliptic-curve systems. The date is unknown; long-lived secrets create harvest-now-decrypt-later pressure today.</p></Doc><Doc title="ML-KEM"><p>ML-KEM is for key establishment. A recipient generates a keypair; a sender encapsulates to the public key, producing ciphertext and a shared secret; the recipient decapsulates to recover the same secret.</p></Doc><Doc title="ML-DSA"><p>ML-DSA is for digital signatures. A private key signs a message, and the public key verifies authenticity and integrity. It does not encrypt data.</p></Doc><Doc title="Crypto-agility"><p>Applications call stable cryptographic interfaces while configuration selects providers. Algorithms, parameter sets, and implementations can change without scattering migrations through business code.</p></Doc><Doc title="Inventory first"><p>Organizations cannot safely migrate what they cannot locate. Inventory connects algorithms to files, assets, roles, owners, dependencies, and evidence before a replacement is chosen.</p></Doc><Doc title="Know the boundaries"><ul><li>KEM ≠ digital signature</li><li>KEM ≠ AES</li><li>ML-DSA ≠ encryption</li><li>AES-256-GCM ≠ PQC</li><li>HKDF ≠ encryption</li><li>Hashing ≠ encryption</li></ul></Doc></div></>}
function Doc({title,children}:any){return <article className="panel doc"><h3>{title}</h3>{children}</article>}
function PageIntro({label,title,text}:any){return <div className="page-intro"><span className="eyebrow">{label}</span><h2>{title}</h2><p>{text}</p></div>}
function Empty(){return <div className="empty"><Radar size={38}/><h3>No inventory yet</h3><p>Run the demo scan from the Dashboard to begin.</p></div>}

export default App
