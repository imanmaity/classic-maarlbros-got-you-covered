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

# ---- trust guards ----
def _addr_of(msg):
    return parseaddr(decode(msg.get("From", "")))[1].strip().lower()

def _sender_ok(msg):
    if not SENDER:
        return True
    addr, want = _addr_of(msg), SENDER.strip().lower()
    if not addr:
        return False
    if "@" in want:
        return addr == want
    return addr.split("@")[-1] == want            

def _name_dates(fn):
    out = []
    for d, m, y in re.findall(r'(\d{1,2})[._\-/](\d{1,2})[._\-/](\d{2,4})', fn or ""):
        y = int(y); y = 2000 + y if y < 100 else y
        try: out.append(datetime.date(y, int(m), int(d)))
        except ValueError:
            try: out.append(datetime.date(y, int(d), int(m)))
            except ValueError: pass
    return out

def _looks_like_schedule(raw):
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

ROOM_RE = r'(?:[A-Za-z]{1,4}-?\d{1,3}[A-Za-z]?|\d{2,4}-[A-Za-z]{1,2}|\d{3}\s[A-Za-z](?![A-Za-z])|\d{3}[A-Za-z]?)'
_WEEKDAYS = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4,"saturday":5,"sunday":6}

def _room_norm(s):
    s = re.sub(r'\s+', '', str(s)).upper()                 
    s = re.sub(r'^(\d{2,4})([A-Z]{1,2})$', r'\1-\2', s)    
    return s

def _venue_label(s):
    s = str(s).strip().lower()
    if 'zoom' in s:  return 'Zoom'
    if 'webex' in s: return 'Webex'
    if 'meet' in s:  return 'Google Meet'
    if 'team' in s:  return 'MS Teams'
    if re.search(r'online|virtual|classroom', s): return 'Online'
    return re.sub(r'\s+', ' ', s).title()

def _venue_events(t):
    online = (r'(?:online|virtually|virtual\s+mode|ms\s*-?\s*teams|microsoft\s*teams|'
              r'google\s*meet|g-?meet|zoom(?:\s*(?:call|meeting|link))?|webex|google\s*classroom)')
    hall   = (r'(?:auditorium|amphitheat(?:re|er)|seminar\s*hall|conference\s*(?:room|hall)|'
              r'board\s*room|(?:computer\s*)?lab(?:oratory)?|library)')
    cue = (r'(?:held|conducted|conduct\w*|shifted|moved|take\s*place|takes?\s*place|'
           r'venue|be\s+held|arranged)\b[^.\n]{0,25}?\b(?:in|to|at|via|on|through|:)\s*(?:the\s+|a\s+)?')
    ev = []
    for m in re.finditer(cue + r'(' + online + r'|' + hall + r')', t, re.I):
        ev.append((m.start(), _venue_label(m.group(1)), None))
    for m in re.finditer(r'\b(' + online + r')\b', t, re.I):   
        ev.append((m.start(), _venue_label(m.group(1)), None))
    return ev

_CHANGE_SUBJECT_RE = re.compile(
    r'postpon|prepon|reschedul|cancel|class\s*-?\s*room|classroom|\bvenue\b|\broom\b|'
    r'change\s+in\s+(?:class|schedule|time|timing|venue)', re.I)

def _divs(group):
    g = (group or "").strip()
    if re.search(r'\b(?:all|both|entire|every|each)\b', g, re.I):
        return [""]
    return [d.upper() for d in re.findall(r'(?<![A-Za-z.])([A-Ha-h])(?![A-Za-z.])', g)]

def _bare_codes(text):
    stop = {"MBA", "IMBA", "BTECH", "IIM", "PDF", "FYI", "TBA", "AM", "PM",
            "LH", "NOTE", "ALL", "AND", "FOR", "THE", "ARE", "IS"}
    t = text
    while re.search(r'\([^()]*\)', t):
        t = re.sub(r'\([^()]*\)', ' ', t)
    out = []
    def add(a):
        a = a.upper()
        if a not in stop and a not in out:
            out.append(a)
    for ab in re.findall(r'\b([A-Z][A-Z&]{1,5})\b\s+(?i:sessions?|classes?|lectures?|scheduled|additional)\b', t):
        add(ab)                                   
    for sent in re.split(r'\n|(?<!\d)\.(?!\d)', t):   
        if re.search(r'(?i:postpon\w*|prepon\w*|reschedul\w*|cancel\w*|not\s+be\s+held|revis\w*|additional)', sent):
            for ab in re.findall(r'\b([A-Z][A-Z&]{1,5})\b', sent):   
                add(ab)
    return out

def _secs_in(t):
    s = []
    for ab, dvgroup in re.findall(r'([A-Za-z&]{2,6})\(\s*([A-Za-z][A-Za-z&,\s]*?)\s*\)', t):
        for dv in _divs(dvgroup):
            s.append((ab, dv))
    return s

def _detect_rooms(t):
    nr = orr = None
    m = re.search(r'\b(' + ROOM_RE + r')\s+to\s+(' + ROOM_RE + r')\b', t, re.I)   
    if m: orr, nr = _room_norm(m.group(1)), _room_norm(m.group(2))
    if nr is None:                                                               
        m = re.search(r'\b(' + ROOM_RE + r')\s+class\s*-?\s*room\b', t, re.I)
        if m: nr = _room_norm(m.group(1))
    if nr is None:                                                               
        m = re.search(r'(?:held|conducted|shifted|moved|take\s*place|venue|class\s*-?\s*room|classroom|room|hall)\b'
                      r'[^.\n]{0,25}?\b(?:in|to|at|:)\s*(?:room\s*(?:no\.?)?\s*|class\s*-?\s*room\s*|venue\s*|hall\s*)?'
                      r'(' + ROOM_RE + r')\b', t, re.I)
        if m: nr = _room_norm(m.group(1))
    if orr is None:                                                              
        m = re.search(r'(?:instead of|in place of|rather than|in lieu of|not in)\s+(?:room\s*)?(' + ROOM_RE + r')\b', t, re.I)
        if m: orr = _room_norm(m.group(1))
    if nr is None:                                                               
        _vv = _venue_events(t)
        if _vv: nr = _vv[0][1]
    return nr, orr

def _room_events(t):
    ev = []
    for m in re.finditer(r'\b(' + ROOM_RE + r')\s+to\s+(' + ROOM_RE + r')\b', t, re.I):  
        ev.append((m.start(), _room_norm(m.group(2)), _room_norm(m.group(1))))
    for m in re.finditer(r'\b(' + ROOM_RE + r')\s+class\s*-?\s*room\b', t, re.I):          
        ev.append((m.start(), _room_norm(m.group(1)), None))
    for m in re.finditer(r'(?:held|conducted|shifted|moved|take\s*place|venue|class\s*-?\s*room|classroom|room|hall)\b'
                         r'[^.\n]{0,25}?\b(?:in|to|at|:)\s*(?:room\s*(?:no\.?)?\s*|class\s*-?\s*room\s*|venue\s*|hall\s*)?'
                         r'(' + ROOM_RE + r')\b', t, re.I):                                 
        ev.append((m.start(), _room_norm(m.group(1)), None))
    ev.extend(_venue_events(t))                                                              
    ev.sort(key=lambda e: e[0])
    return ev

def _clauses(t):
    segs = re.split(r'(?:\s*\b\d+\)\s*)|(?<=[.;])\s+', t)
    return [s for s in segs if s and s.strip()]

def parse_change(text, edate=None):
    edate = edate or datetime.date.today()
    
    text = re.sub(r'from\s*05:00\s*[Pp][Mm]\s*is\s*continued\s*till\s*07:10\s*[Pp][Mm]', '05:00 PM to 06:00 PM and 06:10 PM to 07:10 PM', text, flags=re.I)
    text = re.sub(r'\b([A-Z][A-Z&]{1,5})\s+\(\s*([A-Za-z][A-Za-z&,\s]*?)\s*\)', r'\1(\2)', text)
    while True:
        new_text = re.sub(
            r'\b([A-Z][A-Z&]{1,5})\(\s*([A-Za-z][A-Za-z&,\s]*?)\s*\)((?:\s*[,.&]\s*|\s+(?:and|&)\s+|\s+)*)\(\s*([A-Ha-h])\s*\)',
            r'\1(\2)\3\1(\4)',
            text
        )
        if new_text == text:
            break
        text = new_text

    text = re.sub(r'\(\s*([A-Za-z][A-Za-z&]{1,5})\s*\)\s*(\(\s*[A-Za-z])', r'\1\2', text)
    text = text.replace("*", " ").replace("'", "")
    text = re.sub(r'\b([A-Z][A-Z&]{1,5})\s*-\s*([A-Ha-h])\b(?![A-Za-z0-9])', r'\1(\2)', text)
    text = re.sub(r'-{3,}\s*forwarded message\s*-{3,}', ' ', text, flags=re.I)
    text = re.sub(r'(?im)^\s*(?:from|to|cc|bcc|date|sent|subject|reply-to)\s*:[^\n]*', ' ', text)
    
    secs = []
    for ab, dvgroup in re.findall(r'([A-Za-z&]{2,6})\(\s*([A-Za-z][A-Za-z&,\s]*?)\s*\)', text):
        for dv in _divs(dvgroup):
            secs.append((ab, dv))
    for _ab in _bare_codes(text):
        if not any(a.upper() == _ab for a, _ in secs) and (_ab, "") not in secs:
            secs.append((_ab, ""))
    if not secs: return []
    
    _dtext = re.sub(r'(?:sent|dated|circulated|issued|shared|vide|'
                    r'as\s+per\s+(?:the\s+)?(?:schedule|circular|notice|mail|email))'
                    r'[^.\n]{0,20}?\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', ' ', text, flags=re.I)
    raw_dates = re.findall(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', _dtext)
    raw_dates = [(d, m, y) for d, m, y in raw_dates if 1 <= int(m) <= 12 and 1 <= int(d) <= 31]
    
    def _yr(y):
        v = int(('20' + y) if len(y) == 2 else y)
        return edate.year if abs(v - edate.year) > 1 else v
        
    dates = [f"{_yr(y):04d}-{int(m):02d}-{int(d):02d}" for d, m, y in raw_dates]
    dates = list(dict.fromkeys(dates))
    
    tmatches = re.findall(r'(\d{1,2}[:.]\d{2})\s*(?:[AaPp][Mm]\s*)?(?:[-\u2013\u2014]|to|till|until|is\s+continued\s+till)\s*\d{1,2}[:.]\d{2}\s*([AaPp][Mm])?', text, flags=re.I)
    starts = [s.replace('.', ':') for s, _ in tmatches]
    meris = [m.upper() for _, m in tmatches]
    known = [m for m in meris if m]
    fill = known[-1] if known and len(set(known)) == 1 else None
    times = [s + (m if m else (fill or "")) for s, m in zip(starts, meris)]
    
    low = text.lower()
    ctype = ('Preponed' if 'prepon' in low else 'Postponed' if 'postpon' in low
             else 'Cancelled' if ('cancel' in low or 'not be held' in low)
             else 'Rescheduled' if ('reschedul' in low or 'shift' in low or 'additional' in low) else 'Changed')
    
    old_date = dates[0] if dates else None
    new_date = dates[-1] if len(dates) >= 2 else None
    tba = len(times) == 0 
    
    def day(ds):
        try: return datetime.date.fromisoformat(ds).strftime("%A")
        except Exception: return None
        
    def _add(n): return (edate + datetime.timedelta(days=n)).isoformat()
    rel_date = None
    if   re.search(r'\bday\s+after\s+tomorrow\b', low): rel_date = _add(2)
    elif re.search(r'\btomorrow\b', low):              rel_date = _add(1)
    elif re.search(r'\btoday\b', low):                 rel_date = _add(0)
    else:
        wd = re.search(r'\b(?:on|this|coming)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', low)
        if wd:
            rel_date = _add((_WEEKDAYS[wd.group(1)] - edate.weekday()) % 7)
    if not dates and rel_date is None:
        rel_date = _add(1)
        
    new_room, old_room = _detect_rooms(text)
    has_time_shift = bool(times)
    has_date_shift = bool(new_date) and (new_date != old_date)
    is_room_change = (new_room is not None) and not has_time_shift and not has_date_shift \
                     and not any(k in low for k in ('postpon', 'prepon', 'cancel'))
                     
    cut = len(text)
    for pat in (r'\bregards\b', r'\bthanks\b', r'\bthank you\b', r'\bwarm regards\b',
                r'\bbest regards\b', r'\bsincerely\b', r'\byours\b',
                r'(MBA\s+)?Programme Office'):
        mm = re.search(pat, text, re.I)
        if mm: cut = min(cut, mm.start())
    raw = re.sub(r'\s+', ' ', text[:cut]).strip()[:400]
    out = []
    
    _acts = [(p, 'room', (nr, orr)) for p, nr, orr in _room_events(text)]
    for m in re.finditer(r'(?i:postpon\w*|prepon\w*|reschedul\w*|cancel\w*|not\s+be\s+held|revis\w*|additional)', text):
        w = m.group(0).lower()
        _acts.append((m.start(), 'verb',
                      'Preponed' if 'prepon' in w else 'Postponed' if 'postpon' in w
                      else 'Cancelled' if ('cancel' in w or 'not' in w) else 'Rescheduled' if ('reschedul' in w or 'additional' in w) else 'Changed'))
    _acts.sort(key=lambda e: e[0])
    
    _pos = {}
    for sm in re.finditer(r'([A-Za-z&]{2,6})\(\s*([A-Za-z][A-Za-z&,\s]*?)\s*\)', text):
        for dv in _divs(sm.group(2)):
            _pos.setdefault((sm.group(1).upper(), dv.upper()), sm.start())
            
    room_secs, room_of, verb_secs, verb_of = [], {}, [], {}
    for ab, dv in secs:
        key = (ab.upper(), dv.upper())
        if key in room_of or key in verb_of:
            continue
        p = _pos.get(key)
        if p is None:                                     
            mm = re.search(r'\b' + re.escape(ab.upper()) + r'\b', text)   
            if mm: p = mm.start()                         
        act = next((e for e in _acts if e[0] >= p), None) if p is not None else None
        if act is None:                                   
            act = (0, 'room', (new_room, old_room)) if is_room_change else (0, 'verb', ctype)
        if act[1] == 'room' and act[2][0] is not None and not has_time_shift:
            room_secs.append(key); room_of[key] = (act[2][0], act[2][1] or old_room)
        else:
            verb_secs.append(key); verb_of[key] = act[2] if act[1] == 'verb' else ctype
            
    if room_secs:
        d0 = old_date or new_date or rel_date or edate.isoformat()
        d_day = day(d0); hhmm = times[0] if len(times) == 1 else None
        for key in room_secs:
            nr, orr = room_of[key]
            out.append({"abbr": key[0], "division": key[1], "type": "Room Change",
                        "old_date": d0, "old_day": d_day, "new_date": d0, "new_day": d_day,
                        "old_hhmm": hhmm, "new_hhmm": hhmm,
                        "old_room": orr, "new_room": nr, "tba": False, "raw": raw})
                        
    if verb_secs:
        if old_date is None and rel_date:
            old_date = rel_date
            if new_date is None and not times: new_date = rel_date
        if new_date is None and times and old_date and ctype in ('Changed', 'Rescheduled'):
            new_date = old_date
            
        _has_target = bool(re.search(r'\bto\s+\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', low))
        _multi = (len(dates) >= 2 and not _has_target)
        
        for i, key in enumerate(verb_secs):
            vt = verb_of[key]
            
            if not times:                      
                sec_times = [None]
            elif len(times) == len(verb_secs): 
                sec_times = [times[i]]
            elif len(verb_secs) == 1:
                sec_times = times
            elif len(times) == 1:              
                sec_times = [times[0]]
            else:                              
                sec_times = [times[i] if i < len(times) else times[-1]]

            if _multi:
                for ds in dates:
                    for hhmm in sec_times:
                        nd = None if vt in ('Postponed', 'Cancelled') else ds
                        nh = None if vt in ('Postponed', 'Cancelled') else hhmm
                        is_tba = True if vt in ('Postponed', 'Cancelled') else tba
                        out.append({"abbr": key[0], "division": key[1], "type": vt,
                                    "old_date": ds, "old_day": day(ds), "new_date": nd, "new_day": day(nd),
                                    "new_hhmm": nh, "old_room": old_room, "new_room": new_room, "tba": is_tba, "raw": raw})
            else:
                for hhmm in sec_times:
                    out.append({"abbr": key[0], "division": key[1], "type": vt,
                                "old_date": old_date, "old_day": day(old_date),
                                "new_date": new_date, "new_day": day(new_date),
                                "new_hhmm": hhmm, "old_room": old_room, "new_room": new_room, "tba": tba, "raw": raw})
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
        if not _sender_ok(msg): continue      
        _subj = decode(msg.get("Subject", "")).lower()
        if CHANGE_SUBJECT.lower() not in _subj and not _CHANGE_SUBJECT_RE.search(_subj):
            continue
        try: _edate = parsedate_to_datetime(msg.get("Date")).date()
        except Exception: _edate = datetime.date.today()
        for c in parse_change(body_text(msg), _edate):
            key = (c["abbr"], c["division"], c["old_date"], c["new_date"], c["new_hhmm"], c["type"])
            if key not in seen:
                changes.append(c); seen.add(key)
                
    # --- START OF FORCED MANUAL OVERRIDE ---
    forced_changes = [
        # PML Postponements (July 29 & 31)
        {"abbr": "PML", "division": "", "type": "Postponed", "old_date": "2026-07-29", "old_day": "Wednesday", "new_date": None, "new_day": None, "old_hhmm": None, "new_hhmm": None, "old_room": None, "new_room": None, "tba": True, "raw": "MANUAL OVERRIDE: PML Postponed"},
        {"abbr": "PML", "division": "", "type": "Postponed", "old_date": "2026-07-31", "old_day": "Friday", "new_date": None, "new_day": None, "old_hhmm": None, "new_hhmm": None, "old_room": None, "new_room": None, "tba": True, "raw": "MANUAL OVERRIDE: PML Postponed"},

        # SBM (C) in E3 (30.07.2026)
        {"abbr": "SBM", "division": "C", "type": "Rescheduled", "old_date": "2026-07-30", "old_day": "Thursday", "new_date": "2026-07-30", "new_day": "Thursday", "old_hhmm": None, "new_hhmm": "05:00PM", "old_room": None, "new_room": "E3", "tba": False, "raw": "MANUAL OVERRIDE: SBM (C) in E3"},
        {"abbr": "SBM", "division": "C", "type": "Rescheduled", "old_date": "2026-07-30", "old_day": "Thursday", "new_date": "2026-07-30", "new_day": "Thursday", "old_hhmm": None, "new_hhmm": "06:00PM", "old_room": None, "new_room": "E3", "tba": False, "raw": "MANUAL OVERRIDE: SBM (C) in E3"},
        
        # SBM (C) in E3 (01.08.2026)
        {"abbr": "SBM", "division": "C", "type": "Rescheduled", "old_date": "2026-08-01", "old_day": "Saturday", "new_date": "2026-08-01", "new_day": "Saturday", "old_hhmm": None, "new_hhmm": "05:00PM", "old_room": None, "new_room": "E3", "tba": False, "raw": "MANUAL OVERRIDE: SBM (C) in E3"},
        {"abbr": "SBM", "division": "C", "type": "Rescheduled", "old_date": "2026-08-01", "old_day": "Saturday", "new_date": "2026-08-01", "new_day": "Saturday", "old_hhmm": None, "new_hhmm": "06:00PM", "old_room": None, "new_room": "E3", "tba": False, "raw": "MANUAL OVERRIDE: SBM (C) in E3"},

        # SDM (C) in E2 (30.07.2026 & 01.08.2026)
        {"abbr": "SDM", "division": "C", "type": "Changed", "old_date": "2026-07-30", "old_day": "Thursday", "new_date": "2026-07-30", "new_day": "Thursday", "old_hhmm": None, "new_hhmm": "06:10PM", "old_room": None, "new_room": "E2", "tba": False, "raw": "MANUAL OVERRIDE: SDM (C) in E2"},
        {"abbr": "SDM", "division": "C", "type": "Changed", "old_date": "2026-08-01", "old_day": "Saturday", "new_date": "2026-08-01", "new_day": "Saturday", "old_hhmm": None, "new_hhmm": "06:10PM", "old_room": None, "new_room": "E2", "tba": False, "raw": "MANUAL OVERRIDE: SDM (C) in E2"},

        # SDM (B) in E2 (30.07.2026 & 01.08.2026)
        {"abbr": "SDM", "division": "B", "type": "Changed", "old_date": "2026-07-30", "old_day": "Thursday", "new_date": "2026-07-30", "new_day": "Thursday", "old_hhmm": None, "new_hhmm": "07:20PM", "old_room": None, "new_room": "E2", "tba": False, "raw": "MANUAL OVERRIDE: SDM (B) in E2"},
        {"abbr": "SDM", "division": "B", "type": "Changed", "old_date": "2026-08-01", "old_day": "Saturday", "new_date": "2026-08-01", "new_day": "Saturday", "old_hhmm": None, "new_hhmm": "07:20PM", "old_room": None, "new_room": "E2", "tba": False, "raw": "MANUAL OVERRIDE: SDM (B) in E2"}
    ]
    changes.extend(forced_changes)
    # --- END OF FORCED MANUAL OVERRIDE ---

    os.makedirs(os.path.dirname(CHANGES_OUT) or ".", exist_ok=True)
    json.dump(changes, open(CHANGES_OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"[fetch_email] Parsed {len(changes)} change notice(s) -> {CHANGES_OUT}")
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
            if _addr_of(msg) != addr.strip().lower(): continue 
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
SCHED_SINCE_DAYS = int(os.environ.get("SCHEDULE_SINCE_DAYS", "180"))
SCHED_GRACE_DAYS = int(os.environ.get("SCHEDULE_GRACE_DAYS", "10"))
TODAY_IST = (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).date()
since_s = (TODAY_IST - datetime.timedelta(days=SCHED_SINCE_DAYS)).strftime("%d-%b-%Y")

crit = (["FROM", SENDER] if SENDER else []) + ["SINCE", since_s]
typ, data = M.search(None, *crit)
ids = data[0].split()
if not ids:
    M.logout(); sys.exit(f"No emails from {SENDER or 'anyone'} since {since_s} — not publishing.")

skipped = []   
for num in reversed(ids):                 
    typ, md = M.fetch(num, "(RFC822)")
    msg = email.message_from_bytes(md[0][1])
    subj = decode(msg.get("Subject", ""))
    if not _sender_ok(msg):               
        skipped.append(f"from {_addr_of(msg)!r} != {SENDER!r}")
        continue
    if SUBJ and SUBJ.lower() not in subj.lower():
        continue
    for part in msg.walk():
        fn = part.get_filename()
        if not (fn and decode(fn).lower().endswith((".xlsx", ".xls"))):
            continue
        fn = decode(fn)
        ds = _name_dates(fn)              
        if ds and max(ds) < TODAY_IST - datetime.timedelta(days=SCHED_GRACE_DAYS):
            skipped.append(f"{fn!r} stale (range ends {max(ds)})")
            continue
        raw = part.get_payload(decode=True)
        ok = _looks_like_schedule(raw)    
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

if os.path.exists(OUT) and os.path.getsize(OUT) > 0:
    print(f"No fresh valid timetable by email; keeping the committed {OUT}."
          + (" Skipped: " + "; ".join(skipped[:6]) if skipped else ""))
    sys.exit(0)
sys.exit("No fresh .xlsx schedule from the expected sender and no committed fallback — not publishing. "
         + ("Skipped: " + "; ".join(skipped[:6]) if skipped else ""))
