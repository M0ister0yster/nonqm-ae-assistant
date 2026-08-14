import streamlit as st

st.set_page_config(
    page_title="Champions Funding AE Pocket Assistant",
    page_icon="🏠",
    layout="centered",
)

st.title("🏠 Champions Funding AE Pocket Assistant")
st.caption("NMLS #2254210 — Instant DSCR Calculator & Eligibility Engine")

st.markdown("---")

# ==========================================
# SECTION 1: STATE & LOCATION ELIGIBILITY
# ==========================================
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

# City restriction check for MD and PA overlays
selected_city = ""
if selected_state in ["MD", "PA"]:
    selected_city = st.text_input(
        "Enter City Name (Checks for Baltimore / Philly Overlays):"
    )

# State Licensing Rules Mapping
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

# Consumer Ally Program Permitted States
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

# Business Purpose Eligibility Evaluation
if loan_purpose == "Business Purpose (DSCR / Investment / Rental)":
    if selected_state in ["ND", "SD"]:
        st.error(
            f"❌ **CANNOT LEND IN {selected_state}:** Champions Funding does NOT originate Business Purpose / DSCR loans in North or South Dakota."
        )
    else:
        st.success(
            f"✅ **ELIGIBLE:** Business Purpose / DSCR loans permitted in **{selected_state}**."
        )

        # Licensing Alerts
        if selected_state in broker_lic_req:
            st.warning(f"⚠️ **LICENSING NOTICE:** {broker_lic_req[selected_state]}")

        # Attestation Form Alert for NY / NJ
        if selected_state in ["NY", "NJ"]:
            st.info(
                f"📝 **ATTESTATION REQUIRED:** Unlicensed Brokers in {selected_state} must complete a Business Purpose Broker Attestation."
            )

        # City Restriction Warnings
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
    # Consumer Purpose Evaluation
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

# ==========================================
# SECTION 2: DSCR CALCULATION ENGINE
# ==========================================
st.header("2. DSCR Calculation")

rental_type = st.radio(
    "Select Property Rental Type:",
    ["Long-Term Rental (LTR)", "Short-Term Rental (STR / Airbnb)"],
    horizontal=True,
)

gross_rent = 0.0

if rental_type == "Long-Term Rental (LTR)":
    st.caption("🏆 **Selling Point:** Champions Funding takes the HIGHER of Lease Agreement vs. Market Rent.")
    c1, c2 = st.columns(2)
    with c1:
        lease_rent = st.number_input(
            "Lease Agreement Rent ($/mo)", min_value=0.0, value=2500.0, step=100.0
        )
    with c2:
        market_rent = st.number_input(
            "Form 1007 Market Rent ($/mo)",
            min_value=0.0,
            value=2700.0,
            step=100.0,
        )

    # CHAMPIONS FUNDING RULE: Take whichever is HIGHER
    gross_rent = max(lease_rent, market_rent)
    st.info(
        f"💡 **Qualifying Gross Rent Used:** **${gross_rent:,.2f}** *(Using the HIGHER value between Lease Rent and Market Rent)*"
    )

else:
    st.caption("📊 **STR Rule:** 12-Month Average Monthly Revenue reduced by 20% for operating expenses.")
    str_gross = st.number_input(
        "Total 12-Month STR Gross Revenue ($)",
        min_value=0.0,
        value=60000.0,
        step=1000.0,
    )
    monthly_avg = str_gross / 12.0
    # CHAMPIONS FUNDING RULE: 20% OpEx Haircut (80% qualifying)
    gross_rent = monthly_avg * 0.80
    st.info(
        f"💡 **12-Mo Monthly Average:** ${monthly_avg:,.2f}/mo | **Qualifying Gross Rent (80%):** **${gross_rent:,.2f}**"
    )

# Housing Expenses (PITIA)
st.subheader("Monthly Housing Expense (PITIA)")
col_p1, col_p2, col_p3, col_p4 = st.columns(4)
with col_p1:
    pi = st.number_input("P&I ($)", min_value=0.0, value=1800.0, step=50.0)
with col_p2:
    taxes = st.number_input("Taxes ($)", min_value=0.0, value=300.0, step=25.0)
with col_p3:
    ins = st.number_input("Insurance ($)", min_value=0.0, value=150.0, step=25.0)
with col_p4:
    hoa = st.number_input("HOA ($)", min_value=0.0, value=0.0, step=25.0)

pitia = pi + taxes + ins + hoa

# ==========================================
# SECTION 3: RESULTS & COPY/PASTE PITCH
# ==========================================
if pitia > 0:
    dscr = gross_rent / pitia

    st.markdown("---")
    st.header("3. Scenario Results & LO Response")

    m1, m2, m3 = st.columns(3)
    m1.metric("Gross Rent Used", f"${gross_rent:,.2f}")
    m2.metric("Total PITIA", f"${pitia:,.2f}")
    m3.metric("DSCR Ratio", f"{dscr:.2f}x")

    # Qualification Tiers
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

    # Generated Copy-Paste Message for LO Outreach
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
else:
    st.info("Enter PITIA components above to see the calculated DSCR ratio and pitch output.")
