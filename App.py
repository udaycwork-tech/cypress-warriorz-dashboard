import streamlit as st
import base64
import os

# Configure the main page settings
st.set_page_config(
    page_title="Cypress Warriorz | Analytics Hub",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to get base64 image so we can embed it securely into the CSS
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

# Read the local image file you referenced
img_base64 = get_base64_of_bin_file("image_4b1e47.jpg")
bg_style = f"background-image: url('data:image/jpeg;base64,{img_base64}');" if img_base64 else "background-color: #1A1A1A;"

# Custom CSS to inject a modern, visually appealing UI
st.markdown(f"""
<style>
    /* Force Times New Roman for the entire page body */
    html, body, [class*="css"], p, li, div, h1, h2, h3, h4, h5, h6 {{
        font-family: 'Times New Roman', Times, serif !important;
    }}
    
    .hero-section {{
        {bg_style}
        background-size: cover;
        background-position: center;
        padding: 80px 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 40px;
        /* Dark transparent overlay so the gold text is readable over the bright image */
        box-shadow: inset 0 0 0 2000px rgba(15, 15, 15, 0.75);
        border: 2px solid #D4AF37;
    }}
    
    .main-header {{
        font-size: 5rem !important; /* Significantly larger */
        color: #D4AF37 !important; /* Warriorz Gold */
        font-family: 'Arial Black', Impact, sans-serif !important; /* Sleek, bold athletic font */
        font-weight: 900;
        margin-bottom: 0px;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.9); /* Heavy drop shadow for contrast */
        line-height: 1.1;
    }}
    .sub-header {{
        font-size: 1.8rem !important;
        color: #E0E0E0 !important;
        margin-top: 15px;
        font-weight: 600;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.9);
    }}
    .feature-card {{
        background-color: #1A1A1A; /* Sleek Dark/Black Background */
        padding: 25px;
        border-radius: 12px;
        border-left: 6px solid #D4AF37; /* Warriorz Gold Accent */
        box-shadow: 0 4px 6px -1px rgba(212, 175, 55, 0.15), 0 2px 4px -1px rgba(212, 175, 55, 0.1); /* Subtle gold glow */
        height: 100%;
        color: #E0E0E0; /* Explicitly setting text color so it never goes invisible */
    }}
    .feature-card p, .feature-card ul {{
        color: #E0E0E0; /* Ensuring lists and paragraphs are readable */
    }}
    .feature-title {{
        color: #D4AF37; /* Warriorz Gold */
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 15px;
    }}
    .highlight-text {{
        color: #FFFFFF; /* Pure White for popping contrast */
        font-weight: 700;
        border-bottom: 1px solid #D4AF37; /* Little gold underline */
    }}
</style>
""", unsafe_allow_html=True)

# Headers - Wrapped in the new hero-section div
st.markdown(f'''
<div class="hero-section">
    <p class="main-header">Cypress Warriorz Analytics Hub</p>
    <p class="sub-header">Data-Driven Excellence on the Field</p>
</div>
''', unsafe_allow_html=True)

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
