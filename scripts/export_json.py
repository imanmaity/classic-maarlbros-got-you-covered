#!/usr/bin/env python3
"""Export university.db -> schedule_data.json (normalized: sections stored once).
Also folds in this week's class-change notices from changes.json (written by
fetch_email.py) so the app can highlight them."""
import sqlite3, json, re, sys, os, datetime

DB  = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "university.db")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "schedule_data.json")
WEEK_OF = "2026-06-22"

con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
cur = con.cursor()

def to_min(t):
    m = re.match(r"(\d{1,2}):(\d{2})(AM|PM)", t or "")
    if not m: return 9999
    h, mi, ap = int(m.group(1)), int(m.group(2)), m.group(3)
    if ap == "PM" and h != 12: h += 12
    if ap == "AM" and h == 12: h = 0
    return h*60 + mi

sess = {r["session"]: (r["start_time"], r["end_time"])
        for r in cur.execute("SELECT DISTINCT session,start_time,end_time FROM meetings")}
sessions = sorted([{"name": k, "start": v[0], "end": v[1]} for k, v in sess.items()],
                  key=lambda s: to_min(s["start"]))

sections = {}
for c in cur.execute("""SELECT sec.section_id sid, s.abbr, s.name sname, s.area, sec.division,
                               f.name fname, f.email, sec.classroom_code room
                        FROM sections sec JOIN subjects s ON s.code=sec.subject_code
                        LEFT JOIN faculty f ON f.faculty_key=sec.faculty_key""").fetchall():
    mtg = [{"day": m["day"], "session": m["session"], "start": m["start_time"], "end": m["end_time"]}
           for m in cur.execute("SELECT day,session,start_time,end_time FROM meetings WHERE section_id=?",
                                (c["sid"],)).fetchall()]
    sections[str(c["sid"])] = {"abbr": c["abbr"], "name": c["sname"], "area": c["area"],
                               "division": c["division"], "faculty": c["fname"],
                               "email": c["email"], "room": c["room"], "meetings": mtg}

events = [{"date":e["date"],"day":e["day"],"type":e["type"],"name":e["name"]}
          for e in cur.execute("SELECT date,day,type,name FROM events").fetchall()]

students = {}
for s in cur.execute("SELECT roll_no,name,batch FROM students").fetchall():
    sids = [str(e["section_id"]) for e in
            cur.execute("SELECT section_id FROM enrollments WHERE roll_no=?", (s["roll_no"],)).fetchall()]
    students[s["roll_no"]] = {"n": s["name"], "b": s["batch"], "s": sids}

# class-change notices (kept only if they touch the displayed week)
changes = []
chg_path = os.path.join(os.path.dirname(os.path.abspath(DB)), "changes.json")
if os.path.exists(chg_path):
    try:
        wstart = datetime.date.fromisoformat(WEEK_OF)
        wend = wstart + datetime.timedelta(days=6)
        def in_week(ds):
            try: return wstart <= datetime.date.fromisoformat(ds) <= wend
            except Exception: return False
        for c in json.load(open(chg_path, encoding="utf-8")):
            if in_week(c.get("new_date")) or in_week(c.get("old_date")):
                changes.append(c)
    except Exception as e:
        print("changes.json skipped:", e)

data = {"meta": {"institute": "Institute of Management, Nirma University",
                 "term": "MBA Term-IV", "week_of": WEEK_OF},
        "days": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
        "sessions": sessions, "events": events, "changes": changes,
        "sections": sections, "students": students}
open(OUT, "w", encoding="utf-8").write(json.dumps(data, separators=(",", ":"), ensure_ascii=False))
print(f"Wrote {OUT}: {len(sections)} sections, {len(students)} students, {len(changes)} changes")
con.close()
