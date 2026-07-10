#!/usr/bin/env python3
"""Export university.db -> schedule_data.json, carrying EVERY live week.

The master workbook can span several weeks (same electives, only the day/time/
room shift week to week). This exporter buckets the dated meetings into one
array per week and ships them all, so the app can show the whole run instead of
collapsing everything to a single week.

Week selection:
  * A "week" is a Mon-Sun span that has at least one dated meeting.
  * Weeks whose Sunday has already passed (relative to today, IST) are dropped,
    so a finished week is never shown; the current/upcoming weeks remain.
  * If every dated week is in the past, the last one is kept (so the file is
    never empty). If there are no dated meetings at all, the current calendar
    week is used and recurring (date-less) rows carry it.

Output shape (per section):
  meetingsByWeek : { "<monday-iso>": [ {day,session,start,end}, ... ], ... }
  meetings       : first week's pattern       (back-compat: old front ends)
  meetingsNext   : second week's pattern      (back-compat)
meta.weeks       : [ "<monday-iso>", ... ]  ordered, current week first
meta.week_of / week_of_next kept for back-compat.
"""
import sqlite3, json, re, sys, os, datetime

DB  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "university.db")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "schedule_data.json")

con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
cur = con.cursor()

# ---- pick the weeks to display ----
today = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=5, minutes=30)).date()  # IST
mdates = sorted({datetime.date.fromisoformat(r["date"])
                 for r in cur.execute("SELECT DISTINCT date FROM meetings WHERE date IS NOT NULL")})

def monday_of(d): return d - datetime.timedelta(days=d.weekday())

# every Mon that owns at least one dated meeting, in order
week_mons = sorted({monday_of(d) for d in mdates})
# drop weeks that have fully finished (Sunday < today); always keep at least one
kept = [m for m in week_mons if (m + datetime.timedelta(days=6)) >= today]
if not kept:
    kept = week_mons[-1:] if week_mons else []
if not kept:
    kept = [monday_of(today)]        # no dated meetings anywhere -> current week only

WEEKS = kept                          # ordered list of datetime.date Mondays
WK_START = WEEKS[0]
WK_END   = WK_START + datetime.timedelta(days=6)
NEXT_START = WEEKS[1] if len(WEEKS) > 1 else WK_START + datetime.timedelta(days=7)

def week_pat(rows, start, end):
    """day-of-week pattern for one week; date-less rows are treated as recurring (appear every week)."""
    seen=set(); out=[]
    for m in rows:
        ds=m["date"]; dd=None
        if ds:
            try: dd=datetime.date.fromisoformat(ds)
            except Exception: dd=None
        if dd is not None and not (start <= dd <= end): continue
        k=(m["day"], m["session"])
        if k in seen: continue
        seen.add(k); out.append({"day":m["day"],"session":m["session"],"start":m["start_time"],"end":m["end_time"]})
    return out

def to_min(t):
    m = re.match(r"(\d{1,2}):(\d{2})(AM|PM)", t or "")
    if not m: return 9999
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap == "PM" and h != 12: h += 12
    if ap == "AM" and h == 12: h = 0
    return h*60 + mi

# sessions actually used anywhere (client filters to the shown week)
sess = {r["session"]: (r["start_time"], r["end_time"])
        for r in cur.execute("SELECT DISTINCT session,start_time,end_time FROM meetings")}
sessions = sorted([{"name": k, "start": v[0], "end": v[1]} for k, v in sess.items()],
                  key=lambda s: to_min(s["start"]))

sections = {}
for c in cur.execute("""SELECT sec.section_id sid, s.abbr, s.name sname, s.area, sec.division,
                               f.name fname, f.email, sec.classroom_code room
                        FROM sections sec JOIN subjects s ON s.code=sec.subject_code
                        LEFT JOIN faculty f ON f.faculty_key=sec.faculty_key""").fetchall():
    rows=cur.execute("SELECT DISTINCT day,session,start_time,end_time,date FROM meetings WHERE section_id=?", (c["sid"],)).fetchall()
    by_week = {mon.isoformat(): week_pat(rows, mon, mon + datetime.timedelta(days=6)) for mon in WEEKS}
    sections[str(c["sid"])] = {"abbr": c["abbr"], "name": c["sname"], "area": c["area"],
                               "division": c["division"], "faculty": c["fname"],
                               "email": c["email"], "room": c["room"],
                               "meetingsByWeek": by_week,
                               "meetings": by_week[WK_START.isoformat()],
                               "meetingsNext": by_week.get(NEXT_START.isoformat(), [])}

events = [{"date":e["date"],"day":e["day"],"type":e["type"],"name":e["name"]}
          for e in cur.execute("SELECT date,day,type,name FROM events ORDER BY date").fetchall()]

students = {}
for s in cur.execute("SELECT roll_no,name,batch FROM students").fetchall():
    sids = [str(e["section_id"]) for e in
            cur.execute("SELECT section_id FROM enrollments WHERE roll_no=?", (s["roll_no"],)).fetchall()]
    students[s["roll_no"]] = {"n": s["name"], "b": s["batch"], "s": sids}

changes = []
chg_path = os.path.join(os.path.dirname(os.path.abspath(DB)), "changes.json")
# current room per (abbr, division) — lets a "held in T3" mail show "was <current room>"
room_by = {(str(s["abbr"]).upper(), str(s["division"] or "").upper()): s["room"]
           for s in sections.values()}
if os.path.exists(chg_path):
    try:
        for c in json.load(open(chg_path, encoding="utf-8")):
            if c.get("type") == "Room Change" and not c.get("old_room"):
                c["old_room"] = room_by.get((str(c.get("abbr", "")).upper(),
                                             str(c.get("division", "")).upper()))
            changes.append(c)
    except Exception as e:
        print("changes.json skipped:", e)

updates = []
upd_path = os.path.join(os.path.dirname(os.path.abspath(DB)), "updates.json")
if os.path.exists(upd_path):
    try:
        for u in json.load(open(upd_path, encoding="utf-8")):
            updates.append(u)
    except Exception as e:
        print("updates.json skipped:", e)

data = {"meta": {"institute": "Institute of Management, Nirma University",
                 "term": "MBA Term-IV",
                 "weeks": [m.isoformat() for m in WEEKS],
                 "week_of": WK_START.isoformat(), "week_of_next": NEXT_START.isoformat(),
                 "recurring": True},
        "days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
        "sessions": sessions, "events": events, "changes": changes, "updates": updates,
        "sections": sections, "students": students}
open(OUT, "w", encoding="utf-8").write(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
print(f"Weeks {[m.isoformat() for m in WEEKS]}: {len(sessions)} sessions, {len(events)} events, {len(changes)} changes")
con.close()
