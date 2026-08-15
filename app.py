import os
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Champions Funding AE Pocket Assistant",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Champions Funding AE Pocket Assistant")

tab1, tab2 = st.tabs(["🧮 DSCR Scenario Calculator", "📋 MLO Lead Directory"])

# ----------------- TAB 1: DSCR CALCULATOR -----------------
with tab1:
    st.header("DSCR Calculator")
    col1, col2 = st.columns(2)
    
    with col1:
        gross_rent = st.number_input("Gross Monthly Rental Income ($)", min_value=0.0, value=3000.0, step=100.0)
        pitia = st.number_input("Monthly PITIA ($)", min_value=0.0, value=2200.0, step=100.0)
    
    with col2:
        if pitia > 0:
            dscr = gross_rent / pitia
            st.metric(label="Calculated DSCR", value=f"{dscr:.2f}")
            if dscr >= 1.0:
                st.success("Qualifies for Standard DSCR Program (>= 1.0)")
            elif dscr >= 0.75:
                st.warning("Low DSCR Tier (0.75 - 0.99)")
            else:
                st.error("No-Ratio / Non-Qualifying (< 0.75)")
        else:
            st.info("Enter PITIA to calculate DSCR.")

# ----------------- TAB 2: MLO LEAD DIRECTORY -----------------
with tab2:
    st.header("MLO Lead Directory & Prioritization")
    
    # Drag-and-drop CSV Uploader
    uploaded_file = st.file_uploader("Upload Zillow/NMLS Scraped CSV File", type=["csv"])
    
    df = None
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("Loaded uploaded CSV dataset!")
    elif os.path.exists("master_leads.csv"):
        df = pd.read_csv("master_leads.csv")
        st.info("Loaded master_leads.csv from repository.")
    
    if df is not None:
        search_query = st.text_input("🔍 Search Leads (by Name, Brokerage, NMLS #, or City):")
        
        if search_query:
            mask = df.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
            df_display = df[mask]
        else:
            df_display = df
            
        st.write(f"Showing **{len(df_display)}** leads:")
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Upload a CSV file above or save 'master_leads.csv' to view your leads.")
