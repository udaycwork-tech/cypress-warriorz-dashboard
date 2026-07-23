import streamlit as st
import os

st.set_page_config(page_title="Warriorz Analytics", page_icon="🏏", layout="centered")

st.markdown("""
    <style>
        .stApp { background-color: #0b0b0d; color: #ffffff; }
        h1 { color: #d4af37; font-family: 'Arial Black', sans-serif; }
        h3 { color: #a1a1aa; }
        hr { border-top: 2px solid #d4af37; }
    </style>
""", unsafe_allow_html=True)

logo_path = "assets/CWCCNEWLOGO.jpeg"
if os.path.exists(logo_path):
    st.image(logo_path, width=200)

st.title("Cypress Warriorz Data Infrastructure")
st.markdown("### End-to-End Sports Analytics & Machine Learning Pipeline")
st.divider()

st.markdown("""
Welcome to the internal data portal for the Cypress Warriorz. This platform orchestrates raw match data into actionable, mathematically optimized on-field strategies.

**Technical Architecture:**
*   **Data Warehouse:** Snowflake (Star Schema modeling with Fact and Dimension tables).
*   **ETL Pipeline:** Automated extraction and cleaning of raw CSV match logs into structured operational tables.
*   **Deep Learning Engine:** PyTorch neural networks trained to project multi-target player performance.
*   **Combinatorial Optimization:** SciPy Mixed-Integer Linear Programming (MILP) to generate optimal 11-man lineups.
*   **Frontend:** Streamlit integration for live strategic modeling and historical record keeping.

👈 **Use the sidebar to navigate between the AI Strategy Engine and the Historical Player Database.**
""")