import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import requests

RECIPIENT_EMAIL = "cmausman14@gmail.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_live_mlo_data():
  """Fetches live active MLO data directly from active state regulatory registries."""
  print("📡 Connecting to live state financial registries...")
  leads = []

  # 1. CALIFORNIA DFPI LIVE MLO REGISTRY
  ca_url = "https://data.dfpi.ca.gov/resource/mlo-licenses.json?$limit=100"
  try:
    res = requests.get(ca_url, headers=HEADERS, timeout=12)
    if res.status_code == 200 and len(res.json()) > 0:
      for row in res.json():
        nmls = str(row.get("nmls_id", row.get("license_number", "")))
        name = row.get("individual_name", row.get("name", ""))
        company = row.get("employer_name", "Independent / Unassigned")
        if nmls and name:
          leads.append({
              "NMLS_ID": nmls,
              "Name": name,
              "Current_Company": company,
              "State": "CA",
              "Status": "Active",
              "Lead_Trigger": "🟢 Active License (CA DFPI Registry)",
          })
      print(f"  [+] Extracted {len(leads)} live California MLO records.")
  except Exception as e:
    print(f"  [-] CA endpoint warning: {e}")

  # 2. ARIZONA DIFI LIVE MLO REGISTRY
  az_url = "https://data.az.gov/resource/difi-mortgage-mlo.json?$limit=100"
  try:
    res = requests.get(az_url, headers=HEADERS, timeout=12)
    if res.status_code == 200 and len(res.json()) > 0:
      az_count = 0
      for row in res.json():
        nmls = str(row.get("nmls_id", row.get("license_num", "")))
        first = row.get("first_name", "")
        last = row.get("last_name", "")
        name = f"{first} {last}".strip()
        company = row.get("company_name", "Independent / Unassigned")
        if nmls and name:
          leads.append({
              "NMLS_ID": nmls,
              "Name": name,
              "Current_Company": company,
              "State": "AZ",
              "Status": "Active",
              "Lead_Trigger": "🟢 Active License (AZ DIFI Registry)",
          })
          az_count += 1
      print(f"  [+] Extracted {az_count} live Arizona MLO records.")
  except Exception as e:
    print(f"  [-] AZ endpoint warning: {e}")

  if leads:
    df = pd.DataFrame(leads)
    df.drop_duplicates(subset=["NMLS_ID"], inplace=True)
    # Force overwrite master_leads.csv with live records
    df.to_csv("master_leads.csv", index=False)
    print(f"✅ Successfully wrote {len(df)} REAL records to master_leads.csv")
    return df
  else:
    print("⚠️ Could not fetch live records from APIs.")
    return pd.DataFrame()


def send_email_alert(sender_email, sender_pass, df):
  if df.empty:
    return

  try:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"🎯 Real-Time NMLS Pipeline Alert: {len(df)} Live MLO Leads"
    )
    msg["From"] = sender_email
    msg["To"] = RECIPIENT_EMAIL

    table_html = (
        df[["NMLS_ID", "Name", "Current_Company", "State", "Lead_Trigger"]]
        .head(10)
        .to_html(index=False)
    )

    html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #0056b3;">🚨 Live NMLS Real-Data Refresh Complete</h2>
            <p>Hey Christine! Your pipeline scraper pulled live, verified MLO data directly from active state regulatory registries.</p>
            <p><b>Total Real Active MLO Records Processed:</b> {len(df)}</p>
            <hr>
            <h3>🔥 Sample Live MLO Records (Real NMLS IDs):</h3>
            {table_html}
            <br>
            <p>👉 Open your <b>Champions AE Suite App</b> to interact with all real records!</p>
          </body>
        </html>
        """

    msg.attach(MIMEText(html_content, "html"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_pass)
    server.sendmail(sender_email, RECIPIENT_EMAIL, msg.as_string())
    server.quit()
    print("📧 Live email dispatched successfully!")
  except Exception as e:
    print(f"Failed to send email: {e}")


if __name__ == "__main__":
  leads_df = fetch_live_mlo_data()
  email_user = os.getenv("EMAIL_USER")
  email_pass = os.getenv("EMAIL_PASS")

  if email_user and email_pass and not leads_df.empty:
    send_email_alert(email_user, email_pass, leads_df)
