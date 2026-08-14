import os
import re
from datetime import datetime, timedelta
import pandas as pd
import requests

PINK_PIN_STATES = ["CA", "AZ", "MT", "MI", "VA", "VT"]
BLUE_PIN_STATES = ["OR", "ID", "UT", "MN"]
ALLY_STATES = [
    "AZ",
    "CA",
    "CT",
    "DE",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "MI",
    "MN",
    "MT",
    "NJ",
    "NC",
    "OK",
    "OR",
    "RI",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
]

MAJOR_INSTITUTIONS = [
    "wells fargo",
    "citibank",
    "chase",
    "bank of america",
    "pnc",
    "us bank",
    "truist",
    "rocket mortgage",
    "loandepot",
    "guaranteed rate",
    "fairway independent",
    "crosscountry mortgage",
    "guild mortgage",
    "movement mortgage",
    "caliber home loans",
]


def classify_lead_trigger(row):
    triggers = []

    if row.get("Is_Newly_Licensed", False):
        triggers.append("🆕 Brand New Licensee (High AE Need)")

    prior_comp = str(row.get("Prior_Company", "")).strip().lower()
    curr_comp = str(row.get("Current_Company", "")).strip().lower()

    if prior_comp and prior_comp != "none" and prior_comp != curr_comp:
        if any(inst in prior_comp for inst in MAJOR_INSTITUTIONS):
            triggers.append(
                f"🏦 Ex-Institutional LO (Moved from {row.get('Prior_Company')})"
            )
        else:
            triggers.append(
                f"🔄 Sponsorship Transfer (Joined {row.get('Current_Company')})"
            )

    if row.get("Has_New_State_Added", False):
        triggers.append("🗺️ Expanded into New State(s)")

    return " | ".join(triggers) if triggers else "⭐ Active Industry MLO"


def evaluate_licensing(states_list):
    flags = []
    valid_states = []

    for state in states_list:
        s = state.strip().upper()
        if s in ["ND", "SD"]:
            continue
        valid_states.append(s)

        if s in PINK_PIN_STATES:
            flags.append(f"{s}: Broker Lic Req")
        elif s in BLUE_PIN_STATES:
            flags.append(f"{s}: Dual Lic Req (Broker+LO)")
        elif s in ["NY", "NJ"]:
            flags.append(f"{s}: Attestation Form Req")

    return ", ".join(valid_states), "; ".join(flags)


def fetch_and_process_nmls_leads():
    print("Starting automated multi-trigger NMLS lead scraper...")

    raw_data = [
        {
            "NMLS_ID": "1982341",
            "Name": "Sarah Jenkins",
            "Current_Company": "Apex Mortgage Solutions",
            "Prior_Company": "Wells Fargo Bank",
            "Initial_License_Date": "2021-03-15",
            "Company_Start_Date": "2026-08-01",
            "States": "AZ, CA, TX",
            "Is_Newly_Licensed": False,
            "Has_New_State_Added": True,
            "Phone": "602-555-0144",
            "Email": "sjenkins@apexmortgage.com",
        },
        {
            "NMLS_ID": "2491022",
            "Name": "Marcus Vance",
            "Current_Company": "Sunbelt Wholesale Brokers",
            "Prior_Company": "None (New Exam Pass)",
            "Initial_License_Date": "2026-07-20",
            "Company_Start_Date": "2026-07-22",
            "States": "FL, GA, TN",
            "Is_Newly_Licensed": True,
            "Has_New_State_Added": False,
            "Phone": "407-555-0188",
            "Email": "mvance@sunbeltbrokers.com",
        },
        {
            "NMLS_ID": "1420911",
            "Name": "David Miller",
            "Current_Company": "Desert Horizon Lending",
            "Prior_Company": "Guaranteed Rate",
            "Initial_License_Date": "2018-01-10",
            "Company_Start_Date": "2026-08-05",
            "States": "CA, UT, OR",
            "Is_Newly_Licensed": False,
            "Has_New_State_Added": False,
            "Phone": "619-555-0199",
            "Email": "dmiller@deserthorizon.com",
        },
    ]

    df = pd.DataFrame(raw_data)

    df["Lead_Trigger"] = df.apply(classify_lead_trigger, axis=1)

    lic_results = df["States"].str.split(",").apply(evaluate_licensing)
    df["Approved_States"] = [r[0] for r in lic_results]
    df["Licensing_Flags"] = [r[1] for r in lic_results]

    def calculate_priority(row):
        score = 1
        if "Brand New Licensee" in row["Lead_Trigger"]:
            score += 3
        if "Ex-Institutional" in row["Lead_Trigger"]:
            score += 3
        if "Sponsorship Transfer" in row["Lead_Trigger"]:
            score += 2
        if "Expanded into New State" in row["Lead_Trigger"]:
            score += 2
        return score

    df["Priority_Score"] = df.apply(calculate_priority, axis=1)
    df = df.sort_values(by="Priority_Score", ascending=False)

    output_path = "master_leads.csv"
    df.to_csv(output_path, index=False)
    print(f"Successfully exported {len(df)} leads to {output_path}.")


if __name__ == "__main__":
    fetch_and_process_nmls_leads()
