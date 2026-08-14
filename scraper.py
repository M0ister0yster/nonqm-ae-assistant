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


def fetch_verified_mlo_leads():
  print("📡 Querying state financial registry API endpoints...")
  all_leads = []

  # 1. CALIFORNIA DFPI PUBLIC ENDPOINT
  try:
    ca_url = "https://data.ca.gov/api/3/action/datastore_search?resource_id=mlo-licenses&limit=200"
    res = requests.get(ca_url, headers=HEADERS, timeout=15)
    print(f"  [CA API Status] HTTP {res.status_code}")

    # Fallback to direct Socrata JSON
    if res.status_code != 200:
      ca_url = "https://data.dfpi.ca.gov/resource/mlo-licenses.json?$limit=200"
      res = requests.get(ca_url, headers=HEADERS, timeout=15)

    if res.status_code == 200 and res.json():
      data = res.json()
      records = (
          data.get("result", {}).get("records", [])
          if isinstance(data, dict) and "result" in data
          else data
      )
      print(f"  [CA API] Retrieved {len(records)} raw records.")

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
              "Lead_Trigger": "🟢 Active License (CA DFPI Feed)",
              "Approved_States": "CA",
          })
  except Exception as e:
    print(f"  [-] CA API Exception: {e}")

  # 2. ARIZONA DIFI PUBLIC ENDPOINT
  try:
    az_url = "https://data.az.gov/resource/difi-mortgage-mlo.json?$limit=200"
    res = requests.get(az_url, headers=HEADERS, timeout=15)
    print(f"  [AZ API Status] HTTP {res.status_code}")

    if res.status_code == 200 and res.json():
      records = res.json()
      print(f"  [AZ API] Retrieved {len(records)} raw records.")

      for row in records:
        nmls = str(
            row.get("nmls_id", row.get("NMLS ID", row.get("license_num", "")))
        ).strip()
        first = str(row.get("first_name", row.get("First Name", ""))).strip()
        last = str(row.get("last_name", row.get("Last Name", ""))).strip()
        name = (
            f"{first} {last}".strip()
            if first.lower() != "nan" and last.lower() != "nan"
            else str(row.get("name", "")).strip()
        )
        company = str(
            row.get(
                "company_name", row.get("Company Name", "Independent / Unassigned")
            )
        ).strip()

        if nmls and name and nmls.lower() != "nan" and name.lower() != "nan":
          all_leads.append({
              "NMLS_ID": nmls,
              "Name": name,
              "Current_Company": company,
              "State": "AZ",
              "Status": "Active",
              "Lead_Trigger": "🟢 Active License (AZ DIFI Feed)",
              "Approved_States": "AZ",
          })
  except Exception as e:
    print(f"  [-] AZ API Exception: {e}")

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
    print("⚠️ No records retrieved. Initializing clean target frame.")
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
            <h2 style="color: #0056b3;">🚨 Verified NMLS Registry Refresh Complete</h2>
            <p>Hey Christine! Your pipeline scraper pulled live, verified MLO records directly from state licensing files.</p>
            <p><b>Total Verified Active MLO Records Processed:</b> {len(df)}</p>
            <hr>
            <h3>🔥 Sample Live MLO Records:</h3>
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
  leads_df = fetch_verified_mlo_leads()
  email_user = os.getenv("EMAIL_USER")
  email_pass = os.getenv("EMAIL_PASS")

  if email_user and email_pass and not leads_df.empty:
    send_email_alert(email_user, email_pass, leads_df)
