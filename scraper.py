import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import requests

RECIPIENT_EMAIL = "cmausman14@gmail.com"


def fetch_live_proxy_data(api_key):
  print("📡 Pulling live MLO records via ScraperAPI residential proxy...")
  all_leads = []

  # 1. CALIFORNIA DFPI
  ca_target = "https://data.dfpi.ca.gov/resource/mlo-licenses.json?$limit=200&$where=license_status='Approved'"
  ca_proxy_url = f"http://api.scraperapi.com?api_key={api_key}&url={ca_target}"

  try:
    res = requests.get(ca_proxy_url, timeout=45)
    print(f"  [CA Proxy Status] HTTP {res.status_code}")
    if res.status_code == 200 and res.json():
      for row in res.json():
        nmls = str(
            row.get("nmls_id", row.get("license_number", ""))
        ).strip()
        name = str(
            row.get("individual_name", row.get("name", ""))
        ).strip()
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
      print(f"  [+] Ingested {len(all_leads)} live CA records.")
  except Exception as e:
    print(f"  [-] CA Proxy Error: {e}")

  # 2. ARIZONA DIFI
  az_target = "https://data.az.gov/resource/difi-mortgage-mlo.json?$limit=200"
  az_proxy_url = f"http://api.scraperapi.com?api_key={api_key}&url={az_target}"

  try:
    res = requests.get(az_proxy_url, timeout=45)
    print(f"  [AZ Proxy Status] HTTP {res.status_code}")
    if res.status_code == 200 and res.json():
      az_count = 0
      for row in res.json():
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
      print(f"  [+] Ingested {az_count} live AZ records.")
  except Exception as e:
    print(f"  [-] AZ Proxy Error: {e}")

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
    print("⚠️ Proxy returned no rows. Maintaining clean frame.")
    df = pd.DataFrame(columns=cols)

  for c in cols:
    if c not in df.columns:
      df[c] = "N/A"

  df.to_csv("master_leads.csv", index=False)
  print(f"✅ Saved {len(df)} verified records to master_leads.csv")
  return df


def send_email_alert(sender_email, sender_pass, df):
  if df.empty:
    print("No records to email.")
    return

  try:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"🎯 Multi-State NMLS Pipeline Alert: {len(df)} Verified MLO Leads"
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
            <h2 style="color: #0056b3;">🚨 Live Multi-State NMLS Ingestion Complete</h2>
            <p>Hey Christine! Your pipeline scraper pulled live, verified MLO records via proxy integration.</p>
            <p><b>Total Active MLO Records Processed:</b> {len(df)}</p>
            <hr>
            <h3>🔥 Sample Live MLO Records:</h3>
            {table_html}
            <br>
            <p>👉 Open your <b>Champions AE Suite App</b> to interact with all leads!</p>
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
  api_key = os.getenv("SCRAPER_API_KEY")
  email_user = os.getenv("EMAIL_USER")
  email_pass = os.getenv("EMAIL_PASS")

  if api_key:
    leads_df = fetch_live_proxy_data(api_key)
    if email_user and email_pass and not leads_df.empty:
      send_email_alert(email_user, email_pass, leads_df)
  else:
    print("❌ Missing SCRAPER_API_KEY environment variable.")
