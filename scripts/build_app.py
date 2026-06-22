#!/usr/bin/env python3
"""Inject schedule_data.json into a self-contained single-file web app (index.html).
Minimal, mobile-first day-by-day calendar."""
import sys, os
DATA_PATH = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/dataset/schedule_data.json"
OUT_PATH  = sys.argv[2] if len(sys.argv) > 2 else "/mnt/user-data/outputs/app/index.html"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
data = open(DATA_PATH, encoding="utf-8").read()

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>My Week · IMNU Term IV</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#cfe8f0; --dot:#5a9bb2; --surface:#ffffff; --input:#f3fafc;
  --ink:#16323a; --muted:#50686f; --faint:#7e9aa2; --line:#bcdbe5;
  --accent:#9a2a3a; --accent-soft:#f1dee1; --shadow:rgba(20,48,58,.10);
  --fin:#3b5bdb; --fin-bg:#e8ecfd;
  --mkt:#d9480f; --mkt-bg:#fbe7d8;
  --dna:#0c8c6a; --dna-bg:#d7f1e8;
  --ob:#6741d9;  --ob-bg:#eae4fb;
  --om:#b8730a;  --om-bg:#fbecd2;
  --es:#b02458;  --es-bg:#fbe0ea;
  --gen:#5b6776; --gen-bg:#e9ecf0;
  --hol:#9a6b1f; --hol-bg:#f6e8cf;
  --exam:#b02458; --exam-bg:#fbe0ea;
  --chg:#7c3aed; --chg-bg:#efe7fd;
  --radius:16px;
}
html[data-theme="dark"]{
  --bg:#13171c; --dot:#222a33; --surface:#1b2027; --input:#161b22;
  --ink:#e9eef3; --muted:#9aa6b2; --faint:#6c7681; --line:#2a313a;
  --accent:#e26b80; --accent-soft:#34232a; --shadow:rgba(0,0,0,.4);
  --fin:#7aa2ff; --fin-bg:#1c2740;
  --mkt:#ff9d5c; --mkt-bg:#36230f;
  --dna:#3fd6a8; --dna-bg:#10302a;
  --ob:#ab8cff;  --ob-bg:#241d3e;
  --om:#e3b15c;  --om-bg:#342916;
  --es:#ff7da6;  --es-bg:#371b27;
  --gen:#9aa6b2; --gen-bg:#242a31;
  --hol:#e3b15c; --hol-bg:#342916;
  --exam:#ff7da6; --exam-bg:#371b27;
  --chg:#b794f6; --chg-bg:#2a2140;
}
*{box-sizing:border-box}
html,body{margin:0}
body{
  font-family:"Inter",system-ui,sans-serif; color:var(--ink); background:var(--bg);
  -webkit-font-smoothing:antialiased; line-height:1.5;
  background-image:radial-gradient(circle at 1px 1px,var(--dot) 1px,transparent 0);
  background-size:24px 24px; transition:background-color .25s,color .25s;
}
.wrap{max-width:640px;margin:0 auto;padding:24px 16px 72px}

header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:22px}
.eyebrow{font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:600;margin:0 0 4px}
h1{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:23px;letter-spacing:-.02em;margin:0;line-height:1.05}
.hd-right{display:flex;align-items:center;gap:10px;flex:none}
.week{text-align:right;font-size:10px;color:var(--muted);line-height:1.25}
.week b{display:block;color:var(--ink);font-size:12.5px;font-family:"JetBrains Mono",monospace;white-space:nowrap}
.toggle{width:38px;height:38px;flex:none;display:grid;place-items:center;cursor:pointer;
  border:1.5px solid var(--line);border-radius:11px;background:var(--surface);color:var(--ink);
  transition:border-color .15s,background .15s,transform .08s}
.toggle:hover{border-color:var(--accent)}
.toggle:active{transform:translateY(1px)}
.toggle svg{width:18px;height:18px;display:block}

.lookup{background:var(--surface);border:1.5px solid var(--line);border-radius:var(--radius);padding:18px;
  transition:background-color .25s,border-color .25s}
.lookup h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:600;font-size:17px;margin:0 0 3px}
.lookup p{margin:0 0 14px;color:var(--muted);font-size:13px}
.field{display:flex;gap:9px}
input[type=text]{flex:1;min-width:0;font-family:"JetBrains Mono",monospace;font-size:16px;
  letter-spacing:.05em;text-transform:uppercase;padding:13px 14px;border:1.5px solid var(--line);
  border-radius:11px;background:var(--input);color:var(--ink);outline:none;transition:border-color .15s,box-shadow .15s}
input[type=text]:focus{border-color:var(--accent);box-shadow:0 0 0 4px var(--accent-soft)}
input[type=text]::placeholder{color:var(--faint);letter-spacing:.03em}
button.go{font-family:"Inter";font-weight:600;font-size:14px;color:#fff;background:var(--accent);
  border:none;border-radius:11px;padding:0 18px;cursor:pointer;transition:transform .08s,filter .15s;white-space:nowrap}
button.go:hover{filter:brightness(.92)}
button.go:active{transform:translateY(1px)}
.err{margin-top:12px;font-size:13.5px;color:var(--accent);display:none}
.err.show{display:block}

#result{margin-top:26px;display:none}
#result.show{display:block;animation:rise .4s cubic-bezier(.2,.7,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}

.who{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.who .name{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:21px;letter-spacing:-.02em}
.chip{font-family:"JetBrains Mono",monospace;font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;
  background:var(--accent-soft);color:var(--accent);letter-spacing:.03em}
.who .meta{color:var(--muted);font-size:13px}

/* change notice */
.notice{display:flex;gap:10px;align-items:flex-start;background:var(--chg-bg);
  border:1.5px solid color-mix(in srgb,var(--chg) 32%,transparent);border-left:4px solid var(--chg);
  border-radius:12px;padding:11px 13px;margin-bottom:16px;font-size:13px;line-height:1.45}
.notice .ntag{flex:none;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;
  color:#fff;background:var(--chg);padding:3px 7px;border-radius:5px;margin-top:1px}
.notice .ntxt{color:var(--ink)}

/* legend */
.legend{display:flex;gap:14px;flex-wrap:wrap;margin:0 0 13px;font-size:12px;color:var(--muted)}
.legend .li{display:flex;align-items:center;gap:6px}
.sw{width:14px;height:14px;border-radius:4px;flex:none}
.sw.cls{background:var(--fin-bg);border:1.5px solid var(--fin)}
.sw.today{background:var(--accent-soft);border:2px solid var(--accent)}
.sw.hol{background:var(--hol-bg);border:1.5px solid var(--hol)}
.sw.exam{background:var(--exam-bg);border:1.5px solid var(--exam)}
.sw.chg{background:var(--chg-bg);border:1.5px solid var(--chg)}
.tp{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#fff;
  background:var(--accent);padding:2px 6px;border-radius:5px;margin-top:3px;display:inline-block}

/* grid timetable */
.grid-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;
  border:1.5px solid var(--line);border-radius:var(--radius);background:var(--surface)}
.grid{display:grid;min-width:340px}
.gcorner{position:sticky;left:0;z-index:3;background:var(--surface);border-bottom:1.5px solid var(--line)}
.gh{padding:8px 3px;text-align:center;border-bottom:1.5px solid var(--line);border-left:1px solid var(--line)}
.gh .gd{display:block;font-size:9.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);font-weight:600}
.gh .gn{display:block;font-family:"JetBrains Mono",monospace;font-size:13px;font-weight:700;color:var(--ink);margin-top:1px}
.gh.today{background:var(--accent-soft)} .gh.today .gd,.gh.today .gn{color:var(--accent)}
.gh.hol{background:var(--hol-bg)} .gh.hol .gd{color:var(--hol)}
.gh.exam{background:var(--exam-bg)} .gh.exam .gd{color:var(--exam)}
.gt{position:sticky;left:0;z-index:2;background:var(--surface);font-family:"JetBrains Mono",monospace;
  font-size:9.5px;color:var(--faint);text-align:right;padding:7px 6px;border-bottom:1px solid var(--line);
  line-height:1.35;white-space:nowrap;font-weight:700}
.gt span{display:block;opacity:.65;font-weight:500}
.gc{min-height:48px;border-bottom:1px solid var(--line);border-left:1px solid var(--line);padding:4px}
.gc.today{background:color-mix(in srgb,var(--accent) 6%,transparent)}
.gc.clash{outline:1.5px solid var(--accent);outline-offset:-1.5px;border-radius:6px}
.gblk{display:block;text-decoration:none;border-radius:7px;padding:5px 6px;
  background:var(--cb,var(--gen-bg));color:var(--c,var(--gen));
  border:1px solid color-mix(in srgb,var(--c,var(--gen)) 24%,transparent)}
.gblk+.gblk{margin-top:4px}
.gblk .ga{display:block;font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:12.5px;line-height:1.05}
.gblk .ga small{font-weight:600;font-size:9px;opacity:.8}
.gblk .gr{display:block;font-family:"JetBrains Mono",monospace;font-size:9px;font-weight:700;margin-top:3px;opacity:.85}
.ev-holiday{--c:var(--hol);--cb:var(--hol-bg)}
.ev-exam{--c:var(--exam);--cb:var(--exam-bg)}
.gblk.chg{outline:2px solid var(--chg);outline-offset:1px}
.gblk.out{opacity:.5} .gblk.out .ga{text-decoration:line-through}
.gmv{display:block;font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:.03em;
  color:#fff;background:var(--chg);border-radius:4px;padding:1px 4px;margin-top:3px;text-align:center}
.tag{font-family:"JetBrains Mono",monospace;font-weight:700;font-size:11px;
  color:var(--c,var(--gen));background:var(--cb,var(--gen-bg));padding:1px 6px;border-radius:5px;white-space:nowrap}
.empty-week{background:var(--surface);border:1.5px solid var(--line);border-radius:var(--radius);
  padding:22px;text-align:center;color:var(--muted);font-size:14px}

/* directory (collapsible) */
.dir{margin-top:18px;background:var(--surface);border:1.5px solid var(--line);border-radius:var(--radius);overflow:hidden}
.dir summary{cursor:pointer;list-style:none;padding:14px 16px;font-size:11px;letter-spacing:.12em;
  text-transform:uppercase;color:var(--faint);font-weight:600;display:flex;align-items:center;justify-content:space-between}
.dir summary::-webkit-details-marker{display:none}
.dir summary::after{content:"+";font-size:18px;color:var(--faint)}
.dir[open] summary::after{content:"–"}
.dir summary:hover{color:var(--accent)}
.dir-list{padding:0 16px 6px}
.di{padding:12px 0;border-top:1px solid var(--line)}
.di-h{display:flex;align-items:center;gap:9px}
.di-nm{font-weight:600;font-size:14px}
.di-r{font-size:12.5px;color:var(--muted);margin-top:4px;word-break:break-word}
.di-r a{color:var(--fin);text-decoration:none}
.di-r.meets{font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--faint)}
.di-r.none{font-style:italic}

footer{margin-top:34px;padding-top:16px;border-top:1px solid var(--line);font-size:11.5px;color:var(--faint);text-align:center}

.a-finance{--c:var(--fin);--cb:var(--fin-bg)}
.a-marketing{--c:var(--mkt);--cb:var(--mkt-bg)}
.a-dna{--c:var(--dna);--cb:var(--dna-bg)}
.a-ob{--c:var(--ob);--cb:var(--ob-bg)}
.a-om{--c:var(--om);--cb:var(--om-bg)}
.a-es{--c:var(--es);--cb:var(--es-bg)}
.a-gen{--c:var(--gen);--cb:var(--gen-bg)}

@media (max-width:520px){
  h1{font-size:20px}
  .who .name{font-size:19px}
  .field{flex-wrap:wrap}
  button.go{flex:1;padding:12px 0}
}
@media (prefers-reduced-motion:reduce){
  #result.show{animation:none}
  *{transition:none!important}
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <p class="eyebrow" id="inst"></p>
      <h1>Your week</h1>
    </div>
    <div class="hd-right">
      <div class="week"><span>Week of</span><b id="weekof"></b></div>
      <button class="toggle" id="themeBtn" aria-label="Switch theme"></button>
    </div>
  </header>

  <div class="lookup">
    <h2>Find your schedule</h2>
    <p>Enter your roll number to see your classes this week.</p>
    <div class="field">
      <input type="text" id="roll" placeholder="e.g. 25MBA420" autocomplete="off" spellcheck="false" aria-label="Roll number">
      <button class="go" id="btn">Show</button>
    </div>
    <div class="err" id="err"></div>
  </div>

  <div id="result"></div>

  <footer>Tentative weekly schedule — confirm any room/time changes with the department.</footer>
</div>

<script>
const DATA = __DATA__;

const SUN='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19"/></svg>';
const MOON='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A8.5 8.5 0 1 1 11.2 3a6.5 6.5 0 0 0 9.8 9.8z"/></svg>';
const root = document.documentElement;
function setTheme(t){
  root.setAttribute("data-theme", t);
  try{ localStorage.setItem("imnu-theme", t); }catch(e){}
  const btn = document.getElementById("themeBtn");
  btn.innerHTML = t==="dark" ? SUN : MOON;
  btn.setAttribute("aria-label", t==="dark" ? "Switch to light theme" : "Switch to dark theme");
}
let saved=null; try{ saved=localStorage.getItem("imnu-theme"); }catch(e){}
setTheme(saved || (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark":"light"));
document.getElementById("themeBtn").addEventListener("click",
  ()=> setTheme(root.getAttribute("data-theme")==="dark" ? "light":"dark"));

const AREA_SLUG = {"Finance":"finance","Marketing":"marketing","DnA":"dna","OB":"ob","OM":"om","E & S":"es"};
const slug = a => "a-" + (AREA_SLUG[a] || "gen");
const esc = s => (s==null?"":String(s)).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const $ = id => document.getElementById(id);
const pad = n => String(n).padStart(2,"0");

$("inst").textContent = DATA.meta.institute + " · " + DATA.meta.term;
const wk = new Date(DATA.meta.week_of + "T00:00:00");
const fmt = d => d.toLocaleDateString("en-GB",{day:"numeric",month:"short"});
const fmtDM = ds => new Date(ds+"T00:00:00").toLocaleDateString("en-GB",{day:"numeric",month:"short"});
const wkEnd = new Date(wk); wkEnd.setDate(wk.getDate()+6);
const fmtRange = (a,b)=>{ const dd=d=>d.getDate(), mo=d=>d.toLocaleDateString("en-GB",{month:"short"});
  return a.getMonth()===b.getMonth() ? `${dd(a)}–${dd(b)} ${mo(b)}` : `${dd(a)} ${mo(a)} – ${dd(b)} ${mo(b)}`; };
$("weekof").textContent = fmtRange(wk, wkEnd);

const dayDate = {};
DATA.days.forEach((d,i)=>{ const dt=new Date(wk); dt.setDate(wk.getDate()+i);
  dayDate[d]=`${dt.getFullYear()}-${pad(dt.getMonth()+1)}-${pad(dt.getDate())}`; });
const now=new Date(); const todayStr=`${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
const todayDay = Object.keys(dayDate).find(d=>dayDate[d]===todayStr) || null;

function cleanNotice(t){
  if(!t) return "";
  const m = t.search(/\b(regards|thanks|thank you|warm regards|best regards|sincerely|yours)\b/i);
  let s = (m>=0 ? t.slice(0,m) : t);
  return s.replace(/\s+/g,' ').trim();
}

function lookup(){
  const roll = $("roll").value.trim().toUpperCase();
  $("roll").value = roll;
  const err = $("err"), res = $("result");
  res.classList.remove("show"); err.classList.remove("show");
  if(!roll){ err.textContent="Type your roll number to continue."; err.classList.add("show"); return; }
  const st = DATA.students[roll];
  if(!st){ err.textContent="No student found for "+roll+". Check the roll number and try again."; err.classList.add("show"); return; }
  render(roll, st);
}

function render(roll, st){
  const electives = st.s.map(id => Object.assign({id}, DATA.sections[id]));
  const meetings = [];
  electives.forEach(e => (e.meetings||[]).forEach(m => meetings.push(Object.assign({sec:e}, m))));

  // changes affecting this student
  const myKey = new Set(electives.map(e=>e.abbr+'|'+(e.division||'')));
  const myChanges = (DATA.changes||[]).filter(c=>myKey.has(c.abbr+'|'+(c.division||'')));
  const elBy={}; electives.forEach(e=>{ elBy[e.abbr+'|'+(e.division||'')]=e; });
  const normHM = s => { const m=String(s||'').match(/(\d{1,2})[:.](\d{2})/); return m?parseInt(m[1])+':'+m[2]:''; };
  const sessByHM = hm => DATA.sessions.find(s=>normHM(s.start)===normHM(hm));
  const changeOut=new Set();
  myChanges.forEach(c=>{
    const el=elBy[c.abbr+'|'+(c.division||'')], ses=sessByHM(c.new_hhmm);
    if(el&&ses&&c.new_day&&c.type!=='Cancelled') meetings.push({sec:el,day:c.new_day,session:ses.name,start:ses.start,end:ses.end,changed:'in'});
    if(c.old_day) changeOut.add(c.old_day+'|'+c.abbr+'|'+(c.division||''));
  });
  meetings.forEach(m=>{ if(!m.changed && changeOut.has(m.day+'|'+m.sec.abbr+'|'+(m.sec.division||''))) m.changed='out'; });

  const byDay={}; meetings.forEach(m=>{ (byDay[m.day]=byDay[m.day]||[]).push(m); });
  const sIdx = n => DATA.sessions.findIndex(s=>s.name===n);
  Object.values(byDay).forEach(list=>list.sort((a,b)=>sIdx(a.session)-sIdx(b.session)));
  const evByDay={}; (DATA.events||[]).forEach(e=>{ (evByDay[e.day]=evByDay[e.day]||[]).push(e); });

  let html = `<div class="who"><span class="name">${esc(st.n)}</span><span class="chip">${esc(roll)}</span><span class="meta">${electives.length} electives · ${esc(st.b)}</span></div>`;

  if(myChanges.length){
    const seen=new Set();
    myChanges.forEach(c=>{ const t=cleanNotice(c.raw); if(!t||seen.has(t)) return; seen.add(t);
      html += `<div class="notice"><span class="ntag">${esc(c.type||'Changed')}</span><span class="ntxt">${esc(t)}</span></div>`; });
  }

  // legend
  html += `<div class="legend">
      <span class="li"><span class="sw cls"></span>My Class</span>
      <span class="li"><span class="sw today"></span>Today</span>
      <span class="li"><span class="sw hol"></span>Holiday</span>
      <span class="li"><span class="sw exam"></span>Exam</span>
      ${myChanges.length?'<span class="li"><span class="sw chg"></span>Changed</span>':''}
    </div>`;

  // grid timetable
  const usedDays = DATA.days.filter(d => (byDay[d]&&byDay[d].length) || (evByDay[d]&&evByDay[d].length));
  const usedSess = DATA.sessions.filter(s => meetings.some(m=>m.session===s.name));
  const cellMap = {}; meetings.forEach(m=>{ const k=m.day+'|'+m.session; (cellMap[k]=cellMap[k]||[]).push(m); });
  const shortT = t => String(t||'').replace(/AM$/,'a').replace(/PM$/,'p').replace(/^0/,'');
  const dnum = d => fmtDM(dayDate[d]).split(' ')[0];

  if(!usedDays.length || !usedSess.length){
    html += `<div class="empty-week">No classes scheduled for you this week.</div>`;
  } else {
    const firstSess = usedSess[0].name;
    html += `<div class="grid-wrap"><div class="grid" style="grid-template-columns:auto repeat(${usedDays.length},minmax(54px,1fr))">`;
    html += `<div class="gcorner"></div>`;
    usedDays.forEach(d=>{
      const isT=d===todayDay, ev=evByDay[d]||[];
      const hol=ev.some(e=>e.type==='holiday'), exam=ev.some(e=>e.type==='exam');
      html += `<div class="gh${isT?' today':hol?' hol':exam?' exam':''}"><span class="gd">${d.slice(0,3)}</span><span class="gn">${dnum(d)}</span>${isT?'<span class="tp">Today</span>':''}</div>`;
    });
    usedSess.forEach(s=>{
      html += `<div class="gt">${esc(shortT(s.start))}<span>${esc(shortT(s.end))}</span></div>`;
      usedDays.forEach(d=>{
        const cell = cellMap[d+'|'+s.name]||[];
        const evHere = (s.name===firstSess)?(evByDay[d]||[]):[];
        let inner='';
        evHere.forEach(ev=>{ inner += `<span class="gblk ev-${ev.type==='holiday'?'holiday':'exam'}"><span class="ga">${ev.type==='holiday'?'Holiday':'Exam'}</span><span class="gr">${esc(ev.name)}</span></span>`; });
        cell.forEach(m=>{
          const cc=m.changed==='in'?' chg':m.changed==='out'?' chg out':'';
          const mv=m.changed==='in'?'<span class="gmv">moved here</span>':m.changed==='out'?'<span class="gmv">moved</span>':'';
          inner += `<span class="gblk ${slug(m.sec.area)}${cc}" title="${esc(m.sec.name)} · ${esc(m.sec.room||'')} · ${esc(m.sec.faculty||'')}"><span class="ga">${esc(m.sec.abbr)}<small>${m.sec.division?(' '+esc(m.sec.division)):''}</small></span><span class="gr">${esc(m.sec.room||'TBA')}</span>${mv}</span>`;
        });
        html += `<div class="gc${d===todayDay?' today':''}${cell.length>1?' clash':''}">${inner}</div>`;
      });
    });
    html += `</div></div>`;
  }

  // directory (collapsed by default)
  html += `<details class="dir"><summary>Electives, faculty &amp; rooms</summary><div class="dir-list">`;
  electives.slice().sort((a,b)=>a.abbr.localeCompare(b.abbr)).forEach(e=>{
    const when = (e.meetings||[]).map(m=>`${m.day.slice(0,3)} ${m.start}`).join(", ");
    html += `<div class="di ${slug(e.area)}">
        <div class="di-h"><span class="tag">${esc(e.abbr)}(${esc(e.division||'-')})</span><span class="di-nm">${esc(e.name)}</span></div>
        <div class="di-r">${esc(e.faculty||'—')}${e.email?` · <a href="mailto:${esc(e.email)}">${esc(e.email)}</a>`:''} · Room ${esc(e.room||'TBA')}</div>
        ${when?`<div class="di-r meets">${esc(when)}</div>`:`<div class="di-r meets none">Not scheduled this week</div>`}
      </div>`;
  });
  html += `</div></details>`;

  $("result").innerHTML = html;
  $("result").classList.add("show");
}

$("btn").addEventListener("click", lookup);
$("roll").addEventListener("keydown", e=>{ if(e.key==="Enter") lookup(); });
$("roll").focus();
</script>
</body>
</html>
"""
open(OUT_PATH, "w", encoding="utf-8").write(TEMPLATE.replace("__DATA__", data))
print(f"Wrote {OUT_PATH}")
