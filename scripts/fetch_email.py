#!/usr/bin/env python3
"""Fetch from the admin's email via IMAP:
  1) the newest schedule .xlsx attachment  -> argv[1] (default rosters/schedule_latest.xlsx)
  2) recent "Change in class schedule" notices -> data/changes.json (parsed)

Env vars (set as GitHub repository secrets):
  MAIL_USER, MAIL_PASS, SENDER, IMAP_HOST (default imap.gmail.com),
  MAIL_SUBJECT (optional, required substring in the schedule email's subject),
  CHANGE_SUBJECT (optional, default "change in class")
Exits non-zero if no schedule attachment is found (so a stale week is never published).
Change parsing is best-effort and never fails the build.
"""
import imaplib, email, os, sys, re, json, datetime
from email.header import decode_header
from email.utils import parsedate_to_datetime, parseaddr

OUT  = sys.argv[1] if len(sys.argv) > 1 else "rosters/schedule_latest.xlsx"
CHANGES_OUT = os.environ.get("CHANGES_OUT", "data/changes.json")
HOST = os.environ.get("IMAP_HOST", "imap.gmail.com")
USER = os.environ.get("MAIL_USER"); PWD = os.environ.get("MAIL_PASS")
SENDER = os.environ.get("SENDER", "mba.im@nirmauni.ac.in")
SUBJ = os.environ.get("MAIL_SUBJECT", "")
CHANGE_SUBJECT = os.environ.get("CHANGE_SUBJECT", "change in class")
if not (USER and PWD):
    sys.exit("MAIL_USER / MAIL_PASS not set.")

def decode(s):
    return "".join(p.decode(enc or "utf-8", "ignore") if isinstance(p, bytes) else p
                   for p, enc in decode_header(s or ""))

def body_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                try: return part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "ignore")
                except Exception: pass
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html = part.get_payload(decode=True).decode("utf-8", "ignore")
                return re.sub(r"<[^>]+>", " ", html)
        return ""
    try: return msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8", "ignore")
    except Exception: return ""

# ---- trust guards: only an email from the right sender, carrying a current-dated
#      schedule, may overwrite the roster. Stops a stray/spoofed or stale re-sent
#      mail from quietly kicking off a build for 150 students. ----
def _addr_of(msg):
    return parseaddr(decode(msg.get("From", "")))[1].strip().lower()

def _sender_ok(msg):
    """True only if the real From address matches SENDER. If SENDER is a full
    address, require an EXACT match (IMAP's FROM search is a loose substring and
    can be fooled by a display name or look-alike). If SENDER is a bare domain,
    require the address to be in that domain."""
    if not SENDER:
        return True
    addr, want = _addr_of(msg), SENDER.strip().lower()
    if not addr:
        return False
    if "@" in want:
        return addr == want
    return addr.split("@")[-1] == want            # SENDER given as a domain

def _name_dates(fn):
    """Calendar dates found in an attachment filename, e.g. the
    '29_06_2026-12_07_2026' range in the weekly schedule file name."""
    out = []
    for d, m, y in re.findall(r'(\d{1,2})[._\-/](\d{1,2})[._\-/](\d{2,4})', fn or ""):
        y = int(y); y = 2000 + y if y < 100 else y
        try: out.append(datetime.date(y, int(m), int(d)))
        except ValueError:
            try: out.append(datetime.date(y, int(d), int(m)))   # tolerate m/d swap
            except ValueError: pass
    return out

def _looks_like_schedule(raw):
    """Is `raw` actually the master timetable, or some other .xlsx the office
    happened to attach? Returns True only if the workbook carries BOTH a
    Course-Detail catalog (course codes in column B) AND a weekly grid sheet
    with dated rows -- i.e. exactly what build_dataset needs to parse a real
    timetable. Mirrors build_dataset's own sheet detection, so 'valid here'
    means 'parses to non-zero there'. Returns False for a blank/wrong sheet,
    and None only if openpyxl is unavailable to check (caller then accepts)."""
    try:
        from openpyxl import load_workbook
        import io
    except Exception:
        return None
    try:
        wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        sheets = {s: [list(r) for r in wb[s].iter_rows(values_only=True)]
                  for s in wb.sheetnames}
        wb.close()
    except Exception:
        return False
    cd = next((s for s in sheets if "course detail" in s.lower()),
              next(iter(sheets), None))
    cd_rows = sheets.get(cd, [])
    has_codes = any(
        len(r) > 1 and isinstance(r[1], str) and "total" not in r[1].lower()
        and re.search(r"[A-Za-z]", r[1]) and re.search(r"\d", r[1])
        for r in cd_rows[1:])
    has_grid = any(
        any(len(r) > 0 and isinstance(r[0], datetime.datetime) for r in rows[2:])
        for s, rows in sheets.items() if s != cd)
    return bool(has_codes and has_grid)

# room/venue token, e.g. "T3", "E6", "T-3", "309-F", "LH1" (letters+digits, or digits-letters)
ROOM_RE = r'(?:[A-Za-z]{1,4}-?\d{1,3}[A-Za-z]?|\d{2,4}-[A-Za-z]{1,3})'
_WEEKDAYS = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4,"saturday":5,"sunday":6}
def _room_norm(s): return re.sub(r'\s+', '', str(s)).upper()

# #1: which notices to parse. Keep the configurable phrase, but also let
# postpone / reschedule / cancel / venue notices through even when their
# subject never says "change in class".
_CHANGE_SUBJECT_RE = re.compile(
    r'postpon|prepon|reschedul|cancel|class\s*-?\s*room|classroom|\bvenue\b|\broom\b|'
    r'change\s+in\s+(?:class|schedule|time|timing|venue)', re.I)

# #4: pull division letters out of a parenthesised group sensibly.
#   "A & B" -> [A, B] ; "A" -> [A] ; "All"/"both" -> [""] (whole course) ;
#   noise like "MBA students" / "B.Tech" -> []  (no stray single letters;
#   the period/letter guards stop the "B" in "B.Tech" being read as a division).
def _divs(group):
    g = (group or "").strip()
    if re.search(r'\b(?:all|both|entire|every|each)\b', g, re.I):
        return [""]
    return [d.upper() for d in re.findall(r'(?<![A-Za-z.])([A-Ha-h])(?![A-Za-z.])', g)]

# #5: bare codes (no "(division)") named as a class, e.g. "PML session ...",
# or named with a postpone/cancel verb, e.g. "PML is postponed". The code is
# matched case-SENSITIVELY (uppercase only) so words like "is"/"are" can't slip
# in; only the verbs are case-insensitive. A stop-list drops common non-courses.
def _bare_codes(text):
    """Bare codes with no "(division)" -- named as a class ("PML session ...")
    or inside a postpone/cancel sentence ("BI(A) and PML are postponed").
    Self-contained (no module-level constants) so selftest can extract it with
    parse_change. Codes are matched case-SENSITIVELY (uppercase only) so words
    like "is"/"are" can't slip in; a stop-list drops common non-course words."""
    stop = {"MBA", "IMBA", "BTECH", "IIM", "PDF", "FYI", "TBA", "AM", "PM",
            "LH", "NOTE", "ALL", "AND", "FOR", "THE", "ARE", "IS"}
    out = []
    def add(a):
        a = a.upper()
        if a not in stop and a not in out:
            out.append(a)
    for ab in re.findall(r'\b([A-Z][A-Z&]{1,5})\b\s+(?i:sessions?|classes?|lectures?|scheduled)\b', text):
        add(ab)                                   # "PML session", "PML scheduled"
    for sent in re.split(r'\n|(?<!\d)\.(?!\d)', text):   # sentence split that keeps dates (05.01.2026) whole
        if re.search(r'(?i:postpon\w*|prepon\w*|reschedul\w*|cancel\w*|not\s+be\s+held)', sent):
            for ab in re.findall(r'\b([A-Z][A-Z&]{1,5})\b', sent):   # -> take every code it names
                add(ab)
    return out

def _secs_in(t):
    """(abbr, division) pairs mentioned in a fragment of notice text."""
    s = []
    for ab, dvgroup in re.findall(r'([A-Za-z&]{2,6})\(\s*([A-Za-z][A-Za-z&,\s]*?)\s*\)', t):
        for dv in _divs(dvgroup):
            s.append((ab, dv))
    return s

def _detect_rooms(t):
    """(new_room, old_room) from a fragment, using the same venue patterns."""
    nr = orr = None
    m = re.search(r'\b(' + ROOM_RE + r')\s+to\s+(' + ROOM_RE + r')\b', t, re.I)   # "from E6 to T3"
    if m: orr, nr = _room_norm(m.group(1)), _room_norm(m.group(2))
    if nr is None:                                                               # "T3 classroom"
        m = re.search(r'\b(' + ROOM_RE + r')\s+class\s*-?\s*room\b', t, re.I)
        if m: nr = _room_norm(m.group(1))
    if nr is None:                                                               # "held in / shifted to / venue: T3"
        m = re.search(r'(?:held|conducted|shifted|moved|take\s*place|venue|class\s*-?\s*room|classroom|room|hall)\b'
                      r'[^.\n]{0,25}?\b(?:in|to|at|:)\s*(?:room\s*(?:no\.?)?\s*|class\s*-?\s*room\s*|venue\s*|hall\s*)?'
                      r'(' + ROOM_RE + r')\b', t, re.I)
        if m: nr = _room_norm(m.group(1))
    if orr is None:                                                              # "instead of E6"
        m = re.search(r'(?:instead of|in place of|rather than|in lieu of|not in)\s+(?:room\s*)?(' + ROOM_RE + r')\b', t, re.I)
        if m: orr = _room_norm(m.group(1))
    return nr, orr

def _room_events(t):
    """[(pos, new_room, old_room)] for every venue mention in the text, in order,
    so each section can bind to the room named AFTER it -- robust to however the
    office formats the numbered points."""
    ev = []
    for m in re.finditer(r'\b(' + ROOM_RE + r')\s+to\s+(' + ROOM_RE + r')\b', t, re.I):  # "from E6 to T3"
        ev.append((m.start(), _room_norm(m.group(2)), _room_norm(m.group(1))))
    for m in re.finditer(r'\b(' + ROOM_RE + r')\s+class\s*-?\s*room\b', t, re.I):          # "T3 classroom"
        ev.append((m.start(), _room_norm(m.group(1)), None))
    for m in re.finditer(r'(?:held|conducted|shifted|moved|take\s*place|venue|class\s*-?\s*room|classroom|room|hall)\b'
                         r'[^.\n]{0,25}?\b(?:in|to|at|:)\s*(?:room\s*(?:no\.?)?\s*|class\s*-?\s*room\s*|venue\s*|hall\s*)?'
                         r'(' + ROOM_RE + r')\b', t, re.I):                                 # "held in / shifted to T3"
        ev.append((m.start(), _room_norm(m.group(1)), None))
    ev.sort(key=lambda e: e[0])
    return ev

def _clauses(t):
    """Split a notice into venue clauses on numbered markers ("1)", "2)") and
    sentence enders, so each subject group pairs with the room in its own clause."""
    segs = re.split(r'(?:\s*\b\d+\)\s*)|(?<=[.;])\s+', t)
    return [s for s in segs if s and s.strip()]

def parse_change(text, edate=None):
    # edate = the email's own date, so "today"/"tomorrow"/weekday resolve correctly
    edate = edate or datetime.date.today()
    # sections like "SBM(A)", "SBM(A & B)", "SDM(A), SDM(B)" -> one (abbr, division) per division
    secs = []
    for ab, dvgroup in re.findall(r'([A-Za-z&]{2,6})\(\s*([A-Za-z][A-Za-z&,\s]*?)\s*\)', text):
        for dv in _divs(dvgroup):
            secs.append((ab, dv))
    # #5: also catch bare codes named with a postpone/cancel verb but no
    # "(division)", e.g. "PML session is postponed" -- even alongside other
    # parenthesised sections. Empty division -> whole class.
    for _ab in _bare_codes(text):
        if not any(a.upper() == _ab for a, _ in secs) and (_ab, "") not in secs:
            secs.append((_ab, ""))
    if not secs: return []
    raw_dates = re.findall(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', text)
    def _yr(y):
        # a schedule notice's date is always near the send date, so a year far
        # from the email's is a typo -- e.g. "01.07.2016" in a 2026 mail -> 2026.
        v = int(('20' + y) if len(y) == 2 else y)
        return edate.year if abs(v - edate.year) > 1 else v
    dates = [f"{_yr(y):04d}-{int(m):02d}-{int(d):02d}" for d, m, y in raw_dates]
    # time ranges, capturing a trailing AM/PM if present (e.g. "02:40-03:40 & 03:50-04:50PM")
    tmatches = re.findall(r'(\d{1,2}[:.]\d{2})\s*(?:[-\u2013\u2014]|to)\s*\d{1,2}[:.]\d{2}\s*([AaPp][Mm])?', text)
    starts = [s.replace('.', ':') for s, _ in tmatches]
    meris = [m.upper() for _, m in tmatches]
    # if a single meridiem is stated for the whole sentence, apply it to the bare times too
    known = [m for m in meris if m]
    fill = known[-1] if known and len(set(known)) == 1 else None
    times = [s + (m if m else (fill or "")) for s, m in zip(starts, meris)]
    low = text.lower()
    ctype = ('Preponed' if 'prepon' in low else 'Postponed' if 'postpon' in low
             else 'Cancelled' if ('cancel' in low or 'not be held' in low)
             else 'Rescheduled' if ('reschedul' in low or 'shift' in low) else 'Changed')
    old_date = dates[0] if dates else None
    new_date = dates[-1] if len(dates) >= 2 else None
    tba = len(times) == 0  # no new time announced -> "to be announced"
    def day(ds):
        try: return datetime.date.fromisoformat(ds).strftime("%A")
        except Exception: return None
    # resolve a relative / weekday-only date ("today", "tomorrow", "on Wednesday") to a real date
    def _add(n): return (edate + datetime.timedelta(days=n)).isoformat()
    rel_date = None
    if   re.search(r'\bday\s+after\s+tomorrow\b', low): rel_date = _add(2)
    elif re.search(r'\btomorrow\b', low):              rel_date = _add(1)
    elif re.search(r'\btoday\b', low):                 rel_date = _add(0)
    else:
        wd = re.search(r'\b(?:on|this|coming)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', low)
        if wd:
            rel_date = _add((_WEEKDAYS[wd.group(1)] - edate.weekday()) % 7)
    # ---- room / venue detection (only the classroom changes; day & time stay put) ----
    new_room, old_room = _detect_rooms(text)
    has_time_shift = bool(times)
    has_date_shift = bool(new_date) and (new_date != old_date)
    is_room_change = (new_room is not None) and not has_time_shift and not has_date_shift \
                     and not any(k in low for k in ('postpon', 'prepon', 'cancel'))
    # keep the message, drop the office sign-off / signature
    cut = len(text)
    for pat in (r'\bregards\b', r'\bthanks\b', r'\bthank you\b', r'\bwarm regards\b',
                r'\bbest regards\b', r'\bsincerely\b', r'\byours\b',
                r'(MBA\s+)?Programme Office'):
        mm = re.search(pat, text, re.I)
        if mm: cut = min(cut, mm.start())
    raw = re.sub(r'\s+', ' ', text[:cut]).strip()[:400]
    out = []
    if is_room_change:
        d0 = old_date or new_date or rel_date or edate.isoformat()   # the day the relocated class meets
        d_day = day(d0)
        hhmm = times[0] if len(times) == 1 else None                 # optional; room change attaches by day
        # A single notice can assign different rooms to different groups, e.g.
        #   "1) IPM(A),FSA(C) ... E2 Classroom.  2) CB(A),CB(B) ... E1 classroom."
        # Pair each section with the room mentioned in ITS clause; fall back to the
        # global room only if a section's clause names no venue of its own.
        # Bind each section to the FIRST venue named AFTER it in the text, so a
        # mis-formatted numbered list can't dump a section onto the global (first)
        # room. E.g. "1) CB(A) ... E2.  2) CB(B) ... T4" -> CB(A)=E2, CB(B)=T4,
        # because T4 is the next venue after CB(B) and E2 sits before it.
        rev = _room_events(text)
        seg_room = {}
        for sm in re.finditer(r'([A-Za-z&]{2,6})\(\s*([A-Za-z][A-Za-z&,\s]*?)\s*\)', text):
            after = next((e for e in rev if e[0] >= sm.start()), None)
            if after:
                for dv in _divs(sm.group(2)):
                    seg_room.setdefault((sm.group(1).upper(), dv.upper()), (after[1], after[2] or old_room))
        for ab, dv in secs:
            nr, orr = seg_room.get((ab.upper(), dv.upper()), (new_room, old_room))
            out.append({"abbr": ab.upper(), "division": dv.upper(), "type": "Room Change",
                        "old_date": d0, "old_day": d_day, "new_date": d0, "new_day": d_day,
                        "old_hhmm": hhmm, "new_hhmm": hhmm,
                        "old_room": orr, "new_room": nr, "tba": False, "raw": raw})
        return out
    # a dateless time/cancel change ("cancelled today") still gets a concrete day to render on
    if old_date is None and rel_date:
        old_date = rel_date
        if new_date is None and not times: new_date = rel_date
    # Postponements/cancellations can list several INDEPENDENT dates, e.g.
    #   "sessions scheduled on 29.06, 01.07 & 03.07 are postponed".
    # Each date is its own postponed session, not a from->to shift, so emit one
    # change per (section, date). Genuine shifts ("rescheduled to 03.07") are
    # excluded so they keep the old->new behaviour below.
    # A multi-date postponement ("on 29.06, 01.07 & 03.07 are postponed") means each
    # date is its own postponed session. But a notice that names a TARGET date
    # ("postponed to 24.06", "rescheduled to ...") is a real from->to shift and must
    # keep the old->new behaviour below.
    _has_target = bool(re.search(r'\bto\s+\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', low)) or \
                  bool(re.search(r'reschedul|shift|moved\s+to|will\s+(?:now\s+)?be\s+held|held\s+on\b', low))
    if ctype in ('Postponed', 'Cancelled') and len(dates) >= 2 and not _has_target:
        out = []
        for ab, dv in secs:
            for ds in dates:
                out.append({"abbr": ab.upper(), "division": dv.upper(), "type": ctype,
                            "old_date": ds, "old_day": day(ds),
                            "new_date": None, "new_day": None,
                            "new_hhmm": None, "tba": True, "raw": raw})
        return out
    for i, (ab, dv) in enumerate(secs):
        if not times:                 hhmm = None
        elif len(times) == len(secs): hhmm = times[i]            # "respectively" -> per division
        elif len(times) == 1:         hhmm = times[0]            # one time for all
        else:                         hhmm = times[i] if i < len(times) else times[-1]
        out.append({"abbr": ab.upper(), "division": dv.upper(), "type": ctype,
                    "old_date": old_date, "old_day": day(old_date),
                    "new_date": new_date, "new_day": day(new_date),
                    "new_hhmm": hhmm, "tba": tba, "raw": raw})
    return out

M = imaplib.IMAP4_SSL(HOST); M.login(USER, PWD); M.select("INBOX")

# ---- 1) change notices (best effort) ----
changes, seen = [], set()
since = (datetime.date.today() - datetime.timedelta(days=14)).strftime("%d-%b-%Y")
crit = ["FROM", SENDER, "SINCE", since] if SENDER else ["SINCE", since]
try:
    typ, data = M.search(None, *crit)
    for num in reversed(data[0].split()):
        typ, md = M.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(md[0][1])
        _subj = decode(msg.get("Subject", "")).lower()
        if CHANGE_SUBJECT.lower() not in _subj and not _CHANGE_SUBJECT_RE.search(_subj):
            continue
        try: _edate = parsedate_to_datetime(msg.get("Date")).date()
        except Exception: _edate = datetime.date.today()
        for c in parse_change(body_text(msg), _edate):
            # dedup by the actual change (subject + division + dates + time + type), NOT by the shared
            # message text -- otherwise a single mail naming two divisions keeps only one of them.
            # new_room is deliberately excluded: mail is scanned newest-first, so if a later
            # "typographical error" correction moves the same cell to a different room, the newer
            # one is kept and the superseded room is dropped.
            key = (c["abbr"], c["division"], c["old_date"], c["new_date"], c["new_hhmm"], c["type"])
            if key not in seen:
                changes.append(c); seen.add(key)
    os.makedirs(os.path.dirname(CHANGES_OUT) or ".", exist_ok=True)
    json.dump(changes, open(CHANGES_OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"[fetch_email v2026-07-01: nearest-room + year-snap] Parsed {len(changes)} change notice(s) -> {CHANGES_OUT}")
except Exception as e:
    print("Change-notice fetch skipped:", e)

# ---- 1b) committee notices -> data/updates.json (best effort, never fails the build) ----
UPDATES_OUT = os.environ.get("UPDATES_OUT", "data/updates.json")
COMMITTEES = [
    ("PLACECOMM", "Placement Committee",        os.environ.get("PLACECOMM_FROM", "placecomm.im@nirmauni.ac.in")),
    ("SAC",       "Student Advisory Committee", os.environ.get("SAC_FROM",       "sac.im@nirmauni.ac.in")),
    ("SWC",       "Student Welfare Committee",  os.environ.get("SWC_FROM",       "studentwelfare.im@nirmauni.ac.in")),
    ("NICHE",     "The Marketing Club",         os.environ.get("NICHE_FROM",     "niche.im@nirmauni.ac.in")),
    ("FINESSE",   "Finance Club",               os.environ.get("FINESSE_FROM",   "finesse.im@nirmauni.ac.in")),
    ("NEWSJN",    "The News Club",              os.environ.get("NEWSJN_FROM",    "newsjunction.im@nirmauni.ac.in")),
    ("CULT",      "The Cultural Committee",     os.environ.get("CULT_FROM",      "cultcomm.im@nirmauni.ac.in")),
    ("PRATIKRITI","Photography Club",           os.environ.get("PRATIKRITI_FROM","pratikriti.im@nirmauni.ac.in")),
    ("CLIQUE",    "The IT Club",                os.environ.get("CLIQUE_FROM",    "clique.im@nirmauni.ac.in")),
    ("XQUIZIT",   "Quiz Club",                  os.environ.get("XQUIZIT_FROM",   "xquizit.im@nirmauni.ac.in")),
    ("SPORTZZZ",  "Sports Committee",           os.environ.get("SPORTZZZ_FROM",  "sportzzzcomm.im@nirmauni.ac.in")),
    ("OPTIMUS",   "Operations Club",            os.environ.get("OPTIMUS_FROM",   "optimus.im@nirmauni.ac.in")),
    ("SIP",       "Summer Internship",          os.environ.get("SIP_FROM",       "summerpc.imnu@nirmauni.ac.in")),
]
def msg_date(msg):
    try: return parsedate_to_datetime(msg.get("Date")).date().isoformat()
    except Exception: return None
updates = []
_today = datetime.date.today()
_month = _today.strftime("%Y-%m")                       # current year-month
since_u = _today.replace(day=1).strftime("%d-%b-%Y")    # 1st of this month
for code, cname, addr in COMMITTEES:
    try:
        typ, data = M.search(None, "FROM", addr, "SINCE", since_u)
        for num in data[0].split()[-15:][::-1]:         # this month's mails per committee
            typ, md = M.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(md[0][1])
            subj = re.sub(r"\s+", " ", decode(msg.get("Subject", ""))).strip()
            if not subj:
                continue
            d = msg_date(msg)
            if not d or d[:7] != _month:                # current month only
                continue
            raw = body_text(msg)
            body = re.sub(r"\s+", " ", raw).strip()                        # one-line, for the short snippet
            full = re.sub(r"[ \t]+", " ", raw)                             # keep line breaks for the full read
            full = re.sub(r"\n[ \t]*(\n[ \t]*)+", "\n\n", full).strip()    # collapse runs of blank lines
            updates.append({"code": code, "committee": cname, "subject": subj[:140],
                            "date": d, "snippet": body[:200], "body": full[:1600], "from": addr})
    except Exception as e:
        print(f"Committee fetch skipped ({code}):", e)
updates.sort(key=lambda u: (u["date"] or ""), reverse=True)
updates = updates[:120]
try:
    os.makedirs(os.path.dirname(UPDATES_OUT) or ".", exist_ok=True)
    json.dump(updates, open(UPDATES_OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Parsed {len(updates)} committee update(s) -> {UPDATES_OUT}")
except Exception as e:
    print("Committee updates write skipped:", e)

# ---- 2) schedule attachment (required) ----
# Only consider recent mail (bounds the search; never reaches back to ancient threads).
SCHED_SINCE_DAYS = int(os.environ.get("SCHEDULE_SINCE_DAYS", "180"))
SCHED_GRACE_DAYS = int(os.environ.get("SCHEDULE_GRACE_DAYS", "10"))
TODAY_IST = (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).date()
since_s = (TODAY_IST - datetime.timedelta(days=SCHED_SINCE_DAYS)).strftime("%d-%b-%Y")

crit = (["FROM", SENDER] if SENDER else []) + ["SINCE", since_s]
typ, data = M.search(None, *crit)
ids = data[0].split()
if not ids:
    M.logout(); sys.exit(f"No emails from {SENDER or 'anyone'} since {since_s} — not publishing.")

skipped = []   # reasons, for a clear log if nothing usable is found
for num in reversed(ids):                 # newest first
    typ, md = M.fetch(num, "(RFC822)")
    msg = email.message_from_bytes(md[0][1])
    subj = decode(msg.get("Subject", ""))
    if not _sender_ok(msg):               # exact-sender guard (IMAP FROM is only a hint)
        skipped.append(f"from {_addr_of(msg)!r} != {SENDER!r}")
        continue
    if SUBJ and SUBJ.lower() not in subj.lower():
        continue
    for part in msg.walk():
        fn = part.get_filename()
        if not (fn and decode(fn).lower().endswith((".xlsx", ".xls"))):
            continue
        fn = decode(fn)
        ds = _name_dates(fn)              # staleness guard: reject an old re-sent schedule
        if ds and max(ds) < TODAY_IST - datetime.timedelta(days=SCHED_GRACE_DAYS):
            skipped.append(f"{fn!r} stale (range ends {max(ds)})")
            continue
        raw = part.get_payload(decode=True)
        ok = _looks_like_schedule(raw)    # is this really the timetable, not a stray .xlsx?
        if ok is False:
            skipped.append(f"{fn!r} not a valid timetable (no course-detail/grid)")
            continue
        os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
        open(OUT, "wb").write(raw)
        rng = f", covers {min(ds)}..{max(ds)}" if ds else ""
        warn = "" if ok else "  [WARN: openpyxl unavailable, accepted unchecked]"
        print(f"Saved {fn!r} (from {_addr_of(msg)}, subject {subj!r}{rng}) -> {OUT}{warn}")
        M.logout(); sys.exit(0)
M.logout()
# Nothing valid arrived by mail. If a known-good schedule is already committed
# to the repo, keep publishing with it rather than freezing the site for a week.
if os.path.exists(OUT) and os.path.getsize(OUT) > 0:
    print(f"No fresh valid timetable by email; keeping the committed {OUT}."
          + (" Skipped: " + "; ".join(skipped[:6]) if skipped else ""))
    sys.exit(0)
sys.exit("No fresh .xlsx schedule from the expected sender and no committed fallback — not publishing. "
         + ("Skipped: " + "; ".join(skipped[:6]) if skipped else ""))
