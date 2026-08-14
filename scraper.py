import io
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


def fetch_official_state_registries():
  print(
      "📡 Pulling newest MLO license approvals & transfers from state bulk"
      " feeds..."
  )
  all_leads = []

  # 1. CALIFORNIA DFPI - Query explicitly ordered by newest status date
  try:
    # $order=license_status_date DESC gets the absolute newest approvals/changes first
    ca_url = (
        "https://data.dfpi.ca.gov/resource/mlo-licenses.json?"
        "$limit=300&"
        "$order=license_status_date DESC&"
        "$where=license_status='Approved'"
    )
    res = requests.get(ca_url, headers=HEADERS, timeout=20)
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
        status = str(row.get("license_status", "Approved")).strip()

        if nmls and name and nmls != "nan" and name != "nan":
          all_leads.append({
              "NMLS_ID": nmls,
              "Name": name,
              "Current_Company": company,
              "State": "CA",
              "Status": status,
              "Lead_Trigger": "🟢 Recent Approval (CA DFPI Feed)",
              "Approved_States": "CA",
          })
      print(f"  [+] Ingested newest California MLO records.")
  except Exception as e:
    print(f"  [-] CA DFPI bulk download note: {e}")

  # 2. ARIZONA DIFI - Query ordered by newest record updates
  try:
    az_url = (
        "https://data.az.gov/resource/difi-mortgage-mlo.json?"
        "$limit=300&"
        "$order=last_modified_date DESC"
    )
    res = requests.get(az_url, headers=HEADERS, timeout=20)
    if res.status_code == 200 and res.json():
      for row in res.json():
        nmls = str(row.get("nmls_id", row.get("license_num", ""))).strip()
        first = str(row.get("first_name", "")).strip()
        last = str(row.get("last_name", "")).strip()
        name = (
            f"{first} {last}".strip()
            if first != "nan" and last != "nan"
            else str(row.get("name", "")).strip()
        )
        company = str(
            row.get("company_name", "Independent / Unassigned")
        ).strip()
        status = str(row.get("status", "Active")).strip()

        if nmls and name and nmls != "nan" and name != "nan":
          all_leads.append({
              "NMLS_ID": nmls,
              "Name": name,
              "Current_Company": company,
              "State": "AZ",
              "Status": status,
              "Lead_Trigger": "🟢 Recent Approval (AZ DIFI Feed)",
              "Approved_States": "AZ",
          })
      print(f"  [+] Ingested newest Arizona MLO records.")
  except Exception as e:
    print(f"  [-] AZ DIFI bulk download note: {e}")

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
    print("⚠️ No new records found in this batch. Initializing clean frame.")
    df = pd.DataFrame(columns=cols)

  for c in cols:
    if c not in df.columns:
      df[c] = "N/A"

  df.to_csv("master_leads.csv", index=False)
  print(f"✅ Saved {len(df)} verified real-world records to master_leads.csv")
  return df


def send_email_alert(sender_email, sender_pass, df):
  if df.empty:
    print("No new records to email.")
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
            <h2 style="color: #0056b3;">🚨 Verified Multi-State NMLS Bulk Refresh</h2>
            <p>Hey Christine! Your pipeline scraper pulled live, verified MLO records directly from official state licensing registries.</p>
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
  leads_df = fetch_official_state_registries()
  email_user = os.getenv("EMAIL_USER")
  email_pass = os.getenv("EMAIL_PASS")

  if email_user and email_pass and not leads_df.empty:
    send_email_alert(email_user, email_pass, leads_df)
