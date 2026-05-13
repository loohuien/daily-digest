from datetime import datetime
import html
import os
import smtplib
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dotenv import load_dotenv


SECTION_STYLES = {
    "Academic Papers": ("🎓 Academic Papers", "#6b4f3a"),
    "AI Labs": ("🤖 AI Labs", "#7c3f2c"),
    "Singapore Policy": ("🇸🇬 Singapore Policy", "#9a3412"),
    "Tech News": ("💻 Tech News", "#5c4033"),
    "Other News": ("📰 Other News", "#4b3a2f"),
}


def short_summary(text, max_words=35):
    if not text:
        return "No summary available."
    clean = " ".join(text.split())
    words = clean.split()
    return clean if len(words) <= max_words else " ".join(words[:max_words]) + "..."


def classify_section(item):
    source = item.get("source", "")
    category = item.get("category", "")

    if category == "Academic Papers":
        return "Academic Papers"
    if any(x in source for x in ["OpenAI", "Anthropic", "DeepMind"]):
        return "AI Labs"
    if "CNA" in source or "Straits Times" in source:
        return "Singapore Policy"
    if any(x in source for x in ["Verge", "Technology Review", "MIT"]):
        return "Tech News"
    return "Other News"


def build_full_html_digest(items):
    today = datetime.now().strftime("%d %B %Y")
    grouped = defaultdict(list)

    for item in items:
        grouped[classify_section(item)].append(item)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#3b2a20; font-family:Arial, Helvetica, sans-serif; color:#2d241c;">
      <div style="max-width:820px; margin:0 auto; padding:34px 18px;">

        <div style="background:#4b2e22; border-radius:22px; padding:34px; color:white;">
          <p style="font-size:13px; letter-spacing:1.2px; text-transform:uppercase; margin:0;">
            🌐 Personal Decentralized Briefing
          </p>

          <h1 style="font-size:34px; margin:10px 0 6px 0;">
            ☕ Daily Intelligence Digest
          </h1>

          <p style="font-size:15px; margin:0;">
            {today} · 🎓 Papers · 🤖 AI Labs · 🇸🇬 Policy · 💻 Tech
          </p>
        </div>
    """

    for section, section_items in grouped.items():
        label, accent = SECTION_STYLES.get(section, ("📰 Other News", "#4b3a2f"))

        html_content += f"""
        <div style="background:#fff8e7; border-radius:20px; padding:24px; margin-top:22px; border:2px solid #d8c3a5;">
          <h2 style="font-size:22px; margin:0 0 16px 0; color:{accent}; border-bottom:2px solid {accent}; padding-bottom:8px;">
            {label}
          </h2>
        """

        for i, item in enumerate(section_items[:5], start=1):
            title = html.escape(item.get("title", "Untitled"))
            source = html.escape(item.get("source", "Unknown source"))
            link = item.get("link", "#")
            summary = html.escape(short_summary(item.get("summary", "")))

            html_content += f"""
            <div style="padding:18px; border-left:6px solid {accent}; border-radius:14px; margin-bottom:14px; background:#ffffff; border:1px solid #d8c3a5;">
              <p style="font-size:12px; color:#8b7355; margin:0 0 8px 0; text-transform:uppercase;">
                {source}
              </p>

              <h3 style="font-size:18px; line-height:1.38; margin:0 0 8px 0; color:#2d241c;">
                {i}. {title}
              </h3>

              <p style="font-size:14px; line-height:1.6; color:#4b3a2f; margin:0 0 12px 0;">
                {summary}
              </p>

              <a href="{link}" style="display:inline-block; background:{accent}; color:white; padding:8px 13px; border-radius:10px; font-size:13px; text-decoration:none; font-weight:bold;">
                Read more →
              </a>
            </div>
            """

        html_content += "</div>"

    html_content += """
        <div style="margin-top:24px; padding:24px; background:#ead7bd; border-radius:18px; border:1px solid #d8c3a5;">
          <h2 style="font-size:21px; margin:0 0 12px 0; color:#5c4033;">
            💡 Possible Research Angles
          </h2>
          <ul style="padding-left:20px; margin:0; color:#4b3a2f; font-size:15px; line-height:1.7;">
            <li>🌐 How decentralized social media shifts governance from platform authority to protocol/community authority.</li>
            <li>🤖 How agentic AI interfaces transform users from operators into supervisors and delegators.</li>
            <li>🧠 How AI-curated feeds become personal epistemic infrastructures.</li>
          </ul>
        </div>

      </div>
    </body>
    </html>
    """

    return html_content


def build_email_overview(items, full_digest_url="#"):
    """
    Build a short email overview with a button linking to the full digest
    hosted on GitHub Pages.
    """
    from datetime import datetime
    from collections import defaultdict

    today = datetime.now().strftime("%d %B %Y")
    grouped = defaultdict(list)

    for item in items:
        grouped[classify_section(item)].append(item)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background:#3b2a20; font-family:Arial, Helvetica, sans-serif;">
      <div style="max-width:680px; margin:0 auto; padding:28px 18px;">

        <div style="
            background:#4b2e22;
            color:#ffffff;
            padding:26px;
            border-radius:18px;
        ">
          <h1 style="margin:0 0 8px 0; font-size:28px;">
            ☕ Daily Intelligence Digest
          </h1>
          <p style="margin:0; font-size:14px;">
            {today}
          </p>
        </div>

        <div style="
            background:#fff8e7;
            padding:24px;
            border-radius:18px;
            margin-top:18px;
            color:#2d241c;
        ">
          <h2 style="margin:0 0 14px 0;">
            📌 Today's Overview
          </h2>

          <p style="font-size:15px; line-height:1.6;">
            Here is your daily briefing. Click below to open the full visual digest in your browser.
          </p>

          <p style="margin:22px 0;">
            <a href="{full_digest_url}" style="
                display:inline-block;
                background:#5c4033;
                color:#ffffff;
                padding:12px 18px;
                border-radius:12px;
                text-decoration:none;
                font-weight:bold;
                font-size:15px;
            ">
              📖 Read Full Digest →
            </a>
          </p>
    """

    # Add up to 3 headlines per section
    for section, section_items in grouped.items():
        label, accent = SECTION_STYLES.get(section, ("📰 Other News", "#4b3a2f"))

        html_content += f"""
          <h3 style="color:{accent}; margin:22px 0 8px 0;">
            {label}
          </h3>
          <ul style="margin-top:0; padding-left:20px; line-height:1.55;">
        """

        for item in section_items[:3]:
            title = html.escape(item.get("title", "Untitled"))
            link = item.get("link", "#")

            html_content += f"""
            <li>
              <a href="{link}" style="color:{accent}; font-weight:bold; text-decoration:none;">
                {title}
              </a>
            </li>
            """

        html_content += "</ul>"

    # Research idea box + footer
    html_content += """
          <div style="
              margin-top:24px;
              padding:16px;
              background:#ead7bd;
              border-radius:14px;
          ">
            <strong>💡 Research Idea:</strong>
            Observe how agentic interfaces and decentralized platforms shift authority from institutions to protocols, AI agents, and users.
          </div>

          <p style="
              font-size:12px;
              color:#7c6a55;
              margin-top:22px;
          ">
            Open the full digest for detailed summaries and all links.
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    return html_content

def send_email(subject, html_content, attachment_path=None):
    load_dotenv()

    sender = os.getenv("SENDER_EMAIL")
    password = os.getenv("SENDER_APP_PASSWORD")
    receiver = os.getenv("RECEIVER_EMAIL")

    if not sender or not password or not receiver:
        raise ValueError("Missing SENDER_EMAIL, SENDER_APP_PASSWORD, or RECEIVER_EMAIL in .env")

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = receiver

    # Email body
    msg.attach(MIMEText(html_content, "html"))

    # Optional attachment
    if attachment_path:
        from email.mime.application import MIMEApplication

        with open(attachment_path, "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype="html")
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename="daily_digest.html"
            )
            msg.attach(attachment)

    # Send email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)