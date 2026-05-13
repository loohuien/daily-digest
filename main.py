from datetime import datetime
from feeds import collect_items
from emailer import build_full_html_digest, build_email_overview, send_email

FULL_DIGEST_URL = "https://loohuien.github.io/personal-digest/digest.html"

items = collect_items()

full_html = build_full_html_digest(items)
overview_html = build_email_overview(items, full_digest_url=FULL_DIGEST_URL)

with open("output/digest.html", "w", encoding="utf-8") as f:
    f.write(full_html)

today = datetime.now().strftime("%d %b %Y")
subject = f"Daily Intelligence Digest — {today}"

send_email(subject, overview_html)

print("Overview email sent. Full digest saved to output/digest.html.")