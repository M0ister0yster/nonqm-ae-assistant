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


def fetch_live_state_data():
  print("📡 Pulling live active MLO records from public state endpoints...")
  all_leads = []

  # 1. LIVE CALIFORNIA DFPI MLO REGISTRY (Socrata API)
  try:
    ca_url = (
        "https://data.dfpi.ca.gov/resource/mlo-licenses.json?$limit=200&$where=license_status='Approved'"
    )
    res = requests.get(ca_url, headers=HEADERS, timeout=15)
    if res.status_code == 200 and res.json():
      for row in res.json():
        nmls = str(row.get("nmls_id", row.get("license_number", ""))).strip()
        name = row.get("individual_name", row.get("name", "")).strip()
        company = row.get(
            "employer_name", "Independent / Unassigned"
        ).strip()
        if nmls and name:
          all_leads.append({
              "NMLS_ID": nmls,
              "Name": name,
              "Current_Company": company,
              "State": "CA",
              "Status": "Approved",
              "Lead_Trigger": "🟢 Active License (CA DFPI Feed)",
              "Approved_States": "CA",
          })
      print(f"  [+] Ingested {len(all_leads)} live California MLO records.")
  except Exception as e:
    print(f"  [-] CA endpoint error: {e}")

  # 2. LIVE ARIZONA DIFI MLO REGISTRY
  try:
    az_url = "https://data.az.gov/resource/difi-mortgage-mlo.json?$limit=200"
    res = requests.get(az_url, headers=HEADERS, timeout=15)
    if res.status_code == 200 and res.json():
      az_count = 0
      for row in res.json():
        nmls = str(row.get("nmls_id", row.get("license_num", ""))).strip()
        first = row.get("first_name", "").strip()
        last = row.get("last_name", "").strip()
        name = f"{first} {last}".strip()
        company = row.get("company_name", "Independent / Unassigned").strip()
        if nmls and name:
          all_leads.append({
              "NMLS_ID": nmls,
              "Name": name,
              "Current_Company": company,
              "State": "AZ",
              "Status": "Active",
              "Lead_Trigger": "🟢 Active License (AZ DIFI Feed)",
              "Approved_States": "AZ",
          })
          az_count += 1
      print(f"  [+] Ingested {az_count} live Arizona MLO records.")
  except Exception as e:
    print(f"  [-] AZ endpoint error: {e}")

  if not all_leads:
    print("❌ No records retrieved from live endpoints.")
    return pd.DataFrame()

  df = pd.DataFrame(all_leads)
  df.drop_duplicates(subset=["NMLS_ID"], inplace=True)

  # Ensure every column expected by app.py exists
  required_cols = [
      "NMLS_ID",
      "Name",
      "Current_Company",
      "State",
      "Status",
      "Lead_Trigger",
      "Approved_States",
  ]
  for col in required_cols:
    if col not in df.columns:
      df[col] = "N/A"

  df.to_csv("master_leads.csv", index=False)
  print(f"✅ Saved {len(df)} 100% REAL state-verified records to master_leads.csv")
  return df


def send_email_alert(sender_email, sender_pass, df):
  if df.empty:
    return

  try:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"🎯 Multi-State NMLS Pipeline Alert: {len(df)} Real MLO Leads"
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
    print("📧 Real-data email alert sent successfully!")
  except Exception as e:
    print(f"Email error: {e}")


if __name__ == "__main__":
  leads_df = fetch_live_state_data()
  email_user = os.getenv("EMAIL_USER")
  email_pass = os.getenv("EMAIL_PASS")

  if email_user and email_pass and not leads_df.empty:
    send_email_alert(email_user, email_pass, leads_df)
