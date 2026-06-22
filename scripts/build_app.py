#!/usr/bin/env python3
"""Inject schedule_data.json into a self-contained single-file web app (index.html)."""
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
  --accent:#9a2a3a; --accent-soft:#f1dee1; --shadow:rgba(20,48,58,.14);
  --fin:#3b5bdb; --fin-bg:#e8ecfd;
  --mkt:#d9480f; --mkt-bg:#fbe7d8;
  --dna:#0c8c6a; --dna-bg:#d7f1e8;
  --ob:#6741d9;  --ob-bg:#eae4fb;
  --om:#b8730a;  --om-bg:#fbecd2;
  --es:#b02458;  --es-bg:#fbe0ea;
  --gen:#5b6776; --gen-bg:#e9ecf0;
  --hol:#9a6b1f; --hol-bg:#f6e8cf;
  --exam:#b02458; --exam-bg:#fbe0ea;
  --radius:14px;
}
html[data-theme="dark"]{
  --bg:#13171c; --dot:#222a33; --surface:#1b2027; --input:#161b22;
  --ink:#e9eef3; --muted:#9aa6b2; --faint:#6c7681; --line:#2a313a;
  --accent:#e26b80; --accent-soft:#34232a; --shadow:rgba(0,0,0,.45);
  --fin:#7aa2ff; --fin-bg:#1c2740;
  --mkt:#ff9d5c; --mkt-bg:#36230f;
  --dna:#3fd6a8; --dna-bg:#10302a;
  --ob:#ab8cff;  --ob-bg:#241d3e;
  --om:#e3b15c;  --om-bg:#342916;
  --es:#ff7da6;  --es-bg:#371b27;
  --gen:#9aa6b2; --gen-bg:#242a31;
  --hol:#e3b15c; --hol-bg:#342916;
  --exam:#ff7da6; --exam-bg:#371b27;
}
*{box-sizing:border-box}
html,body{margin:0}
body{
  font-family:"Inter",system-ui,sans-serif; color:var(--ink); background:var(--bg);
  -webkit-font-smoothing:antialiased; line-height:1.5;
  background-image:radial-gradient(circle at 1px 1px,var(--dot) 1px,transparent 0);
  background-size:22px 22px; transition:background-color .25s,color .25s;
}
.wrap{max-width:1080px;margin:0 auto;padding:28px 20px 80px}

header{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;
  padding-bottom:18px;border-bottom:1.5px solid var(--line);margin-bottom:34px;flex-wrap:wrap}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600;margin:0 0 6px}
h1{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:30px;letter-spacing:-.02em;margin:0;line-height:1.05}
.hd-right{display:flex;align-items:center;gap:14px}
.week{text-align:right;font-size:12px;color:var(--muted)}
.week b{display:block;color:var(--ink);font-size:13px}
.toggle{width:40px;height:40px;flex:none;display:grid;place-items:center;cursor:pointer;
  border:1.5px solid var(--line);border-radius:11px;background:var(--surface);color:var(--ink);
  transition:border-color .15s,background .15s,transform .08s}
.toggle:hover{border-color:var(--accent)}
.toggle:active{transform:translateY(1px)}
.toggle svg{width:19px;height:19px;display:block}

.lookup{background:var(--surface);border:1.5px solid var(--line);border-radius:var(--radius);padding:26px;
  transition:background-color .25s,border-color .25s}
.lookup h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:600;font-size:19px;margin:0 0 4px}
.lookup p{margin:0 0 18px;color:var(--muted);font-size:14px}
.field{display:flex;gap:10px;flex-wrap:wrap}
input[type=text]{flex:1;min-width:200px;font-family:"JetBrains Mono",monospace;font-size:18px;
  letter-spacing:.06em;text-transform:uppercase;padding:14px 16px;border:1.5px solid var(--line);
  border-radius:11px;background:var(--input);color:var(--ink);outline:none;transition:border-color .15s,box-shadow .15s}
input[type=text]:focus{border-color:var(--accent);box-shadow:0 0 0 4px var(--accent-soft)}
input[type=text]::placeholder{color:var(--faint);letter-spacing:.04em}
button.go{font-family:"Inter";font-weight:600;font-size:15px;color:#fff;background:var(--accent);
  border:none;border-radius:11px;padding:0 24px;cursor:pointer;transition:transform .08s,filter .15s}
button.go:hover{filter:brightness(.92)}
button.go:active{transform:translateY(1px)}
.err{margin-top:14px;font-size:14px;color:var(--accent);display:none}
.err.show{display:block}

#result{margin-top:34px;display:none}
#result.show{display:block;animation:rise .45s cubic-bezier(.2,.7,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}

.who{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:22px}
.who .name{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:26px;letter-spacing:-.02em}
.chip{font-family:"JetBrains Mono",monospace;font-size:12px;font-weight:700;padding:4px 9px;border-radius:7px;
  background:var(--accent-soft);color:var(--accent);letter-spacing:.04em}
.who .meta{color:var(--muted);font-size:14px}

.section-label{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);font-weight:600;margin:30px 0 12px}

.legend{display:flex;gap:16px;flex-wrap:wrap;margin:0 0 14px;font-size:12.5px;color:var(--muted)}
.legend .li{display:flex;align-items:center;gap:7px}
.sw{width:15px;height:15px;border-radius:4px;flex:none}
.sw.cls{background:color-mix(in srgb,var(--ink) 8%,transparent);border:1.5px solid color-mix(in srgb,var(--ink) 32%,transparent)}
.sw.today{background:var(--accent-soft);border:2px solid var(--accent)}
.sw.hol{background:var(--hol-bg);border:1.5px solid var(--hol)}
.sw.exam{background:var(--exam-bg);border:1.5px solid var(--exam)}

.events{display:flex;gap:9px;flex-wrap:wrap;margin:0 0 18px}
.evp{display:inline-flex;align-items:center;gap:8px;font-size:12.5px;font-weight:500;padding:7px 12px;border-radius:10px;border:1.5px solid}
.evp .d{font-family:"JetBrains Mono",monospace;font-weight:700;font-size:11.5px}
.evp.hol{background:var(--hol-bg);color:var(--hol);border-color:color-mix(in srgb,var(--hol) 35%,transparent)}
.evp.exam{background:var(--exam-bg);color:var(--exam);border-color:color-mix(in srgb,var(--exam) 35%,transparent)}
.evp.none{background:transparent;color:var(--faint);border:1.5px dashed var(--line);font-style:italic}

.tg{display:inline-block;margin-left:7px;font-size:8.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
  padding:2px 6px;border-radius:5px;background:var(--accent);color:#fff;vertical-align:middle}

.grid-wrap{overflow-x:auto}
.grid{display:grid;gap:6px;min-width:560px}
.gh{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:600;padding:0 4px 8px;text-align:center}
.gh.today{color:var(--accent)}
.gh.hol{color:var(--hol)}
.gt{font-family:"JetBrains Mono",monospace;font-size:10.5px;color:var(--faint);text-align:right;padding:10px 10px 0 0;white-space:nowrap;line-height:1.35}
.cell{min-height:46px;border-radius:10px;border:1.5px dashed transparent}
.cell.empty{border-color:var(--line)}
.cell.todaycol{background:color-mix(in srgb,var(--accent) 7%,transparent)}
.cell.clash{outline:2px solid var(--accent);outline-offset:1px;border-radius:11px}
.blk{display:block;text-decoration:none;border-radius:10px;padding:8px 9px;border:1px solid transparent;transition:transform .1s,box-shadow .1s;
  background:var(--cb);color:var(--c);border-color:color-mix(in srgb,var(--c) 26%,transparent)}
.blk+.blk{margin-top:5px}
.blk:hover{transform:translateY(-1px);box-shadow:0 4px 14px var(--shadow)}
.blk .ab{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:15px;letter-spacing:-.01em;line-height:1}
.blk .rm{font-family:"JetBrains Mono",monospace;font-size:11px;font-weight:700;margin-top:5px;opacity:.85}
.blk .rm small{font-weight:500;opacity:.8}
.ev-holiday{--c:var(--hol);--cb:var(--hol-bg)}
.ev-exam{--c:var(--exam);--cb:var(--exam-bg)}

.agenda{display:none}
.day-grp{margin-bottom:18px}
.day-grp h3{font-family:"Bricolage Grotesque",sans-serif;font-size:15px;margin:0 0 8px;padding-bottom:6px;border-bottom:1.5px solid var(--line)}
.day-grp.today h3{color:var(--accent)}
.arow{display:flex;gap:12px;align-items:flex-start;padding:9px 0}
.arow .t{font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--muted);width:64px;flex:none;padding-top:9px;line-height:1.3}
.arow .blk{flex:1}
.arow .blk .nm{font-size:12.5px;font-weight:500;color:inherit;opacity:.95;margin-top:3px}

.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.card{background:var(--surface);border:1.5px solid var(--line);border-radius:var(--radius);padding:16px;border-left-width:4px;
  transition:background-color .25s,border-color .25s;border-left-color:var(--c)}
.card .top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:10px}
.card .nm{font-weight:600;font-size:15px;line-height:1.3}
.badge{font-size:10px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:3px 7px;border-radius:6px;white-space:nowrap;flex:none;
  background:var(--cb);color:var(--c)}
.card .row{display:flex;gap:8px;font-size:13px;color:var(--muted);margin-top:5px;align-items:baseline}
.card .row .k{color:var(--faint);width:54px;flex:none;font-size:11px;text-transform:uppercase;letter-spacing:.06em;padding-top:1px}
.card .row a{color:var(--fin);text-decoration:none;word-break:break-all}
.card .pill{font-family:"JetBrains Mono",monospace;font-size:12px;font-weight:700;color:var(--ink)}
.card .none{font-size:12px;color:var(--faint);font-style:italic;margin-top:6px}

footer{margin-top:48px;padding-top:18px;border-top:1px solid var(--line);font-size:12px;color:var(--faint);
  display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}

.a-finance{--c:var(--fin);--cb:var(--fin-bg)}
.a-marketing{--c:var(--mkt);--cb:var(--mkt-bg)}
.a-dna{--c:var(--dna);--cb:var(--dna-bg)}
.a-ob{--c:var(--ob);--cb:var(--ob-bg)}
.a-om{--c:var(--om);--cb:var(--om-bg)}
.a-es{--c:var(--es);--cb:var(--es-bg)}
.a-gen{--c:var(--gen);--cb:var(--gen-bg)}

@media (max-width:719px){
  .grid-wrap{display:none}
  .agenda{display:block}
  h1{font-size:24px}
  .who .name{font-size:22px}
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
      <h1>Your week, at a glance</h1>
    </div>
    <div class="hd-right">
      <div class="week"><span>Schedule for</span><b id="weekof"></b></div>
      <button class="toggle" id="themeBtn" aria-label="Switch theme"></button>
    </div>
  </header>

  <div class="lookup">
    <h2>Find your schedule</h2>
    <p>Enter your roll number to see where, when, and with whom your electives meet this week.</p>
    <div class="field">
      <input type="text" id="roll" placeholder="e.g. 25MBA106" autocomplete="off" spellcheck="false" aria-label="Roll number">
      <button class="go" id="btn">Show my week</button>
    </div>
    <div class="err" id="err"></div>
  </div>

  <div id="result"></div>

  <footer>
    <span id="ft-term"></span>
    <span>Tentative weekly schedule — confirm room/time changes with the department.</span>
  </footer>
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
const fmtDay = ds => new Date(ds+"T00:00:00").toLocaleDateString("en-GB",{weekday:"short",day:"numeric",month:"short"});
const wkEnd = new Date(wk); wkEnd.setDate(wk.getDate()+6);
$("weekof").textContent = fmt(wk) + " – " + fmt(wkEnd) + ", " + wk.getFullYear();
$("ft-term").textContent = DATA.meta.institute + " · " + DATA.meta.term;

// today + events (global, not student-specific)
const dayDate = {};
DATA.days.forEach((d,i)=>{ const dt=new Date(wk); dt.setDate(wk.getDate()+i);
  dayDate[d]=`${dt.getFullYear()}-${pad(dt.getMonth()+1)}-${pad(dt.getDate())}`; });
const now=new Date(); const todayStr=`${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
const todayDay = Object.keys(dayDate).find(d=>dayDate[d]===todayStr) || null;
const eventsByDay = {}; (DATA.events||[]).forEach(e=>{ (eventsByDay[e.day]=eventsByDay[e.day]||[]).push(e); });

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

function legendAndEvents(){
  let h = `<div class="legend">
      <span class="li"><span class="sw cls"></span>My Class</span>
      <span class="li"><span class="sw today"></span>Today</span>
      <span class="li"><span class="sw hol"></span>Holiday</span>
      <span class="li"><span class="sw exam"></span>Exam</span>
    </div>`;
  const evs = DATA.events||[];
  let strip = evs.filter(e=>e.type==="holiday")
      .map(e=>`<span class="evp hol"><span class="d">${fmtDay(e.date)}</span> ${esc(e.name)}</span>`).join("");
  const exams = evs.filter(e=>e.type==="exam");
  strip += exams.length
      ? exams.map(e=>`<span class="evp exam"><span class="d">${fmtDay(e.date)}</span> ${esc(e.name)}</span>`).join("")
      : `<span class="evp none">No exams this week</span>`;
  return h + `<div class="events">${strip}</div>`;
}

function render(roll, st){
  const electives = st.s.map(id => Object.assign({id}, DATA.sections[id]));
  const meetings = [];
  electives.forEach(e => (e.meetings||[]).forEach(m => meetings.push(Object.assign({sec:e}, m))));
  const eventDays = new Set(Object.keys(eventsByDay));
  const usedDays = DATA.days.filter(d => meetings.some(m=>m.day===d) || eventDays.has(d));
  const usedSess = DATA.sessions.filter(s => meetings.some(m=>m.session===s.name));
  const cellMap = {};
  meetings.forEach(m => { const k=m.day+"|"+m.session; (cellMap[k]=cellMap[k]||[]).push(m); });

  let html = `<div class="who">
      <span class="name">${esc(st.n)}</span>
      <span class="chip">${esc(roll)}</span>
      <span class="meta">${electives.length} electives · ${esc(st.b)} batch</span>
    </div>`;

  html += `<div class="section-label">This week</div>`;
  html += legendAndEvents();

  if(usedDays.length===0){
    html += `<p style="color:var(--muted)">No classes are scheduled for you this week.</p>`;
  } else {
    const firstSess = usedSess.length ? usedSess[0].name : null;
    // grid (desktop)
    html += `<div class="grid-wrap"><div class="grid" style="grid-template-columns:auto repeat(${usedDays.length},1fr)">`;
    html += `<div></div>` + usedDays.map(d=>{
        const hol = (eventsByDay[d]||[]).some(e=>e.type==="holiday");
        const cls = (d===todayDay?"today ":"") + (hol?"hol":"");
        return `<div class="gh ${cls}">${d.slice(0,3)}${d===todayDay?'<span class="tg">Today</span>':''}</div>`;
      }).join("");
    usedSess.forEach(s=>{
      html += `<div class="gt">${esc(s.start)}<br>${esc(s.end||"")}</div>`;
      usedDays.forEach(d=>{
        const list = cellMap[d+"|"+s.name]||[];
        const evHere = (s.name===firstSess) ? (eventsByDay[d]||[]) : [];
        const todayc = d===todayDay ? " todaycol":"";
        const clash = list.length>1 ? " clash":"";
        if(!list.length && !evHere.length){ html += `<div class="cell empty${todayc}"></div>`; return; }
        html += `<div class="cell${clash}${todayc}">`
              + evHere.map(evBlk).join("")
              + list.map(m=>blk(m.sec)).join("") + `</div>`;
      });
    });
    html += `</div></div>`;

    // agenda (mobile)
    html += `<div class="agenda">`;
    usedDays.forEach(d=>{
      const isToday = d===todayDay;
      html += `<div class="day-grp${isToday?' today':''}"><h3>${d}${isToday?'<span class="tg">Today</span>':''}</h3>`;
      (eventsByDay[d]||[]).forEach(ev=>{
        html += `<div class="arow"><div class="t">All day</div>
                 <span class="blk ev-${ev.type==='holiday'?'holiday':'exam'}">
                   <span class="ab">${ev.type==='holiday'?'Holiday':'Exam'}</span>
                   <span class="nm">${esc(ev.name)}</span></span></div>`;
      });
      meetings.filter(m=>m.day===d)
        .sort((a,b)=>usedSess.findIndex(s=>s.name===a.session)-usedSess.findIndex(s=>s.name===b.session))
        .forEach(m=>{
          html += `<div class="arow"><div class="t">${esc(m.start)}<br>${esc(m.end||"")}</div>
                   <a class="blk ${slug(m.sec.area)}" href="#e-${m.sec.id}">
                     <span class="ab">${esc(m.sec.abbr)}(${esc(m.sec.division||"-")})</span>
                     <span class="nm">${esc(m.sec.name)}</span>
                     <span class="rm">${esc(m.sec.room||"TBA")} · ${esc(m.sec.faculty||"")}</span>
                   </a></div>`;
        });
      html += `</div>`;
    });
    html += `</div>`;
  }

  // electives directory
  html += `<div class="section-label">Your electives, faculty &amp; rooms</div><div class="cards">`;
  electives.slice().sort((a,b)=>a.abbr.localeCompare(b.abbr)).forEach(e=>{
    const when = (e.meetings||[]).map(m=>`${m.day.slice(0,3)} ${m.start}`).join(", ");
    html += `<div class="card ${slug(e.area)}" id="e-${e.id}">
      <div class="top"><div class="nm">${esc(e.name)}</div><span class="badge">${esc(e.area)}</span></div>
      <div class="row"><span class="k">Section</span><span class="pill">${esc(e.abbr)}(${esc(e.division||"-")})</span></div>
      <div class="row"><span class="k">Faculty</span><span>${esc(e.faculty||"—")}</span></div>
      ${e.email?`<div class="row"><span class="k">Email</span><a href="mailto:${esc(e.email)}">${esc(e.email)}</a></div>`:""}
      <div class="row"><span class="k">Room</span><span class="pill">${esc(e.room||"TBA")}</span></div>
      ${when?`<div class="row"><span class="k">Meets</span><span>${esc(when)}</span></div>`:`<div class="none">Not scheduled this week</div>`}
    </div>`;
  });
  html += `</div>`;

  $("result").innerHTML = html;
  $("result").classList.add("show");
}

function blk(s){
  return `<a class="blk ${slug(s.area)}" href="#e-${s.id}" title="${esc(s.name)} — ${esc(s.faculty||"")}">
      <span class="ab">${esc(s.abbr)}</span>
      <span class="rm">${esc(s.room||"TBA")} <small>${esc(s.division?"Div "+s.division:"")}</small></span>
    </a>`;
}
function evBlk(ev){
  return `<span class="blk ev-${ev.type==='holiday'?'holiday':'exam'}">
      <span class="ab">${ev.type==='holiday'?'Holiday':'Exam'}</span>
      <span class="rm">${esc(ev.name)}</span></span>`;
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
