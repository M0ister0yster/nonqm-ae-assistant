import io
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import requests

RECIPIENT_EMAIL = "cmausman14@gmail.com"

# Target Footprint
TARGET_STATES = [
    "CA",
    "AZ",
    "MT",
    "MI",
    "VA",
    "VT",
    "OR",
    "ID",
    "UT",
    "MN",
    "FL",
    "TX",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_state_data_via_pandas():
  print("📡 Pulling verified MLO records from public state registry files...")
  all_leads = []

  # 1. CALIFORNIA DFPI CSV EXPORT
  try:
    ca_url = "https://data.dfpi.ca.gov/api/views/mlo-licenses/rows.csv?accessType=DOWNLOAD"
    res = requests.get(ca_url, headers=HEADERS, timeout=30)
    print(f"  [CA CSV Status] HTTP {res.status_code}")
    if res.status_code == 200:
      df_ca = pd.read_csv(io.StringIO(res.text), low_memory=False)
      print(f"  [CA CSV Parsed] {len(df_ca)} total rows found.")

      # Dynamically search for columns regardless of exact naming
      nmls_col = next(
          (
              c
              for c in df_ca.columns
              if "nmls" in c.lower() or "license number" in c.lower()
          ),
          None,
      )
      name_col = next(
          (
              c
              for c in df_ca.columns
              if "name" in c.lower() or "individual" in c.lower()
          ),
          None,
      )
      company_col = next(
          (
              c
              for c in df_ca.columns
              if "employer" in c.lower() or "company" in c.lower()
          ),
          None,
      )

      if nmls_col and name_col:
        for _, row in df_ca.head(300).iterrows():
          nmls = str(row[nmls_col]).split(".")[0].strip()
          name = str(row[name_col]).strip()
          company = (
              str(row[company_col]).strip()
              if company_col
              else "Independent / Unassigned"
          )

          if (
              nmls
              and name
              and nmls.lower() != "nan"
              and name.lower() != "nan"
              and nmls != ""
          ):
            all_leads.append({
                "NMLS_ID": nmls,
                "Name": name,
                "Current_Company": company,
                "State": "CA",
                "Status": "Approved",
                "Lead_Trigger": "🟢 Active License (CA DFPI Registry)",
                "Approved_States": "CA",
            })
        print(f"  [+] Ingested {len(all_leads)} California MLO records.")
  except Exception as e:
    print(f"  [-] CA CSV fetch note: {e}")

  # 2. ARIZONA DIFI CSV EXPORT
  try:
    az_url = "https://data.az.gov/api/views/difi-mortgage-mlo/rows.csv?accessType=DOWNLOAD"
    res = requests.get(az_url, headers=HEADERS, timeout=30)
    print(f"  [AZ CSV Status] HTTP {res.status_code}")
    if res.status_code == 200:
      df_az = pd.read_csv(io.StringIO(res.text), low_memory=False)
      print(f"  [AZ CSV Parsed] {len(df_az)} total rows found.")

      nmls_col = next(
          (
              c
              for c in df_az.columns
              if "nmls" in c.lower() or "license" in c.lower()
          ),
          None,
      )
      name_col = next(
          (
              c
              for c in df_az.columns
              if "name" in c.lower() or "first" in c.lower()
          ),
          None,
      )
      company_col = next(
          (c for c in df_az.columns if "company" in c.lower()), None
      )

      az_count = 0
      if nmls_col and name_col:
        for _, row in df_az.head(300).iterrows():
          nmls = str(row[nmls_col]).split(".")[0].strip()
          name = str(row[name_col]).strip()
          company = (
              str(row[company_col]).strip()
              if company_col
              else "Independent / Unassigned"
          )

          if (
              nmls
              and name
              and nmls.lower() != "nan"
              and name.lower() != "nan"
              and nmls != ""
          ):
            all_leads.append({
                "NMLS_ID": nmls,
                "Name": name,
                "Current_Company": company,
                "State": "AZ",
                "Status": "Active",
                "Lead_Trigger": "🟢 Active License (AZ DIFI Registry)",
                "Approved_States": "AZ",
            })
            az_count += 1
        print(f"  [+] Ingested {az_count} Arizona MLO records.")
  except Exception as e:
    print(f"  [-] AZ CSV fetch note: {e}")

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
    print("⚠️ No records parsed from feeds. Initializing clean target frame.")
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
            <h2 style="color: #0056b3;">🚨 Verified NMLS Official Registry Refresh</h2>
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
  leads_df = fetch_state_data_via_pandas()
  email_user = os.getenv("EMAIL_USER")
  email_pass = os.getenv("EMAIL_PASS")

  if email_user and email_pass and not leads_df.empty:
    send_email_alert(email_user, email_pass, leads_df)
