import streamlit as st

st.set_page_config(
    page_title="Cypress Warriorz | Analytics Hub",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        color: #A3A3A3;
        text-align: center;
        margin-top: -10px;
        margin-bottom: 40px;
        font-weight: 400;
    }
    .feature-card {
        background-color: #1A1A1A;
        padding: 25px;
        border-radius: 12px;
        border-left: 6px solid #D4AF37;
        box-shadow: 0 4px 6px -1px rgba(212, 175, 55, 0.15), 0 2px 4px -1px rgba(212, 175, 55, 0.1);
        height: 100%;
        color: #E0E0E0;
    }
    .feature-card p, .feature-card ul {
        color: #E0E0E0;
    }
    .feature-title {
        color: #D4AF37;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 15px;
    }
    .highlight-text {
        color: #FFFFFF;
        font-weight: 700;
        border-bottom: 1px solid #D4AF37;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">Cypress Warriorz Analytics Hub</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Data-Driven Excellence on the Pitch</p>', unsafe_allow_html=True)

st.divider()

st.markdown("### Welcome to the Command Center")
st.write(
    "This portal connects directly to our secure Neon PostgreSQL cloud data warehouse, delivering real-time "
    "insights and predictive modeling to give the Cypress Warriorz a competitive edge. "
    "Use the sidebar on the left to navigate through our intelligence modules."
)

st.write("") 

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">📊 Player Analysis Module</div>
        <p>Dive deep into historical performance with dynamic, interactive data visualizations. This page allows you to:</p>
        <ul>
            <li><span class="highlight-text">Track Historical Trends:</span> Monitor how player stats fluctuate across games and seasons.</li>
            <li><span class="highlight-text">Comparative Metrics:</span> Instantly see how individual athletes stack up against team benchmarks.</li>
            <li><span class="highlight-text">Strategic Indicators:</span> Visualize scoring efficiency, strike rates, and defensive impact.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-title">🤖 AI Projections Engine</div>
        <p>Leverage our custom-built Machine Learning pipeline to anticipate matchday outcomes. This page features:</p>
        <ul>
            <li><span class="highlight-text">Advanced Deep Learning:</span> Powered by PyTorch Neural Networks and Scikit-Learn.</li>
            <li><span class="highlight-text">Combinatorial Lineup Solver:</span> SciPy Mixed-Integer Linear Programming for optimal 11-man roster selection.</li>
            <li><span class="highlight-text">Strategic Partnerships:</span> Historical pairwise synergy scoring to optimize on-pitch partnerships.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.write("") 
st.divider()

st.info("👈 **Ready to explore? Select '1_Player_Stats' from the sidebar menu to the left to begin.**")