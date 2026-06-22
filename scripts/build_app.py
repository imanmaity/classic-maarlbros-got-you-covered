#!/usr/bin/env python3
"""Inject schedule_data.json into a self-contained single-file web app (index.html).
Warm-gradient weekly grid calendar, mobile-first."""
import sys, os
DATA_PATH = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/dataset/schedule_data.json"
OUT_PATH  = sys.argv[2] if len(sys.argv) > 2 else "/mnt/user-data/outputs/app/index.html"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
data = open(DATA_PATH, encoding="utf-8").read()

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>My Week · IMNU Term IV</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#fcf2e4; --surface:#fffaf3; --card:rgba(255,252,247,.86); --input:#fdf4e8;
  --ink:#2a2018; --muted:#7a6a58; --faint:#a8967f; --line:#ecdcc8;
  --accent:#e07a2a; --accent-soft:#fbe6d2; --ring:#e8902a; --shadow:rgba(150,90,30,.16);
  --grad:linear-gradient(95deg,#ff9a76 0%,#ff9e3d 50%,#ffce4a 100%);
  --blobA:.16;
  --fin:#3b5bdb; --fin-bg:#e8ecfd;
  --mkt:#d9480f; --mkt-bg:#fbe7d8;
  --dna:#0c8c6a; --dna-bg:#d7f1e8;
  --ob:#6741d9;  --ob-bg:#eae4fb;
  --om:#b8730a;  --om-bg:#fbecd2;
  --es:#b02458;  --es-bg:#fbe0ea;
  --gen:#5b6776; --gen-bg:#e9ecf0;
  --hol:#b5791f; --hol-bg:#f7e6c8;
  --exam:#c0356a; --exam-bg:#fbe0ea;
  --chg:#7c3aed; --chg-bg:#efe7fd;
  --pp:#dc2626; --pp-bg:#fbe3e3;
  --radius:18px;
}
html[data-theme="dark"]{
  --bg:#15110c; --surface:#1e1914; --card:rgba(30,25,20,.72); --input:#1b1610;
  --ink:#f3ece2; --muted:#b3a796; --faint:#7e7264; --line:#332b22;
  --accent:#ff9e3d; --accent-soft:#3a2a16; --ring:#ffb24a; --shadow:rgba(0,0,0,.5);
  --grad:linear-gradient(95deg,#ff8f6b 0%,#ff9e3d 50%,#ffce4a 100%);
  --blobA:.4;
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
  --pp:#f87171; --pp-bg:#3a1d1d;
}
*{box-sizing:border-box}
html,body{margin:0}
body{font-family:"Inter",system-ui,sans-serif;color:var(--ink);background:var(--bg);
  -webkit-font-smoothing:antialiased;line-height:1.5;min-height:100vh;transition:background-color .25s,color .25s}
body::before{content:"";position:fixed;inset:-10%;z-index:-1;pointer-events:none;
  background:
    radial-gradient(34% 27% at 12% 9%, rgba(255,178,74,var(--blobA)), transparent 70%),
    radial-gradient(38% 30% at 88% 5%, rgba(255,126,116,calc(var(--blobA)*.85)), transparent 72%),
    radial-gradient(42% 34% at 86% 95%, rgba(255,206,90,var(--blobA)), transparent 70%),
    radial-gradient(34% 28% at 7% 93%, rgba(255,150,80,calc(var(--blobA)*.8)), transparent 72%);
  filter:blur(8px)}
.wrap{max-width:640px;margin:0 auto;padding:24px 16px 72px}

header{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:22px}
.eyebrow{font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:700;margin:0 0 4px}
h1{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:25px;letter-spacing:-.02em;margin:0;line-height:1.02}
.hd-right{display:flex;align-items:center;gap:10px;flex:none}
.week{text-align:right;font-size:10px;color:var(--muted);line-height:1.25}
.week b{display:block;color:var(--ink);font-size:12.5px;font-family:"JetBrains Mono",monospace;white-space:nowrap}
.toggle{width:38px;height:38px;flex:none;display:grid;place-items:center;cursor:pointer;
  border:1.5px solid var(--line);border-radius:11px;background:var(--surface);color:var(--ink);transition:border-color .15s,transform .08s}
.toggle:hover{border-color:var(--accent)} .toggle:active{transform:translateY(1px)} .toggle svg{width:18px;height:18px}

.lookup{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:18px;
  backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);box-shadow:0 10px 34px var(--shadow)}
.lookup h2{font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:17px;margin:0 0 3px}
.lookup p{margin:0 0 14px;color:var(--muted);font-size:13px}
.field{display:flex;gap:9px}
input[type=text]{flex:1;min-width:0;font-family:"JetBrains Mono",monospace;font-size:16px;letter-spacing:.05em;
  text-transform:uppercase;padding:13px 14px;border:1.5px solid var(--line);border-radius:12px;background:var(--input);
  color:var(--ink);outline:none;transition:border-color .15s,box-shadow .15s}
input[type=text]:focus{border-color:var(--accent);box-shadow:0 0 0 4px var(--accent-soft)}
input[type=text]::placeholder{color:var(--faint)}
button.go{font-weight:700;font-size:14px;color:#fff;border:none;border-radius:12px;padding:0 20px;cursor:pointer;
  background:var(--grad);transition:transform .08s,filter .15s;white-space:nowrap}
button.go:hover{filter:brightness(1.04)} button.go:active{transform:translateY(1px)}
.err{margin-top:12px;font-size:13.5px;color:var(--exam);display:none} .err.show{display:block}

#result{margin-top:24px;display:none}
#result.show{display:block;animation:rise .4s cubic-bezier(.2,.7,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}

.who{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.who .name{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:22px;letter-spacing:-.02em}
.chip{font-family:"JetBrains Mono",monospace;font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;background:var(--accent-soft);color:var(--accent)}
.who .meta{color:var(--muted);font-size:13px}

.notice{display:flex;gap:10px;align-items:flex-start;background:var(--chg-bg);
  border:1px solid color-mix(in srgb,var(--chg) 32%,transparent);border-left:4px solid var(--chg);
  border-radius:13px;padding:11px 13px;margin-bottom:15px;font-size:13px;line-height:1.45}
.notice .ntag{flex:none;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#fff;background:var(--chg);padding:3px 7px;border-radius:5px;margin-top:1px}
.notice .ntxt{color:var(--ink)}

.legend{display:flex;gap:14px;flex-wrap:wrap;margin:0 0 12px;font-size:12px;color:var(--muted)}
.legend .li{display:flex;align-items:center;gap:6px}
.sw{width:14px;height:14px;border-radius:4px;flex:none}
.sw.cls{background:var(--fin-bg);border:1.5px solid var(--fin)}
.sw.today{background:transparent;border:2px solid var(--ring);border-radius:50%}
.sw.hol{background:var(--hol-bg);border:1.5px solid var(--hol)}
.sw.exam{background:var(--exam-bg);border:1.5px solid var(--exam)}
.sw.chg{background:var(--chg-bg);border:1.5px solid var(--chg)}

.ic{width:.82em;height:.82em;display:inline-block;vertical-align:-1px;margin-right:3px;flex:none}

/* glass calendar card */
.calcard{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:8px;
  backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);box-shadow:0 14px 44px var(--shadow);min-width:336px}
.grid-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:22px}

/* gradient weekday band */
.weekhead{display:grid;width:100%;margin-bottom:6px}
.whbar{grid-row:1;background:var(--grad);border-radius:13px;align-self:stretch;box-shadow:0 5px 16px rgba(240,150,50,.35)}
.whcorner{grid-row:1;grid-column:1}
.wh{grid-row:1;position:relative;z-index:1;text-align:center;padding:8px 1px 7px;color:#fff}
.wh .whd{display:block;font-size:9.5px;font-weight:800;letter-spacing:.04em;text-transform:uppercase;opacity:.96}
.wh .whn{display:inline-grid;place-items:center;min-width:23px;height:23px;margin-top:3px;
  font-family:"JetBrains Mono",monospace;font-weight:700;font-size:12.5px;line-height:1}
.wh.today .whn{border:2px solid #fff;border-radius:999px;box-shadow:0 0 0 3px rgba(255,255,255,.18)}

/* session grid */
.grid{display:grid;width:100%}
.gt{font-family:"JetBrains Mono",monospace;font-size:9px;color:var(--faint);text-align:right;
  padding:7px 6px;border-top:1px solid var(--line);line-height:1.3;white-space:nowrap;font-weight:700}
.gt span{display:block;opacity:.6;font-weight:500}
.gc{min-height:46px;border-top:1px solid var(--line);border-left:1px solid var(--line);padding:4px}
.gc.today{background:color-mix(in srgb,var(--ring) 13%,transparent)}
.gc.hol{background:color-mix(in srgb,var(--hol) 12%,transparent)}
.gc.exam{background:color-mix(in srgb,var(--exam) 10%,transparent)}
.gc.clash{outline:1.5px solid var(--accent);outline-offset:-1.5px;border-radius:7px}
.gblk{display:block;text-decoration:none;border-radius:8px;padding:5px 6px;
  background:var(--cb,var(--gen-bg));color:var(--c,var(--gen));border:1px solid color-mix(in srgb,var(--c,var(--gen)) 24%,transparent)}
.gblk+.gblk{margin-top:4px}
.gblk .ga{display:block;font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:12px;line-height:1.05}
.gblk .ga small{font-weight:600;font-size:9px;opacity:.85}
.gblk .gr{display:flex;align-items:center;font-family:"JetBrains Mono",monospace;font-size:9px;font-weight:700;margin-top:3px;opacity:.9}
.gblk.chg{outline:2px solid var(--chg);outline-offset:1px}
.gblk.out{opacity:.5} .gblk.out .ga{text-decoration:line-through}
.gmv{display:block;font-size:8px;font-weight:700;text-transform:uppercase;letter-spacing:.03em;color:#fff;background:var(--chg);border-radius:4px;padding:1px 4px;margin-top:3px;text-align:center}
.gblk.pp{background:var(--pp-bg);color:var(--pp);border:1px solid color-mix(in srgb,var(--pp) 40%,transparent);outline:2px solid var(--pp);outline-offset:1px}
.gblk.pp .ga{text-decoration:line-through}
.ppbadge{display:block;font-size:7.5px;font-weight:700;text-transform:uppercase;letter-spacing:.02em;color:#fff;background:var(--pp);border-radius:4px;padding:1px 4px;margin-top:3px;text-align:center}
.notice.red{background:var(--pp-bg);border-color:color-mix(in srgb,var(--pp) 38%,transparent);border-left-color:var(--pp)}
.notice.red .ntag{background:var(--pp)}
.sw.pp{background:var(--pp-bg);border:1.5px solid var(--pp);border-radius:4px}

/* event chips + note (image-style) */
.belowcal{display:flex;flex-wrap:wrap;gap:9px;margin-top:14px}
.note{flex:1 1 150px;background:var(--card);border:1px solid var(--line);border-radius:13px;padding:11px 13px;
  font-size:12.5px;color:var(--muted);box-shadow:0 8px 26px var(--shadow);backdrop-filter:blur(8px)}
.note b{color:var(--ink);font-weight:700}
.chip2{display:flex;align-items:center;gap:9px;background:var(--card);border:1px solid var(--line);border-radius:13px;
  padding:6px 13px 6px 6px;box-shadow:0 8px 26px var(--shadow);backdrop-filter:blur(8px)}
.chip2 .num{display:grid;place-items:center;width:34px;height:34px;border-radius:9px;color:#fff;
  font-family:"JetBrains Mono",monospace;font-weight:700;font-size:14px;flex:none}
.chip2.hol .num{background:var(--hol)} .chip2.exam .num{background:var(--exam)}
.chip2 .typ{display:block;font-size:9px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700}
.chip2 .lab{font-size:13px;font-weight:600;color:var(--ink)}

.empty-week{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:22px;text-align:center;color:var(--muted);font-size:14px}

/* directory */
.dir{margin-top:16px;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;backdrop-filter:blur(8px)}
.dir summary{cursor:pointer;list-style:none;padding:14px 16px;font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--faint);font-weight:700;display:flex;align-items:center;justify-content:space-between}
.dir summary::-webkit-details-marker{display:none}
.dir summary::after{content:"+";font-size:18px;color:var(--faint)} .dir[open] summary::after{content:"–"}
.dir summary:hover{color:var(--accent)}
.dir-list{padding:0 16px 6px}
.di{padding:12px 0;border-top:1px solid var(--line)}
.di-h{display:flex;align-items:center;gap:9px}
.di-nm{font-weight:700;font-size:14px}
.di-r{font-size:12.5px;color:var(--muted);margin-top:4px;word-break:break-word;display:flex;align-items:center;flex-wrap:wrap}
.di-r a{color:var(--fin);text-decoration:none}
.di-r.meets{font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--faint)}

.tag{display:inline-flex;align-items:center;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:11px;
  color:var(--c,var(--gen));background:var(--cb,var(--gen-bg));padding:2px 7px;border-radius:6px;white-space:nowrap}

footer{margin-top:30px;padding-top:16px;border-top:1px solid var(--line);font-size:11.5px;color:var(--faint);text-align:center}

.a-finance{--c:var(--fin);--cb:var(--fin-bg)}
.a-marketing{--c:var(--mkt);--cb:var(--mkt-bg)}
.a-dna{--c:var(--dna);--cb:var(--dna-bg)}
.a-ob{--c:var(--ob);--cb:var(--ob-bg)}
.a-om{--c:var(--om);--cb:var(--om-bg)}
.a-es{--c:var(--es);--cb:var(--es-bg)}
.a-gen{--c:var(--gen);--cb:var(--gen-bg)}

@media (max-width:520px){ h1{font-size:21px} .who .name{font-size:20px} .field{flex-wrap:wrap} button.go{flex:1;padding:12px 0} }
@media (prefers-reduced-motion:reduce){ #result.show{animation:none} *{transition:none!important} }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div><p class="eyebrow" id="inst"></p><h1>Your week</h1></div>
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
const PERSON='<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="3.4"/><path d="M5 20c0-3.5 3.1-5.5 7-5.5s7 2 7 5.5"/></svg>';
const ROOM='<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21V4.5A1.5 1.5 0 0 1 5.5 3h9A1.5 1.5 0 0 1 16 4.5V21"/><path d="M3 21h18M16 8h3.5A1.5 1.5 0 0 1 21 9.5V21"/><circle cx="12" cy="12.5" r="1"/></svg>';

const root=document.documentElement;
function setTheme(t){ root.setAttribute("data-theme",t); try{localStorage.setItem("imnu-theme",t);}catch(e){}
  const b=document.getElementById("themeBtn"); b.innerHTML=t==="dark"?SUN:MOON;
  b.setAttribute("aria-label",t==="dark"?"Switch to light theme":"Switch to dark theme"); }
let saved=null; try{saved=localStorage.getItem("imnu-theme");}catch(e){}
setTheme(saved || (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark":"light"));
document.getElementById("themeBtn").addEventListener("click",()=>setTheme(root.getAttribute("data-theme")==="dark"?"light":"dark"));

const AREA_SLUG={"Finance":"finance","Marketing":"marketing","DnA":"dna","OB":"ob","OM":"om","E & S":"es"};
const slug=a=>"a-"+(AREA_SLUG[a]||"gen");
const esc=s=>(s==null?"":String(s)).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const $=id=>document.getElementById(id);
const pad=n=>String(n).padStart(2,"0");

$("inst").textContent=DATA.meta.institute+" · "+DATA.meta.term;
const wk=new Date(DATA.meta.week_of+"T00:00:00");
const fmt=d=>d.toLocaleDateString("en-GB",{day:"numeric",month:"short"});
const fmtDM=ds=>new Date(ds+"T00:00:00").toLocaleDateString("en-GB",{day:"numeric",month:"short"});
const wkEnd=new Date(wk); wkEnd.setDate(wk.getDate()+6);
const fmtRange=(a,b)=>{const dd=d=>d.getDate(),mo=d=>d.toLocaleDateString("en-GB",{month:"short"});
  return a.getMonth()===b.getMonth()?`${dd(a)}–${dd(b)} ${mo(b)}`:`${dd(a)} ${mo(a)} – ${dd(b)} ${mo(b)}`;};
$("weekof").textContent=fmtRange(wk,wkEnd);

const dayDate={};
DATA.days.forEach((d,i)=>{const dt=new Date(wk);dt.setDate(wk.getDate()+i);
  dayDate[d]=`${dt.getFullYear()}-${pad(dt.getMonth()+1)}-${pad(dt.getDate())}`;});
const now=new Date(); const todayStr=`${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
const todayDay=Object.keys(dayDate).find(d=>dayDate[d]===todayStr)||null;

function cleanNotice(t){ if(!t) return "";
  const m=t.search(/\b(regards|thanks|thank you|warm regards|best regards|sincerely|yours)\b/i);
  return (m>=0?t.slice(0,m):t).replace(/\s+/g,' ').trim(); }

function lookup(){
  const roll=$("roll").value.trim().toUpperCase(); $("roll").value=roll;
  const err=$("err"),res=$("result"); res.classList.remove("show"); err.classList.remove("show");
  if(!roll){ err.textContent="Type your roll number to continue."; err.classList.add("show"); return; }
  const st=DATA.students[roll];
  if(!st){ err.textContent="No student found for "+roll+". Check the roll number and try again."; err.classList.add("show"); return; }
  render(roll,st);
}

const TCOL=44;
function render(roll,st){
  const electives=st.s.map(id=>Object.assign({id},DATA.sections[id]));
  const meetings=[];
  electives.forEach(e=>(e.meetings||[]).forEach(m=>meetings.push(Object.assign({sec:e},m))));

  // match emails that drop "&" (SDM == S&DM) without merging I&PM into IPM
  const canon=a=>{const u=String(a||'').toUpperCase(); return u==='I&PM'?'I&PM':u.replace(/&/g,'');};
  const ckey=(a,d)=>canon(a)+'|'+(d||'');
  const myKey=new Set(electives.map(e=>ckey(e.abbr,e.division)));
  const myChanges=(DATA.changes||[]).filter(c=>myKey.has(ckey(c.abbr,c.division)));
  const elBy={}; electives.forEach(e=>{elBy[ckey(e.abbr,e.division)]=e;});
  const normHM=s=>{const m=String(s||'').match(/(\d{1,2})[:.](\d{2})/); return m?parseInt(m[1])+':'+m[2]:'';};
  const sessByHM=hm=>DATA.sessions.find(s=>normHM(s.start)===normHM(hm));
  const isTBA=c=>!!(c.tba || !sessByHM(c.new_hhmm));
  const changeMap=new Map();   // day|canon(abbr)|div -> change
  myChanges.forEach(c=>{ const el=elBy[ckey(c.abbr,c.division)], ses=sessByHM(c.new_hhmm);
    if(el&&ses&&c.new_day&&!isTBA(c)&&c.type!=='Cancelled') meetings.push({sec:el,day:c.new_day,session:ses.name,start:ses.start,end:ses.end,changed:'in'});
    if(c.old_day) changeMap.set(c.old_day+'|'+ckey(c.abbr,c.division), c); });
  meetings.forEach(m=>{ if(m.changed) return;
    const c=changeMap.get(m.day+'|'+ckey(m.sec.abbr,m.sec.division));
    if(c){ m.changed='out'; m.tba=isTBA(c); } });

  const byDay={}; meetings.forEach(m=>{(byDay[m.day]=byDay[m.day]||[]).push(m);});
  const cellMap={}; meetings.forEach(m=>{const k=m.day+'|'+m.session;(cellMap[k]=cellMap[k]||[]).push(m);});
  const evByDay={}; (DATA.events||[]).forEach(e=>{(evByDay[e.day]=evByDay[e.day]||[]).push(e);});
  const shortT=t=>String(t||'').replace(/AM$/,'a').replace(/PM$/,'p').replace(/^0/,'');
  const dnum=d=>fmtDM(dayDate[d]).split(' ')[0];

  let html=`<div class="who"><span class="name">${esc(st.n)}</span><span class="chip">${esc(roll)}</span><span class="meta">${electives.length} electives · ${esc(st.b)}</span></div>`;

  if(myChanges.length){ const seen=new Set();
    myChanges.forEach(c=>{const t=cleanNotice(c.raw); if(!t||seen.has(t))return; seen.add(t);
      html+=`<div class="notice${isTBA(c)?' red':''}"><span class="ntag">${esc(c.type||'Changed')}</span><span class="ntxt">${esc(t)}</span></div>`;}); }

  const hasMoved=myChanges.some(c=>!isTBA(c));
  const hasPostponed=myChanges.some(c=>isTBA(c));

  html+=`<div class="legend">
      <span class="li"><span class="sw cls"></span>My Class</span>
      <span class="li"><span class="sw today"></span>Today</span>
      <span class="li"><span class="sw hol"></span>Holiday</span>
      <span class="li"><span class="sw exam"></span>Exam</span>
      ${hasMoved?'<span class="li"><span class="sw chg"></span>Changed</span>':''}
      ${hasPostponed?'<span class="li"><span class="sw pp"></span>Postponed</span>':''}
    </div>`;

  const usedDays=DATA.days.filter(d=>(byDay[d]&&byDay[d].length)||(evByDay[d]&&evByDay[d].length));
  const usedSess=DATA.sessions.filter(s=>meetings.some(m=>m.session===s.name));

  if(!usedDays.length||!usedSess.length){
    html+=`<div class="empty-week">No classes scheduled for you this week.</div>`;
  } else {
    const cols=`${TCOL}px repeat(${usedDays.length},minmax(48px,1fr))`;
    html+=`<div class="grid-wrap"><div class="calcard">`;
    // gradient weekday band
    html+=`<div class="weekhead" style="grid-template-columns:${cols}">`;
    html+=`<div class="whbar" style="grid-column:2 / -1"></div><div class="whcorner"></div>`;
    usedDays.forEach((d,i)=>{ const isT=d===todayDay;
      html+=`<div class="wh${isT?' today':''}" style="grid-column:${i+2}"><span class="whd">${d.slice(0,3)}</span><span class="whn">${dnum(d)}</span></div>`; });
    html+=`</div>`;
    // session rows
    html+=`<div class="grid" style="grid-template-columns:${cols}">`;
    usedSess.forEach(s=>{
      html+=`<div class="gt">${esc(shortT(s.start))}<span>${esc(shortT(s.end))}</span></div>`;
      usedDays.forEach(d=>{
        const cell=cellMap[d+'|'+s.name]||[];
        const ev=evByDay[d]||[]; const hol=ev.some(e=>e.type==='holiday'), exam=ev.some(e=>e.type==='exam');
        const flag=d===todayDay?' today':hol?' hol':exam?' exam':'';
        let inner='';
        cell.forEach(m=>{ const ppl=m.changed==='out'&&m.tba;
          const cc=m.changed==='in'?' chg':ppl?' pp':m.changed==='out'?' chg out':'';
          const mv=m.changed==='in'?'<span class="gmv">moved here</span>'
                  :ppl?'<span class="ppbadge">Postponed · TBA</span>'
                  :m.changed==='out'?'<span class="gmv">moved</span>':'';
          inner+=`<span class="gblk ${slug(m.sec.area)}${cc}" title="${esc(m.sec.name)} · ${esc(m.sec.room||'')} · ${esc(m.sec.faculty||'')}"><span class="ga">${PERSON}${esc(m.sec.abbr)}<small>${m.sec.division?(' '+esc(m.sec.division)):''}</small></span><span class="gr">${ROOM}${esc(m.sec.room||'TBA')}</span>${mv}</span>`; });
        html+=`<div class="gc${flag}${cell.length>1?' clash':''}">${inner}</div>`;
      });
    });
    html+=`</div></div></div>`;

    // event chips + summary note (image-style)
    const evs=(DATA.events||[]).slice().sort((a,b)=>a.date<b.date?-1:1);
    const nClasses=meetings.filter(m=>m.changed!=='out').length;
    let below=`<div class="note"><b>${nClasses} ${nClasses===1?'class':'classes'}</b> across <b>${usedDays.length} ${usedDays.length===1?'day':'days'}</b> this week.</div>`;
    evs.forEach(e=>{ const n=fmtDM(e.date).split(' ')[0];
      below+=`<div class="chip2 ${e.type==='holiday'?'hol':'exam'}"><span class="num">${n}</span><span><span class="typ">${e.type==='holiday'?'Holiday':'Exam'}</span><span class="lab">${esc(e.name)}</span></span></div>`; });
    html+=`<div class="belowcal">${below}</div>`;
  }

  // directory
  html+=`<details class="dir"><summary>Electives, faculty &amp; rooms</summary><div class="dir-list">`;
  electives.slice().sort((a,b)=>a.abbr.localeCompare(b.abbr)).forEach(e=>{
    const when=(e.meetings||[]).map(m=>`${m.day.slice(0,3)} ${m.start}`).join(", ");
    html+=`<div class="di ${slug(e.area)}">
        <div class="di-h"><span class="tag">${PERSON}${esc(e.abbr)}(${esc(e.division||'-')})</span><span class="di-nm">${esc(e.name)}</span></div>
        <div class="di-r">${esc(e.faculty||'—')}${e.email?` · <a href="mailto:${esc(e.email)}">${esc(e.email)}</a>`:''}</div>
        <div class="di-r">${ROOM}Room ${esc(e.room||'TBA')}</div>
        ${when?`<div class="di-r meets">${esc(when)}</div>`:`<div class="di-r meets">Not scheduled this week</div>`}
      </div>`;
  });
  html+=`</div></details>`;

  $("result").innerHTML=html;
  $("result").classList.add("show");
}

$("btn").addEventListener("click",lookup);
$("roll").addEventListener("keydown",e=>{ if(e.key==="Enter") lookup(); });
$("roll").focus();
</script>
</body>
</html>
"""
open(OUT_PATH, "w", encoding="utf-8").write(TEMPLATE.replace("__DATA__", data))
print(f"Wrote {OUT_PATH}")
