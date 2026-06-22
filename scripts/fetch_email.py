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
    secs = re.findall(r'([A-Za-z&]{2,6})\(\s*([A-Za-z])\s*\)', text)
    if not secs: return []
    raw_dates = re.findall(r'(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})', text)
    dates = [f"{int(('20'+y) if len(y)==2 else y):04d}-{int(m):02d}-{int(d):02d}" for d, m, y in raw_dates]
    times = [t.replace('.', ':') for t in re.findall(r'(\d{1,2}[:.]\d{2})\s*[-to]+\s*\d{1,2}[:.]\d{2}', text)]
    low = text.lower()
    ctype = ('Preponed' if 'prepon' in low else 'Postponed' if 'postpon' in low
             else 'Cancelled' if 'cancel' in low
             else 'Rescheduled' if ('reschedul' in low or 'shift' in low) else 'Changed')
    old_date = dates[0] if dates else None
    new_date = dates[-1] if len(dates) >= 2 else (dates[0] if dates else None)
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
        hhmm = (times[i] if len(times) == len(secs) else times[0] if len(times) == 1
                else (times[i] if i < len(times) else None)) if times else None
        out.append({"abbr": ab.upper(), "division": dv.upper(), "type": ctype,
                    "old_date": old_date, "old_day": day(old_date),
                    "new_date": new_date, "new_day": day(new_date),
                    "new_hhmm": hhmm, "raw": raw})
    return out

M = imaplib.IMAP4_SSL(HOST); M.login(USER, PWD); M.select("INBOX")

# ---- 1) change notices (best effort) ----
changes, seen_raw = [], set()
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
            if c["raw"] not in seen_raw:
                changes.append(c); seen_raw.add(c["raw"])
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
