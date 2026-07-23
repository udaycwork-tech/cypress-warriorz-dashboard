import streamlit as st

# Configure the main page settings
st.set_page_config(
    page_title="Cypress Warriorz | Analytics Hub",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to inject a modern, visually appealing UI
st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem;
        color: #D4AF37; /* Warriorz Gold */
        text-align: center;
        font-weight: 800;
        margin-bottom: 0px;
        padding-top: 20px;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #A3A3A3; /* Light Gray for contrast */
        text-align: center;
        margin-top: -10px;
        margin-bottom: 40px;
        font-weight: 400;
    }
    .feature-card {
        background-color: #1A1A1A; /* Sleek Dark/Black Background */
        padding: 25px;
        border-radius: 12px;
        border-left: 6px solid #D4AF37; /* Warriorz Gold Accent */
        box-shadow: 0 4px 6px -1px rgba(212, 175, 55, 0.15), 0 2px 4px -1px rgba(212, 175, 55, 0.1); /* Subtle gold glow */
        height: 100%;
        color: #E0E0E0; /* Explicitly setting text color so it never goes invisible */
    }
    .feature-card p, .feature-card ul {
        color: #E0E0E0; /* Ensuring lists and paragraphs are readable */
    }
    .feature-title {
        color: #D4AF37; /* Warriorz Gold */
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 15px;
    }
    .highlight-text {
        color: #FFFFFF; /* Pure White for popping contrast */
        font-weight: 700;
        border-bottom: 1px solid #D4AF37; /* Little gold underline */
    }
</style>
""", unsafe_allow_html=True)

# Headers
st.markdown('<p class="main-header">Cypress Warriorz Analytics Hub</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Data-Driven Excellence on the Court</p>', unsafe_allow_html=True)

st.divider()

# Intro Text
st.markdown("### Welcome to the Command Center")
st.write(
    "This portal connects directly to our secure Snowflake data warehouse, delivering real-time "
    "insights and predictive modeling to give the Cypress Warriorz a competitive edge. "
    "Use the sidebar on the left to navigate through our intelligence modules."
)

st.write("") # Spacer

# Create two columns for the feature cards
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">📊 Player Analysis Module</div>
        <p>Dive deep into historical performance with dynamic, interactive data visualizations. This page allows you to:</p>
        <ul>
            <li><span class="highlight-text">Track Historical Trends:</span> Monitor how player stats fluctuate across games and entire seasons.</li>
            <li><span class="highlight-text">Comparative Metrics:</span> Instantly see how individual athletes stack up against team averages and baseline benchmarks.</li>
            <li><span class="highlight-text">Strategic Indicators:</span> Visualize scoring efficiency, defensive impact, and advanced metrics to optimize playtime and game-day strategy.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">🤖 AI Projections Engine</div>
        <p>Leverage our custom-built Machine Learning pipeline to look into the future. This page features:</p>
        <ul>
            <li><span class="highlight-text">Advanced Algorithms:</span> Powered by PyTorch Neural Networks and Scikit-Learn Random Forests.</li>
            <li><span class="highlight-text">Future Performance:</span> Generate statistically rigorous projections based on historical training data securely stored in Snowflake.</li>
            <li><span class="highlight-text">The Competitive Edge:</span> Anticipate player trajectories and performance ceilings before they happen.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.write("") # Spacer
st.divider()

# Call to action pointing to the sidebar
st.info("👈 **Ready to explore? Select 'Player Analysis' from the sidebar menu to the left to begin.**")
