import os
import pandas as pd
import streamlit as st
from apify_client import ApifyClient

# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Champions Funding AE Suite", 
    page_icon="🏠", 
    layout="centered"
)

# =========================================================
# APIFY CLIENT INITIALIZATION
# =========================================================
# Paste your raw Apify API key inside the quotes below
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
client = ApifyClient(APIFY_TOKEN)

# =========================================================
# CUSTOM CSS: ENLARGE MENUS & DROPDOWNS
# =========================================================
st.markdown(
    """
    <style>
    /* Make selectbox and multiselect input fields larger */
    .stSelectbox div[data-baseweb="select"],
    .stMultiSelect div[data-baseweb="select"] {
        font-size: 18px !important;
        min-height: 52px !important;
    }
    
    /* Make dropdown options text & padding larger */
    div[data-baseweb="popover"] ul li {
        font-size: 18px !important;
        padding: 12px !important;
    }
    
    /* Enlarge tab titles */
    button[data-baseweb="tab"] {
        font-size: 18px !important;
        font-weight: bold !important;
    }
    
    /* Increase table display font size */
    .stDataFrame {
        font-size: 16px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# APPLICATION TABS NAVIGATION
# =========================================================
tab1, tab2 = st.tabs(
    ["📊 DSCR Scenario Desk", "🎯 NMLS Automated Lead Pipeline"]
)

# =========================================================
# TAB 1: DSCR & LOCATION SCENARIO DESK
# =========================================================
with tab1:
    st.title("🏠 Champions Funding AE Pocket Assistant")
    st.caption("NMLS #2254210 – Instant DSCR Calculator & Eligibility Engine")
    st.markdown("---")
    st.header("1. State & Location Eligibility Check")
    st.write("Use your existing DSCR calculator and loan guidelines engine here.")

# =========================================================
# TAB 2: AUTOMATED LEAD PIPELINE (APIFY INTEGRATION)
# =========================================================
with tab2:
    st.title("🎯 Champions Funding Lead Finder")
    st.caption("Automated MLO & Independent Broker Prospecting Engine")
    st.markdown("---")

    st.subheader("LinkedIn Profile & Email Extractor")
    urls_input = st.text_area(
        "Paste Target MLO LinkedIn Profile URLs (One per line):",
        height=150,
        placeholder="https://www.linkedin.com/in/sample-mlo-1\nhttps://www.linkedin.com/in/sample-mlo-2",
    )

    if st.button("🚀 Scrape Profiles & Find Emails"):
        urls = [url.strip() for url in urls_input.split("\n") if url.strip()]

        if not urls:
            st.warning("Please paste at least one valid LinkedIn URL.")
        else:
            with st.spinner("Processing profiles and querying verified emails via Apify..."):
                try:
                    # Input payload for harvestapi/linkedin-profile-scraper Actor
                    run_input = {
                        "queries": urls,
                        "profileScraperMode": "Profile details + email search ($10 per 1k)",
                    }

                    # Trigger Apify actor remotely
                    run = client.actor("harvestapi/linkedin-profile-scraper").call(
                        run_input=run_input
                    )

                    scraped_leads = []
                    dataset_items = client.dataset(
                        run["defaultDatasetId"]
                    ).iterate_items()

                    for item in dataset_items:
                        scraped_leads.append(
                            {
                                "Full Name": item.get("fullName")
                                or f"{item.get('firstName', '')} {item.get('lastName', '')}".strip(),
                                "Title / Headline": item.get("headline"),
                                "Company": item.get("companyName")
                                or item.get("company"),
                                "Location": item.get("location"),
                                "Email": item.get("email") or "Not Found",
                                "LinkedIn URL": item.get("linkedinUrl")
                                or item.get("url"),
                                "Status": "New Lead",
                            }
                        )

                    df_new = pd.DataFrame(scraped_leads)

                    # Update or create master_leads.csv
                    try:
                        df_master = pd.read_csv("master_leads.csv")
                        df_updated = pd.concat([df_master, df_new]).drop_duplicates(
                            subset=["LinkedIn URL"]
                        )
                    except FileNotFoundError:
                        df_updated = df_new

                    df_updated.to_csv("master_leads.csv", index=False)

                    st.success(
                        f"Successfully extracted {len(df_new)} MLO leads into master_leads.csv!"
                    )
                    st.dataframe(df_new)

                except Exception as e:
                    st.error(f"Error executing Apify scraper: {str(e)}")
