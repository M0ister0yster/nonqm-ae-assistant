import os
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Champions Funding AE Pocket Assistant",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Champions Funding AE Pocket Assistant")

tab1, tab2 = st.tabs(["🧮 DSCR Scenario Calculator", "📋 NMLS Lead Directory"])

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

with tab2:
    st.header("NMLS Master Leads")
    if os.path.exists("master_leads.csv"):
        df = pd.read_csv("master_leads.csv")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No master_leads.csv file found in root directory.")
