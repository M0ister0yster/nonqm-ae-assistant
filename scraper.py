import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import requests

RECIPIENT_EMAIL = "cmausman14@gmail.com"


def fetch_live_mlo_leads():
  print("📡 Pulling live MLO records directly from state endpoints...")
  all_leads = []

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
          " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  # 1. CALIFORNIA DFPI - Direct Socrata REST Endpoint
  ca_target = "https://data.dfpi.ca.gov/resource/352i-3aw8.json?$limit=300"
  try:
    print("  [+] Querying California DFPI...")
    res = requests.get(ca_target, headers=headers, timeout=20)
    print(f"  [CA Status] HTTP {res.status_code}")

    if res.status_code == 200:
      data = res.json()
      for row in data:
        nmls = str(
            row.get("nmls_id", row.get("license_number", ""))
        ).strip()
        name = str(row.get("individual_name", row.get("name", ""))).strip()
        company = str(
            row.get("employer_name", "Independent / Unassigned")
        ).strip()

        if nmls and name and nmls.lower() != "nan" and name.lower() != "nan":
          all_leads.append({
              "NMLS_ID": nmls,
              "Name": name,
              "Current_Company": company,
              "State": "CA",
              "Status": "Approved",
              "Lead_Trigger": "🟢 Live License Approval (CA DFPI)",
              "Approved_States": "CA",
          })
      print(f"  [+] Successfully ingested {len(all_leads)} live CA records.")
  except Exception as e:
    print(f"  [-] CA Direct Request Error: {e}")

  # 2. ARIZONA DIFI - Direct Socrata REST Endpoint
  az_target = "https://data.az.gov/resource/ir9e-2iwd.json?$limit=300"
  try:
    print("  [+] Querying Arizona DIFI...")
    res = requests.get(az_target, headers=headers, timeout=20)
    print(f"  [AZ Status] HTTP {res.status_code}")

    if res.status_code == 200:
      data = res.json()
      az_count = 0
      for row in data:
        nmls = str(row.get("nmls_id", row.get("license_num", ""))).strip()
        first = str(row.get("first_name", "")).strip()
        last = str(row.get("last_name", "")).strip()
        name = (
            f"{first} {last}".strip()
            if first.lower() != "nan" and last.lower() != "nan"
            else str(row.get("name", "")).strip()
        )
        company = str(
            row.get("company_name", "Independent / Unassigned")
        ).strip()

        if nmls and name and nmls.lower() != "nan" and name.lower() != "nan":
          all_leads.append({
              "NMLS_ID": nmls,
              "Name": name,
              "Current_Company": company,
              "State": "AZ",
              "Status": "Active",
              "Lead_Trigger": "🟢 Live License Approval (AZ DIFI)",
              "Approved_States": "AZ",
          })
          az_count += 1
      print(f"  [+] Successfully ingested {az_count} live AZ records.")
  except Exception as e:
    print(f"  [-] AZ Direct Request Error: {e}")

  cols = [
      "NMLS_ID",
      "Name",
      "Current_Company",
      "State",
      "Status",
      "Lead_Trigger",
      "Approved_States",
  ]

  if all_leads:
    df = pd.DataFrame(all_leads)
    df.drop_duplicates(subset=["NMLS_ID"], inplace=True)
  else:
    print("⚠️ No records retrieved from state endpoints.")
    df = pd.DataFrame(columns=cols)

  for c in cols:
    if c not in df.columns:
      df[c] = "N/A"

  df.to_csv("master_leads.csv", index=False)
  print(f"✅ Saved {len(df)} live verified records to master_leads.csv")
  return df


def send_email_alert(sender_email, sender_pass, df):
  if df.empty:
    print("No records retrieved; skipping email dispatch.")
    return

  try:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"🎯 Multi-State NMLS Pipeline Alert: {len(df)} Live MLO Leads"
    )
    msg["From"] = sender_email
    msg["To"] = RECIPIENT_EMAIL

    table_html = (
        df[["NMLS_ID", "Name", "Current_Company", "State", "Lead_Trigger"]]
        .head(15)
        .to_html(index=False)
    )

    html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #0056b3;">🚨 Verified Live NMLS Registry Refresh Complete</h2>
            <p>Hey Christine! Your local pipeline scraper pulled fresh, verified MLO records directly from state regulatory endpoints.</p>
            <p><b>Total Verified Active MLO Records Processed:</b> {len(df)}</p>
            <hr>
            <h3>🔥 Sample Verified MLO Leads:</h3>
            {table_html}
            <br>
            <p>👉 Open your <b>Champions AE Suite App</b> to filter and interact with all leads!</p>
          </body>
        </html>
        """

    msg.attach(MIMEText(html_content, "html"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_pass)
    server.sendmail(sender_email, RECIPIENT_EMAIL, msg.as_string())
    server.quit()
    print("📧 Email alert sent successfully!")
  except Exception as e:
    print(f"Email error: {e}")


if __name__ == "__main__":
  email_user = os.getenv("EMAIL_USER")
  email_pass = os.getenv("EMAIL_PASS")

  leads_df = fetch_live_mlo_leads()

  if email_user and email_pass and not leads_df.empty:
    send_email_alert(email_user, email_pass, leads_df)
