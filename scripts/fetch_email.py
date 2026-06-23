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

def parse_change(text):
    # sections like "SBM(A)", "SBM(A & B)", "SDM(A), SDM(B)" -> one (abbr, division) per division
    secs = []
    for ab, dvgroup in re.findall(r'([A-Za-z&]{2,6})\(\s*([A-Za-z][A-Za-z&,\s]*?)\s*\)', text):
        for dv in re.findall(r'[A-Za-z]', dvgroup):
            secs.append((ab, dv))
    if not secs: return []
    raw_dates = re.findall(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', text)
    dates = [f"{int(('20'+y) if len(y)==2 else y):04d}-{int(m):02d}-{int(d):02d}" for d, m, y in raw_dates]
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
             else 'Cancelled' if 'cancel' in low
             else 'Rescheduled' if ('reschedul' in low or 'shift' in low) else 'Changed')
    old_date = dates[0] if dates else None
    new_date = dates[-1] if len(dates) >= 2 else None
    tba = len(times) == 0  # no new time announced -> "to be announced"
    def day(ds):
        try: return datetime.date.fromisoformat(ds).strftime("%A")
        except Exception: return None
    # keep the message, drop the office sign-off / signature
    cut = len(text)
    for pat in (r'\bregards\b', r'\bthanks\b', r'\bthank you\b', r'\bwarm regards\b',
                r'\bbest regards\b', r'\bsincerely\b', r'\byours\b',
                r'(MBA\s+)?Programme Office'):
        mm = re.search(pat, text, re.I)
        if mm: cut = min(cut, mm.start())
    raw = re.sub(r'\s+', ' ', text[:cut]).strip()[:400]
    out = []
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
        if CHANGE_SUBJECT.lower() not in decode(msg.get("Subject", "")).lower():
            continue
        for c in parse_change(body_text(msg)):
            # dedup by the actual change (subject + division + dates + time), NOT by the shared
            # message text -- otherwise a single mail naming two divisions keeps only one of them
            key = (c["abbr"], c["division"], c["old_date"], c["new_date"], c["new_hhmm"], c["type"])
            if key not in seen:
                changes.append(c); seen.add(key)
    os.makedirs(os.path.dirname(CHANGES_OUT) or ".", exist_ok=True)
    json.dump(changes, open(CHANGES_OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Parsed {len(changes)} change notice(s) -> {CHANGES_OUT}")
except Exception as e:
    print("Change-notice fetch skipped:", e)

# ---- 2) schedule attachment (required) ----
crit = ["FROM", SENDER] if SENDER else ["ALL"]
typ, data = M.search(None, *crit)
ids = data[0].split()
if not ids:
    M.logout(); sys.exit(f"No emails found from {SENDER or 'anyone'}.")
for num in reversed(ids):
    typ, md = M.fetch(num, "(RFC822)")
    msg = email.message_from_bytes(md[0][1])
    if SUBJ and SUBJ.lower() not in decode(msg.get("Subject", "")).lower():
        continue
    for part in msg.walk():
        fn = part.get_filename()
        if fn and decode(fn).lower().endswith((".xlsx", ".xls")):
            os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
            open(OUT, "wb").write(part.get_payload(decode=True))
            print(f"Saved {decode(fn)!r} (subject: {decode(msg.get('Subject',''))!r}) -> {OUT}")
            M.logout(); sys.exit(0)
M.logout(); sys.exit("No .xlsx attachment found in matching emails — not publishing.")
