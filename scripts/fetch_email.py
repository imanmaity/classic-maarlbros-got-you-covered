#!/usr/bin/env python3
"""Fetch the newest schedule .xlsx attachment from the admin's email via IMAP.

Env vars (set as GitHub repository secrets):
  MAIL_USER     your mailbox address           e.g. you@gmail.com
  MAIL_PASS     an APP PASSWORD (not your login password)
  SENDER        admin's address to filter on   e.g. timetable@nirmauni.ac.in
  IMAP_HOST     optional, default imap.gmail.com
  MAIL_SUBJECT  optional substring required in the subject line

Saves the newest matching attachment to argv[1] (default rosters/schedule_latest.xlsx).
Exits non-zero if nothing matches, so the workflow never publishes stale data.
"""
import imaplib, email, os, sys
from email.header import decode_header

OUT  = sys.argv[1] if len(sys.argv) > 1 else "rosters/schedule_latest.xlsx"
HOST = os.environ.get("IMAP_HOST", "imap.gmail.com")
USER = os.environ.get("MAIL_USER"); PWD = os.environ.get("MAIL_PASS")
SENDER = os.environ.get("SENDER", "mba.im@nirmauni.ac.in"); SUBJ = os.environ.get("MAIL_SUBJECT", "")
if not (USER and PWD):
    sys.exit("MAIL_USER / MAIL_PASS not set.")

def decode(s):
    return "".join(p.decode(enc or "utf-8", "ignore") if isinstance(p, bytes) else p
                   for p, enc in decode_header(s or ""))

M = imaplib.IMAP4_SSL(HOST); M.login(USER, PWD); M.select("INBOX")
crit = ["FROM", SENDER] if SENDER else ["ALL"]
typ, data = M.search(None, *crit)
ids = data[0].split()
if not ids:
    M.logout(); sys.exit(f"No emails found from {SENDER or 'anyone'}.")
for num in reversed(ids):
    typ, md = M.fetch(num, "(RFC822)")
    msg = email.message_from_bytes(md[0][1])
    if SUBJ and SUBJ.lower() not in decode(msg.get("Subject")).lower():
        continue
    for part in msg.walk():
        fn = part.get_filename()
        if fn and decode(fn).lower().endswith((".xlsx", ".xls")):
            os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
            open(OUT, "wb").write(part.get_payload(decode=True))
            print(f"Saved {decode(fn)!r} (subject: {decode(msg.get('Subject'))!r}) -> {OUT}")
            M.logout(); sys.exit(0)
M.logout(); sys.exit("No .xlsx attachment found in matching emails — not publishing.")
