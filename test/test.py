import imaplib
from dotenv import load_dotenv
import os

load_dotenv()

print(os.getenv("NAVER_ID"))
print(os.getenv("NAVER_PASSWORD"))

imap = imaplib.IMAP4_SSL("imap.naver.com")
imap.login(os.getenv("NAVER_ID"), os.getenv("NAVER_PASSWORD"))
imap.select("INBOX")
typ, data = imap.search(None, "ALL")

print(data)