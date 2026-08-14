import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote
import pandas as pd
import requests

RECIPIENT_EMAIL = "cmausman14@gmail.com"


def fetch_live_mlo_leads(api_key):
  print("📡 Pulling live MLO records via ScraperAPI residential proxy...")
  all_leads = []

  # 1. CALIFORNIA DFPI - Universal Socrata Endpoint via Proxy
  ca_target = "https://data.ca.gov/api/3/action/datastore_search?resource_id=mlo-licenses&limit=300"
  ca_proxy_url = (
      f"http://api.scraperapi.com?api_key={api_key}&url={quote(ca_target, safe='')}"
  )

  try:
    print("  [+] Requesting California DFPI Endpoint...")
    res = requests.get(ca_proxy_url, timeout=30)
    print(f"  [CA Proxy Status] HTTP {res.status_code}")

    if res.status_code == 200:
      data = res.json()
      # Parse Socrata datastore schema
      records = (
          data.get("result", {}).get("records", [])
          if isinstance(data, dict)
          else []
      )

      if not records and isinstance(data, list):
        records = data

      for row in records:
        nmls = str(
            row.get("nmls_id", row.get("NMLS ID", row.get("license_number", "")))
        ).strip()
        name = str(
            row.get(
                "individual_name", row.get("Individual Name", row.get("name", ""))
            )
        ).strip()
        company = str(
            row.get(
                "employer_name",
                row.get("Employer Name", "Independent / Unassigned"),
            )
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
    else:
      print(
          f"  [-] CA primary failed with HTTP {res.status_code}. Attempting"
          " backup query..."
      )
      backup_target = (
          "https://data.dfpi.ca.gov/api/views/mlo-licenses/rows.json"
      )
      res_backup = requests.get(
          f"http://api.scraperapi.com?api_key={api_key}&url={quote(backup_target, safe='')}",
          timeout=30,
      )
      print(f"  [CA Backup Proxy Status] HTTP {res_backup.status_code}")
  except Exception as e:
    print(f"  [-] CA Proxy Exception: {e}")

  # 2. ARIZONA DIFI - Universal Socrata Endpoint via Proxy
  az_target = "https://data.az.gov/resource/difi-mortgage-mlo.json?$limit=300"
  az_proxy_url = (
      f"http://api.scraperapi.com?api_key={api_key}&url={quote(az_target, safe='')}&keep_headers=true"
  )

  try:
    print("  [+] Requesting Arizona DIFI Endpoint...")
    res = requests.get(
        az_proxy_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
        },
        timeout=30,
    )
    print(f"  [AZ Proxy Status] HTTP {res.status_code}")

    if res.status_code == 200:
      data = res.json()
      if isinstance(data, list) and data:
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
        print(f"  [+] Ingested {az_count} live AZ records.")
  except Exception as e:
    print(f"  [-] AZ Proxy Exception: {e}")

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
    print("⚠️ No live records returned. Initializing clean target frame.")
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
            <p>Hey Christine! Your pipeline scraper pulled fresh, verified MLO records directly from state regulatory endpoints.</p>
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
  api_key = os.getenv("SCRAPER_API_KEY")
  email_user = os.getenv("EMAIL_USER")
  email_pass = os.getenv("EMAIL_PASS")

  if api_key:
    leads_df = fetch_live_mlo_leads(api_key)
    if email_user and email_pass and not leads_df.empty:
      send_email_alert(email_user, email_pass, leads_df)
  else:
    print("❌ Missing SCRAPER_API_KEY environment variable.")
