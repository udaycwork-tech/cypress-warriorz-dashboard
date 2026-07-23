import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import joblib
import platform

# --- DEEP LEARNING & OPTIMIZATION IMPORTS ---
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from scipy.optimize import milp, LinearConstraint, Bounds

# --- WINDOWS ENVIRONMENT PATCH ---
platform.libc_ver = lambda *args, **kwargs: ("", "")

# Removed legacy train_ai_predictor and generate_weekend_lineup
from ml_pipeline import (
    engineer_all_features, 
    calculate_pairwise_synergy
)

# ==========================================
# 1. VISUAL CANVAS STYLING DIRECTIVES
# ==========================================
st.set_page_config(
    page_title="Warriorz AI Engine", 
    page_icon="🏏", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .stApp { background-color: #0b0b0d; color: #ffffff; }
        h1, h2, h3 { color: #d4af37 !important; font-family: 'Arial Black', sans-serif; letter-spacing: 0.5px; }
        div[data-testid="stMetricValue"] { color: #d4af37; font-size: 3rem; font-weight: 900; }
        div[data-testid="stMetricLabel"] { color: #a1a1aa; font-size: 1.1rem; text-transform: uppercase; }
        .stSelectbox label, .stMultiSelect label { color: #d4af37 !important; font-weight: bold; }
        hr { border-top: 2px solid #d4af37 !important; }
        .dashboard-card { border: 2px solid #d4af37; border-radius: 12px; padding: 25px; background-color: #121216; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .badge-lock { background-color: #2e2509; color: #d4af37; padding: 6px 12px; font-weight: bold; border-radius: 6px; border: 1px solid #d4af37; font-size: 0.85rem; }
    </style>
""", unsafe_allow_html=True)

logo_path = "assets/CWCCNEWLOGO.jpeg"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)


# ==========================================
# 2. DEEP LEARNING ARCHITECTURE (PYTORCH)
# ==========================================
class WarriorzNet(nn.Module):
    def __init__(self, input_features):
        super(WarriorzNet, self).__init__()
        self.fc1 = nn.Linear(input_features, 128)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(128, 64)
        self.dropout = nn.Dropout(0.2)
        self.fc3 = nn.Linear(64, 32)
        # Outputs: [Runs, Wickets, Points]
        self.output = nn.Linear(32, 3)

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.relu(self.fc3(x))
        return self.output(x)


# ==========================================
# 3. FILE INTERACTION & PIPELINE METHODS
# ==========================================
@st.cache_data(ttl="10m")
def fetch_base_roster():
    try:
        conn = st.connection("snowflake")
        roster_df = conn.query("""
            SELECT PLAYER_NAME 
            FROM CYPRESS_WARRIORZ_DW.RAW_DATA.DIM_PLAYER 
            WHERE IS_ACTIVE = TRUE
            ORDER BY PLAYER_NAME ASC;
        """)
        return roster_df['PLAYER_NAME'].tolist()
    except Exception as e:
        st.sidebar.error(f"🔌 Snowflake Connection Failed: {e}")
        return []

@st.cache_resource
def load_trained_pipeline():
    if os.path.exists('models/training_features.joblib') and os.path.exists('models/warriorz_net.pth'):
        try:
            features = joblib.load('models/training_features.joblib')
            synergy = joblib.load('models/synergy_matrix.joblib')
            historical = joblib.load('models/historical_features.joblib')
            
            # Reconstruct PyTorch Model
            model = WarriorzNet(input_features=len(features))
            model.load_state_dict(torch.load('models/warriorz_net.pth'))
            model.eval()
            
            return model, features, synergy, historical, False
        except Exception:
            pass
    return None, None, None, None, True

all_players = fetch_base_roster()
pytorch_model, training_features, df_synergy, df_engineered, needs_training = load_trained_pipeline()


# ==========================================
# 4. MATHEMATICAL OPTIMIZER (SCIPY MILP)
# ==========================================
def scipy_optimize_lineup(players_df, active_roster):
    """
    Applies Mixed-Integer Linear Programming to find the 
    mathematically optimal 11-man squad meeting all constraints.
    """
    # Filter for active players only
    df = players_df[players_df['PLAYER_NAME'].isin(active_roster)].copy().reset_index(drop=True)
    
    if len(df) < 11:
        return pd.DataFrame()

    N = len(df)
    
    # Objective: Maximize Points (SciPy minimizes, so make coefficients negative)
    c = -df['AI_Projected_Points'].values
    
    # Constraint 1: Exactly 11 players
    A_eq = np.ones((1, N))
    b_eq = np.array([11])
    
    # Constraint 2: Total Wickets between 8 and 10
    A_wicket = df['AI_Projected_Wickets'].values.reshape(1, N)
    lb_wicket = np.array([8])
    ub_wicket = np.array([10])
    
    constraints = [
        LinearConstraint(A_eq, b_eq, b_eq),
        LinearConstraint(A_wicket, lb_wicket, ub_wicket)
    ]
    
    # Bounds: The Leadership Lock
    lb = np.zeros(N)
    ub = np.ones(N)
    
    for idx, row in df.iterrows():
        if row['PLAYER_NAME'] in ['Uday Chaudhary', 'Garv Chaudhary']:
            lb[idx] = 1  # Force selection
            
    bounds = Bounds(lb, ub)
    integrality = np.ones(N) # Binary variables
    
    # Run Solver
    res = milp(c=c, constraints=constraints, bounds=bounds, integrality=integrality)
    
    if res.success:
        selected_indices = np.round(res.x).astype(bool)
        optimal_team = df[selected_indices].copy()
        
        # Assign Batting Order by Projected Runs
        optimal_team = optimal_team.sort_values(by='AI_Projected_Runs', ascending=False).reset_index(drop=True)
        optimal_team['Optimal_Batting_Order'] = optimal_team.index + 1
        
        return optimal_team
    else:
        st.error("🚨 Math Engine Failed: Could not satisfy the 8-10 wicket constraint with the selected squad.")
        return pd.DataFrame()


# ==========================================
# 5. INTERACTIVE CONTROL SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<h1>WARRIORZ ANALYTICS</h1>", unsafe_allow_html=True)
    st.caption("Deep Learning Multi-Target Projections Engine")
    st.divider()
    
    st.subheader("🏏 Roster Check-In")
    active_sign_ups = st.multiselect(
        "Available Matchday Squad:",
        options=all_players,
        default=all_players[:12] if len(all_players) >= 12 else all_players
    )
    
    run_optimization = st.button("⚡ Run Lineup Optimization", use_container_width=True, type="primary")
    st.divider()
    
    with st.expander("⚙️ Core Database Tools"):
        if st.button("Synchronize & Retrain Pipeline"):
            with st.spinner("Executing ETL & Training Neural Network..."):
                try:
                    conn = st.connection("snowflake")
                    # Extraction query remains unchanged
                    ml_data_query = """
                        SELECT 
                            dp.PLAYER_NAME, ffp.File_Name AS MATCH_LOG_ID, ffp.Season AS SEASON,
                            COALESCE(fb.Runs, 0) AS RUNS_SCORED, COALESCE(fb.Balls, 0) AS BALLS_FACED,
                            COALESCE(fb.Batting_Position, 'N/A') AS BATTING_POSITION,
                            COALESCE(fbo.Wickets, 0) AS WICKETS_TAKEN, COALESCE(fbo.Runs, 0) AS RUNS_CONCEDED,
                            COALESCE(fbo.Overs, 0) AS OVERS_BOWLED,
                            COALESCE(fma.Catches, 0) AS CATCHES, COALESCE(fma.Stumpings, 0) AS STUMPINGS,
                            COALESCE(fma.Run_Outs, 0) AS RUN_OUTS, ffp.Total_Pts AS FANTASY_PTS
                        FROM CYPRESS_WARRIORZ_DW.RAW_DATA.DIM_PLAYER dp
                        JOIN CYPRESS_WARRIORZ_DW.RAW_DATA.FACT_FANTASY_POINTS ffp ON dp.PLAYER_NAME = ffp.Player_Name
                        LEFT JOIN CYPRESS_WARRIORZ_DW.RAW_DATA.FACT_BATTING fb ON dp.PLAYER_NAME = fb.BatsMan AND ffp.File_Name = fb.File_Name
                        LEFT JOIN CYPRESS_WARRIORZ_DW.RAW_DATA.FACT_BOWLING fbo ON dp.PLAYER_NAME = fbo.Bowler AND ffp.File_Name = fbo.File_Name
                        LEFT JOIN (
                            SELECT 
                                dp2.PLAYER_NAME, ff.File_Name,
                                SUM(CASE WHEN (LOWER(ff."How Out") LIKE '%ct%' OR LOWER(ff."How Out") LIKE '%c%') AND LOWER(ff."How Out") NOT LIKE '%ctw%' THEN 1 ELSE 0 END) AS Catches,
                                SUM(CASE WHEN LOWER(ff."How Out") LIKE '%st%' THEN 1 ELSE 0 END) AS Stumpings,
                                SUM(CASE WHEN LOWER(ff."How Out") LIKE '%ro%' OR LOWER(ff."How Out") LIKE '%run%' THEN 1 ELSE 0 END) AS Run_Outs
                            FROM CYPRESS_WARRIORZ_DW.RAW_DATA.FACT_FIELDING ff
                            JOIN CYPRESS_WARRIORZ_DW.RAW_DATA.DIM_PLAYER dp2 ON ff.Fielder = dp2.FIELDING_ALIAS
                            GROUP BY dp2.PLAYER_NAME, ff.File_Name
                        ) fma ON dp.PLAYER_NAME = fma.PLAYER_NAME AND ffp.File_Name = fma.File_Name;
                    """
                    raw_logs = conn.query(ml_data_query, ttl=0)
                    
                    df_eng = engineer_all_features(raw_logs)
                    df_syn = calculate_pairwise_synergy(df_eng)
                    
                    # Target & Feature Isolation
                    targets = ['RUNS_SCORED', 'WICKETS_TAKEN', 'FANTASY_PTS']
                    train_feats = [col for col in df_eng.select_dtypes(include=[np.number]).columns if col not in targets]
                    
                    # PyTorch Training Loop
                    X_tensor = torch.FloatTensor(df_eng[train_feats].fillna(0).values)
                    y_tensor = torch.FloatTensor(df_eng[targets].fillna(0).values)
                    
                    dataset = TensorDataset(X_tensor, y_tensor)
                    loader = DataLoader(dataset, batch_size=16, shuffle=True)
                    
                    model = WarriorzNet(input_features=len(train_feats))
                    criterion = nn.MSELoss()
                    optimizer = optim.Adam(model.parameters(), lr=0.005)
                    
                    for epoch in range(100):
                        for batch_X, batch_y in loader:
                            optimizer.zero_grad()
                            predictions = model(batch_X)
                            loss = criterion(predictions, batch_y)
                            loss.backward()
                            optimizer.step()
                    
                    # Save Artifacts
                    os.makedirs('models', exist_ok=True)
                    torch.save(model.state_dict(), 'models/warriorz_net.pth')
                    joblib.dump(train_feats, 'models/training_features.joblib')
                    joblib.dump(df_syn, 'models/synergy_matrix.joblib')
                    joblib.dump(df_eng, 'models/historical_features.joblib')
                    
                    st.success("Deep Learning Pipeline refreshed successfully!")
                    load_trained_pipeline.clear() 
                    st.rerun()
                except Exception as e:
                    st.error(f"Warehouse Optimization Failed: {e}")

# ==========================================
# 6. MAIN ANALYTICAL CANVAS
# ==========================================
if not run_optimization:
    st.markdown("""
        <div class='dashboard-card'>
            <span class='badge-lock'>WARRIORZ DEEP LEARNING ENGINE ONLINE</span>
            <h1 style='margin-top:15px; margin-bottom:5px;'>Matchday Strategy Console</h1>
            <p style='color:#a1a1aa; font-size:1.1rem;'>Strategic selection utilizing PyTorch neural projections and SciPy mathematical constraints. Involvements from fielding are restricted purely to tight tie-breaker scenarios.</p>
        </div>
    """, unsafe_allow_html=True)
    if needs_training:
        st.info("💡 Model repository empty. Run the synchronization tool in the management tab to train the PyTorch Network.")
else:
    # --- NEW SAFETY CHECK ADDED HERE ---
    if needs_training or df_engineered is None:
        st.error("🚨 Missing AI Models: The Deep Learning engine hasn't been trained yet. Please open **⚙️ Core Database Tools** in the sidebar and click **'Synchronize & Retrain Pipeline'** first.")
    elif len(active_sign_ups) < 11:
        st.error("⚠️ Roster Depth Error: 11 active entries required to generate starting configurations.")
    else:
        # Run PyTorch Inference for the Matchday Roster
        inference_df = df_engineered.drop_duplicates(subset=['PLAYER_NAME'], keep='last').copy()
        X_infer = torch.FloatTensor(inference_df[training_features].fillna(0).values)
        
        with torch.no_grad():
            preds = pytorch_model(X_infer).numpy()
            
        inference_df['AI_Projected_Runs'] = np.maximum(0, preds[:, 0])
        inference_df['AI_Projected_Wickets'] = np.maximum(0, preds[:, 1])
        inference_df['AI_Projected_Points'] = np.maximum(0, preds[:, 2])

        # Pass projections to SciPy
        optimal_lineup_df = scipy_optimize_lineup(inference_df, active_sign_ups)
        
        if not optimal_lineup_df.empty:
            total_pts = round(optimal_lineup_df['AI_Projected_Points'].sum(), 1)
            total_runs = round(optimal_lineup_df['AI_Projected_Runs'].sum(), 0)
            total_wkts = round(optimal_lineup_df['AI_Projected_Wickets'].sum(), 1)
            
            st.markdown("<h2>⚡ Optimal Strategy Specifications</h2>", unsafe_allow_html=True)
            
            # Override callouts
            if "Uday Chaudhary" in active_sign_ups or "Garv Chaudhary" in active_sign_ups:
                locks = [f"<b>{p}</b>" for p in ["Uday Chaudhary", "Garv Chaudhary"] if p in active_sign_ups]
                st.markdown(f"<div class='badge-lock' style='margin-bottom:20px;'>👑 Leadership Lock Engaged: {', '.join(locks)} successfully secured in the primary XI sheet.</div>", unsafe_allow_html=True)
                
            # Summary KPI Displays
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1: st.metric("Team Projected Points", f"{total_pts}")
            with kpi2: st.metric("Expected Total Runs", f"{int(total_runs)}")
            with kpi3: st.metric("Expected Bowling Wickets", f"{total_wkts}")
            
            st.divider()
            
            # Horizontal Split Panel Layout
            col_grid, col_charts = st.columns([1.2, 1])
            
            with col_grid:
                st.markdown("### 🏆 Structured Starting 11 Lineup")
                ui_df = optimal_lineup_df.rename(columns={
                    "Optimal_Batting_Order": "Pos",
                    "PLAYER_NAME": "Player Name",
                    "AI_Projected_Points": "Projected Points",
                    "AI_Projected_Runs": "Proj Runs",
                    "AI_Projected_Wickets": "Proj Wickets"
                })
                
                st.dataframe(
                    ui_df[['Pos', 'Player Name', 'Projected Points', 'Proj Runs', 'Proj Wickets']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Pos": st.column_config.NumberColumn("Pos", format="%d"),
                        "Projected Points": st.column_config.NumberColumn("Points Forecast", format="%.1f"),
                        "Proj Runs": st.column_config.ProgressColumn("Runs Forecast", format="%.0f", min_value=0, max_value=55),
                        "Proj Wickets": st.column_config.NumberColumn("Wickets Forecast", format="%.1f")
                    }
                )
                
                # --- GRAPHIC 1: Player Role Matrix ---
                st.markdown("### 🎯 Player Role Matrix")
                st.caption("Identify All-Rounders vs Specialists")
                fig_scatter = px.scatter(
                    optimal_lineup_df,
                    x="AI_Projected_Runs",
                    y="AI_Projected_Wickets",
                    text="PLAYER_NAME",
                    size="AI_Projected_Points",
                    color="AI_Projected_Points",
                    color_continuous_scale=["#1c1c24", "#d4af37"],
                    labels={
                        "AI_Projected_Runs": "Expected Runs",
                        "AI_Projected_Wickets": "Expected Wickets"
                    },
                    template="plotly_dark"
                )
                
                fig_scatter.update_traces(
                    textposition='top center', 
                    textfont=dict(color='#a1a1aa', size=11),
                    marker=dict(line=dict(width=1, color='White'))
                )
                
                fig_scatter.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    margin=dict(l=0, r=0, t=20, b=20),
                    coloraxis_showscale=False 
                )
                st.plotly_chart(fig_scatter, use_container_width=True)

                # --- GRAPHIC 2: Fantasy Point Contribution ---
                st.markdown("### 💎 Fantasy Points Share")
                fig_donut = px.pie(
                    optimal_lineup_df,
                    values="AI_Projected_Points",
                    names="PLAYER_NAME",
                    hole=0.6,
                    color_discrete_sequence=px.colors.sequential.YlOrBr[::-1], 
                    template="plotly_dark"
                )
                
                fig_donut.update_traces(
                    textposition='inside', 
                    textinfo='percent+label',
                    insidetextorientation='radial',
                    marker=dict(line=dict(color='#0b0b0d', width=2))
                )
                
                fig_donut.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    height=350,
                    margin=dict(l=0, r=0, t=20, b=20)
                )
                st.plotly_chart(fig_donut, use_container_width=True)
                
            with col_charts:
                st.markdown("### 📊 Projected Production Mapping")
                
                # Interactive Production Spread Graphic
                fig_prod = px.bar(
                    optimal_lineup_df,
                    x="PLAYER_NAME",
                    y="AI_Projected_Runs",
                    color="AI_Projected_Wickets",
                    labels={"PLAYER_NAME": "Player", "AI_Projected_Runs": "Projected Runs", "AI_Projected_Wickets": "Wickets"},
                    color_continuous_scale=["#1c1c24", "#d4af37"],
                    template="plotly_dark"
                )
                fig_prod.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_title=None,
                    coloraxis_colorbar=dict(title="Wickets")
                )
                st.plotly_chart(fig_prod, use_container_width=True)
                
                # Run Distribution mapped directly to Batting Order
                st.markdown("### 🏏 Projected Run Distribution by Slot")
                fig_slots = px.bar(
                    optimal_lineup_df,
                    x='Optimal_Batting_Order',
                    y='AI_Projected_Runs',
                    text='PLAYER_NAME',
                    labels={
                        'Optimal_Batting_Order': 'Batting Position',
                        'AI_Projected_Runs': 'Expected Runs'
                    },
                    color='AI_Projected_Runs',
                    color_continuous_scale=['#121216', '#d4af37'],
                    template="plotly_dark"
                )
                fig_slots.update_traces(textposition='inside', textfont=dict(color='white', size=11))
                fig_slots.update_layout(
                    xaxis=dict(tickmode='linear', dtick=1),
                    plot_bgcolor='rgba(0,0,0,0)', 
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_slots, use_container_width=True)
                
                # Synergy Component Feed
                if not df_synergy.empty:
                    selected_names = optimal_lineup_df['PLAYER_NAME'].tolist()
                    active_synergy = df_synergy[
                        (df_synergy['Player_A'].isin(selected_names)) & 
                        (df_synergy['Player_B'].isin(selected_names))
                    ].nlargest(2, 'avg_score_together')
                    
                    if not active_synergy.empty:
                        st.markdown("### 🤝 Strategic Partnership Links")
                        for _, row in active_synergy.iterrows():
                            st.markdown(f"""
                                <div class='dashboard-card' style='padding: 15px; margin-bottom:10px;'>
                                    <span style='color:#d4af37; font-weight:bold;'>🔥 DUO COHESION:</span> 
                                    <b>{row['Player_A']}</b> & <b>{row['Player_B']}</b> 
                                    <span style='float:right; color:#00ff00; font-weight:bold;'>{row['avg_score_together']:.1f} Team Pts</span>
                                </div>
                            """, unsafe_allow_html=True)