import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Champions Funding AE Suite", page_icon="🏠", layout="centered"
)

# ==========================================
# CUSTOM CSS: ENLARGE MENUS & DROPDOWNS
# ==========================================
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

tab1, tab2 = st.tabs(
    ["🧮 DSCR Scenario Desk", "🎯 NMLS Automated Lead Pipeline"]
)

# ==========================================
# TAB 1: DSCR & LOCATION SCENARIO DESK
# ==========================================
with tab1:
    st.title("🏠 Champions Funding AE Pocket Assistant")
    st.caption("NMLS #2254210 — Instant DSCR Calculator & Eligibility Engine")

    st.markdown("---")
    st.header("1. State & Location Eligibility Check")

    col_state, col_purpose = st.columns(2)

    states = [
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
        "DC",
    ]

    with col_state:
        selected_state = st.selectbox("Select Property State:", sorted(states))

    with col_purpose:
        loan_purpose = st.selectbox(
            "Select Loan Purpose:",
            [
                "Business Purpose (DSCR / Investment / Rental)",
                "Consumer Purpose (Primary / Secondary Home)",
            ],
        )

    selected_city = ""
    if selected_state in ["MD", "PA"]:
        selected_city = st.text_input(
            "Enter City Name (Checks for Baltimore / Philly Overlays):"
        )

    broker_lic_req = {
        "CA": "Pink Pin: Broker License Required",
        "AZ": "Pink Pin: Broker License Required",
        "MT": "Pink Pin: Broker License Required",
        "MI": "Pink Pin: Broker License Required",
        "VA": "Pink Pin: Broker License Required",
        "VT": "Pink Pin: Broker License Required",
        "OR": "Light Blue Pin: BOTH Broker AND Loan Originator License Required",
        "ID": "Light Blue Pin: BOTH Broker AND Loan Originator License Required",
        "UT": "Light Blue Pin: BOTH Broker AND Loan Originator License Required",
        "MN": "Light Blue Pin: BOTH Broker AND Loan Originator License Required",
    }

    ally_states = [
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

    if loan_purpose == "Business Purpose (DSCR / Investment / Rental)":
        if selected_state in ["ND", "SD"]:
            st.error(
                f"❌ **CANNOT LEND IN {selected_state}:** Champions Funding does NOT originate Business Purpose / DSCR loans in North or South Dakota."
            )
        else:
            st.success(
                f"✅ **ELIGIBLE:** Business Purpose / DSCR loans permitted in **{selected_state}**."
            )

            if selected_state in broker_lic_req:
                st.warning(
                    f"⚠️ **LICENSING NOTICE:** {broker_lic_req[selected_state]}"
                )

            if selected_state in ["NY", "NJ"]:
                st.info(
                    f"📝 **ATTESTATION REQUIRED:** Unlicensed Brokers in {selected_state} must complete a Business Purpose Broker Attestation."
                )

            if "baltimore" in selected_city.lower():
                st.error(
                    "🚨 **CITY RESTRICTION:** Baltimore, MD has specific city overlays/restrictions. Verify guidelines with Ops before proceeding."
                )
            elif (
                "philadelphia" in selected_city.lower()
                or "philly" in selected_city.lower()
            ):
                st.error(
                    "🚨 **CITY RESTRICTION:** Philadelphia, PA has specific city overlays/restrictions. Verify guidelines with Ops before proceeding."
                )
    else:
        if selected_state in ally_states:
            st.success(
                f"✅ **LICENSED & ALLY PERMITTED:** Consumer Purpose permitted in **{selected_state}** (Ally Consumer - No Ratio Permitted)."
            )
        elif selected_state in ["ND", "SD"]:
            st.error(f"❌ **CANNOT LEND IN {selected_state}.**")
        else:
            st.info(
                f"ℹ️ **BUSINESS PURPOSE ONLY STATE:** Consumer primary/secondary home programs may be restricted in **{selected_state}** due to state licensing laws."
            )

    st.markdown("---")
    st.header("2. DSCR Calculation")

    rental_type = st.radio(
        "Select Property Rental Type:",
        ["Long-Term Rental (LTR)", "Short-Term Rental (STR / Airbnb)"],
        horizontal=True,
    )

    gross_rent = 0.0

    if rental_type == "Long-Term Rental (LTR)":
        st.caption(
            "🏆 **Selling Point:** Champions Funding takes the HIGHER of Lease Agreement vs. Market Rent."
        )
        c1, c2 = st.columns(2)
        with c1:
            lease_rent = st.number_input(
                "Lease Agreement Rent ($/mo)",
                min_value=0.0,
                value=2500.0,
                step=100.0,
            )
        with c2:
            market_rent = st.number_input(
                "Form 1007 Market Rent ($/mo)",
                min_value=0.0,
                value=2700.0,
                step=100.0,
            )

        gross_rent = max(lease_rent, market_rent)
        st.info(
            f"💡 **Qualifying Gross Rent Used:** **${gross_rent:,.2f}** *(Using the HIGHER value between Lease Rent and Market Rent)*"
        )

    else:
        st.caption(
            "📊 **STR Rule:** 12-Month Average Monthly Revenue reduced by 20% for operating expenses."
        )
        str_gross = st.number_input(
            "Total 12-Month STR Gross Revenue ($)",
            min_value=0.0,
            value=60000.0,
            step=1000.0,
        )
        monthly_avg = str_gross / 12.0
        gross_rent = monthly_avg * 0.80
        st.info(
            f"💡 **12-Mo Monthly Average:** ${monthly_avg:,.2f}/mo | **Qualifying Gross Rent (80%):** **${gross_rent:,.2f}**"
        )

    st.subheader("Monthly Housing Expense (PITIA)")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        pi = st.number_input("P&I ($)", min_value=0.0, value=1800.0, step=50.0)
    with col_p2:
        taxes = st.number_input(
            "Taxes ($)", min_value=0.0, value=300.0, step=25.0
        )
    with col_p3:
        ins = st.number_input(
            "Insurance ($)", min_value=0.0, value=150.0, step=25.0
        )
    with col_p4:
        hoa = st.number_input("HOA ($)", min_value=0.0, value=0.0, step=25.0)

    pitia = pi + taxes + ins + hoa

    if pitia > 0:
        dscr = gross_rent / pitia

        st.markdown("---")
        st.header("3. Scenario Results & LO Response")

        m1, m2, m3 = st.columns(3)
        m1.metric("Gross Rent Used", f"${gross_rent:,.2f}")
        m2.metric("Total PITIA", f"${pitia:,.2f}")
        m3.metric("DSCR Ratio", f"{dscr:.2f}x")

        if dscr >= 1.00:
            st.success(
                f"✅ **QUALIFIES: Standard DSCR ({dscr:.2f}x)** — Fully cash-flowing property. Eligible for maximum LTV tiers."
            )
        elif 0.75 <= dscr < 1.00:
            st.warning(
                f"⚠️ **QUALIFIES: Low-Ratio DSCR ({dscr:.2f}x)** — Fits Low-Ratio guidelines (check LTV and credit score matrix)."
            )
        else:
            st.error(
                f"🚨 **QUALIFIES: No-Ratio / Zero-DSCR Needed ({dscr:.2f}x)** — DSCR below 0.75. Must run under No-Ratio program."
            )

        st.subheader("Copy/Paste Message for Loan Officer:")

        lic_text = ""
        if selected_state in broker_lic_req:
            lic_text = f"\n• Licensing Note: {broker_lic_req[selected_state]}"
        elif selected_state in ["NY", "NJ"]:
            lic_text = "\n• Note: Requires Business Purpose Attestation Form for unlicensed brokers."

        pitch_text = (
            f"Hey [Broker Name]! I ran the numbers on your {selected_state} scenario:\n\n"
            f"• Qualifying Rent: ${gross_rent:,.2f}/mo "
            f"({'Used higher of Lease vs Market Rent' if rental_type == 'Long-Term Rental (LTR)' else '80% of 12-Mo STR Gross Avg'})\n"
            f"• Total Monthly PITIA: ${pitia:,.2f}\n"
            f"• Calculated DSCR: {dscr:.2f}x\n"
            f"{lic_text}\n\n"
            f"We can write this deal without tax returns or personal income docs! Let me know if you want me to lock this scenario in for you."
        )

        st.code(pitch_text, language="text")

# ==========================================
# TAB 2: AUTOMATED NMLS LEAD PIPELINE
# ==========================================
with tab2:
    st.title("🎯 Automated NMLS Lead Pipeline")
    st.caption(
        "Auto-synced weekly. Prioritizes brand-new MLOs, company transfers, and state expansions."
    )

    lead_file = "master_leads.csv"

    if os.path.exists(lead_file):
        df_leads = pd.read_csv(lead_file)

        new_lic = len(
            df_leads[df_leads["Lead_Trigger"].str.contains("Brand New", na=False)]
        )
        moves = len(
            df_leads[
                df_leads["Lead_Trigger"].str.contains(
                    "Transfer|Ex-Institutional", na=False
                )
            ]
        )
        expansions = len(
            df_leads[df_leads["Lead_Trigger"].str.contains("Expanded", na=False)]
        )

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total Active Leads", len(df_leads))
        col_m2.metric("🆕 Brand-New MLOs", new_lic)
        col_m3.metric("🔄 Company Moves", moves)
        col_m4.metric("🗺️ State Additions", expansions)

        st.markdown("---")

        c_f1, c_f2 = st.columns(2)
        with c_f1:
            trigger_filter = st.multiselect(
                "Filter by Outreach Trigger:",
                options=[
                    "Brand New Licensee",
                    "Ex-Institutional LO",
                    "Sponsorship Transfer",
                    "Expanded into New State",
                ],
            )
        with c_f2:
            target_filter = st.multiselect(
                "Filter by Approved State License:",
                options=sorted(
                    list(
                        set(
                            [
                                s.strip()
                                for sublist in df_leads[
                                    "Approved_States"
                                ].dropna()
                                for s in sublist.split(",")
                            ]
                        )
                    )
                ),
            )

        df_display = df_leads.copy()

        if trigger_filter:
            p_trig = "|".join(trigger_filter)
            df_display = df_display[
                df_display["Lead_Trigger"].str.contains(
                    p_trig, case=False, na=False
                )
            ]

        if target_filter:
            p_state = "|".join(target_filter)
            df_display = df_display[
                df_display["Approved_States"].str.contains(
                    p_state, case=False, na=False
                )
            ]

        st.dataframe(df_display, use_container_width=True)

        st.download_button(
            label="📥 Export Filtered Pipeline (CSV)",
            data=df_display.to_csv(index=False),
            file_name="champions_priority_leads.csv",
            mime="text/csv",
        )
    else:
        st.info(
            "🔄 **Initializing Pipeline...** The background scraper is preparing your first lead batch."
        )
