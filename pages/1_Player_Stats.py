import streamlit as st
import pandas as pd
import plotly.express as px
import platform
import os
import re

# --- WINDOWS BUG FIX ---
platform.libc_ver = lambda *args, **kwargs: ("", "")

# --- FIXED ABSOLUTE PATH TO LOGO ---
current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = "assets/CWCCNEWLOGO.jpeg"

# --- PAGE SETUP & GOLD/BLACK THEME ---
st.set_page_config(page_title="Warriorz Player Stats", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        .stApp { background-color: #0e0e10; color: #ffffff; }
        div[data-testid="stMetricValue"] { color: #d4af37; font-size: 2.5rem; font-weight: bold; }
        div[data-testid="stMetricLabel"] { color: #cccccc; font-size: 1.1rem; }
        .stSelectbox label, .stMultiSelect label, .stRadio label { color: #d4af37 !important; font-weight: bold; }
        hr { border-top: 1px solid #d4af37 !important; }
        
        .rushmore-card { border: 1px solid #d4af37; border-radius: 8px; padding: 15px; text-align: center; background-color: #1a1a1d; margin-bottom: 20px;}
        .rushmore-name { font-size: 1.5rem; font-weight: bold; color: #ffffff; }
        .rushmore-stat { font-size: 2rem; font-weight: bold; color: #d4af37; }
        
        .badge-tag { padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; display: inline-block; margin-bottom: 12px; color: #000000; }
        .trophy-season { border: 2px solid #a1a1a6; border-radius: 8px; padding: 20px; background-color: #1c1c1e; margin-bottom: 20px; text-align: center; box-shadow: 0 0 10px rgba(161, 161, 166, 0.2); }
        .badge-season { background-color: #a1a1a6; }
        .trophy-playoff { border: 2px solid #00ffff; border-radius: 8px; padding: 20px; background-color: #0c1a24; margin-bottom: 20px; text-align: center; box-shadow: 0 0 20px rgba(0, 255, 255, 0.5); }
        .badge-playoff { background-color: #00ffff; }
        .trophy-league { border: 3px solid #d4af37; border-radius: 8px; padding: 20px; background-color: #241e0c; margin-bottom: 20px; text-align: center; box-shadow: 0 0 35px rgba(212, 175, 55, 0.85); transform: scale(1.03); transition: 0.3s; }
        .badge-league { background-color: #d4af37; }
        
        .trophy-icon { font-size: 2.5rem; margin-bottom: 5px; }
        .trophy-title { color: #ffffff; margin-bottom: 5px; font-size: 1.2rem; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; }
        .trophy-winner { color: #ffffff; margin-top: 0px; font-size: 1.8rem; font-weight: bold; }
        .trophy-divider { border-top: 1px solid #333; margin: 12px 0; }
        .trophy-stats { color: #cccccc; font-size: 1rem; margin-bottom: 5px; }
        .trophy-occasion { color: #888888; font-size: 0.9rem; margin-bottom: 0px; font-style: italic; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("snowflake")
    
    query_matches = """
        SELECT 
            dp.PLAYER_NAME,
            dp.IS_ACTIVE,
            ffp.Season AS SEASON,
            ffp.Match_Type AS MATCH_TYPE,
            ffp.Match_Result AS MATCH_RESULT,
            ffp.Opponent AS OPPONENT_TEAM,
            ffp.File_Name AS MATCH_LOG_ID,
            COALESCE(fb.Runs, 0) AS BATTING_RUNS,
            COALESCE(fb.Balls, 0) AS BALLS_FACED,
            COALESCE(fb.Fours, 0) AS FOURS,
            COALESCE(fb.Sixers, 0) AS SIXES,
            CASE WHEN fb.BatsMan IS NOT NULL AND LOWER(fb."How Out") NOT IN ('not out', 'dnb', 'did not bat', 'rt', 'retired', '*', 'nan', '') THEN 1 ELSE 0 END AS DISMISSALS,
            CASE WHEN fb.BatsMan IS NOT NULL AND LOWER(fb."How Out") NOT IN ('dnb', 'did not bat') THEN 1 ELSE 0 END AS BATTED_INNING,
            COALESCE(fb.Batting_Position, 'N/A') AS BATTING_POSITION,
            COALESCE(fbo.Wickets, 0) AS WICKETS,
            COALESCE(fbo.Runs, 0) AS RUNS_CONCEDED,
            COALESCE(FLOOR(fbo.Overs) * 6 + ROUND((fbo.Overs - FLOOR(fbo.Overs)) * 10), 0) AS BALLS_BOWLED,
            CASE WHEN fbo.Bowler IS NOT NULL AND COALESCE(fbo.Overs, 0) > 0 THEN 1 ELSE 0 END AS BOWLED_INNING,
            COALESCE(fbo."Dot Balls", 0) AS DOT_BALLS,
            COALESCE(fma.Catches, 0) AS CATCHES,
            COALESCE(fma.Wk_Catches, 0) AS WK_CATCHES,
            COALESCE(fma.Stumpings, 0) AS STUMPINGS,
            COALESCE(fma.Run_Outs, 0) AS RUN_OUTS,
            CASE WHEN motm.Player_Name IS NOT NULL THEN 1 ELSE 0 END AS MOTM_AWARDS,
            ffp.Total_Pts AS FANTASY_PTS
        FROM 
            DIM_PLAYER dp
        JOIN 
            FACT_FANTASY_POINTS ffp ON dp.PLAYER_NAME = ffp.Player_Name
        LEFT JOIN 
            FACT_BATTING fb ON dp.PLAYER_NAME = fb.BatsMan AND ffp.File_Name = fb.File_Name
        LEFT JOIN 
            FACT_BOWLING fbo ON dp.PLAYER_NAME = fbo.Bowler AND ffp.File_Name = fbo.File_Name
        LEFT JOIN 
            DIM_MOTM motm ON dp.PLAYER_NAME = motm.Player_Name AND ffp.File_Name = motm.File_Name
        LEFT JOIN 
            (
                SELECT 
                    dp2.PLAYER_NAME,
                    ff.File_Name,
                    SUM(CASE WHEN (LOWER(ff."How Out") LIKE '%ct%' OR LOWER(ff."How Out") LIKE '%c%') AND LOWER(ff."How Out") NOT LIKE '%ctw%' THEN 1 ELSE 0 END) AS Catches,
                    SUM(CASE WHEN LOWER(ff."How Out") LIKE '%ctw%' THEN 1 ELSE 0 END) AS Wk_Catches,
                    SUM(CASE WHEN LOWER(ff."How Out") LIKE '%st%' THEN 1 ELSE 0 END) AS Stumpings,
                    SUM(CASE WHEN LOWER(ff."How Out") LIKE '%ro%' OR LOWER(ff."How Out") LIKE '%run%' THEN 1 ELSE 0 END) AS Run_Outs
                FROM FACT_FIELDING ff
                JOIN DIM_PLAYER dp2 ON ff.Fielder = dp2.FIELDING_ALIAS
                GROUP BY dp2.PLAYER_NAME, ff.File_Name
            ) fma ON dp.PLAYER_NAME = fma.PLAYER_NAME AND ffp.File_Name = fma.File_Name;
    """
    
    query_view = "SELECT * FROM VW_ULTIMATE_PLAYER_DASHBOARD;"
    query_awards = "SELECT * FROM DIM_LEAGUE_AWARDS;"
    
    try:
        df_matches = conn.query(query_matches)
        df_view = conn.query(query_view)
        df_awards = conn.query(query_awards)
        df_view = df_view.fillna(0)
        return df_matches, df_view, df_awards
    except Exception as e:
        st.error(f"SQL Compilation Error:\n\n{e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Load dataframes
df_matches, df_view, df_awards = load_data()

if not df_matches.empty and not df_view.empty:
    
    # Pre-declare globally to ensure structural scope validation safety
    filtered_matches = df_matches.copy()
    
    # --- APP NAVIGATION ---
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width='stretch')
    
    app_mode = st.sidebar.radio(
        "Navigation Menu", 
        ["🏔️ Hall of Fame", "🏆 Trophy Cabinet", "🏏 Batting Stats", "🎯 Bowling Stats", "🦅 Fielding Stats", "📈 Winning Impact", "⚡ Individual Profile"]
    )
    st.sidebar.divider()
    
    # --- GLOBAL LEADERBOARD FILTERS ---
    if app_mode in ["🏔️ Hall of Fame", "🏏 Batting Stats", "🎯 Bowling Stats", "🦅 Fielding Stats", "📈 Winning Impact"]:
        st.sidebar.header("🏆 Global Filters")
        
        # NEW ERA FILTER
        era_filter = st.sidebar.selectbox(
            "Franchise Era", 
            ["All Eras", "Cypress Warriors (2023-2024)", "Cypress Warriorz (2025 & Beyond)"]
        )
        
        roster_status = st.sidebar.radio("Roster Status", ["All Players", "Active Only", "Inactive Only"])
        team_match_type = st.sidebar.selectbox("Match Format", ["Career (All)", "Regular Season", "Playoff", "Practice"])
        season_filter = st.sidebar.selectbox("Season", ["All Seasons"] + sorted(df_matches['SEASON'].dropna().unique().tolist(), reverse=True))
        opp_filter = st.sidebar.selectbox("Vs Opponent", ["All Opponents"] + sorted(df_matches['OPPONENT_TEAM'].dropna().unique().tolist()))
        
        if app_mode == "🏏 Batting Stats":
            raw_positions = sorted([p for p in df_matches['BATTING_POSITION'].unique() if p != 0 and p != 'N/A'])
            selected_position = st.sidebar.selectbox("Filter by Position", ["All Positions"] + raw_positions)
        
        # Apply Era Filter Logic
        filtered_matches['SEASON_YEAR'] = filtered_matches['SEASON'].apply(lambda x: int(re.search(r'\d{4}', str(x)).group()) if re.search(r'\d{4}', str(x)) else 0)
        if era_filter == "Cypress Warriors (2023-2024)":
            filtered_matches = filtered_matches[(filtered_matches['SEASON_YEAR'] >= 2023) & (filtered_matches['SEASON_YEAR'] <= 2024)]
        elif era_filter == "Cypress Warriorz (2025 & Beyond)":
            filtered_matches = filtered_matches[filtered_matches['SEASON_YEAR'] >= 2025]

        # Apply Base Filters
        if roster_status == "Active Only":
            filtered_matches = filtered_matches[filtered_matches['IS_ACTIVE'] == True]
        elif roster_status == "Inactive Only":
            filtered_matches = filtered_matches[filtered_matches['IS_ACTIVE'] == False]
            
        if team_match_type == "Career (All)":
            filtered_matches = filtered_matches[filtered_matches['MATCH_TYPE'].isin(['Regular Season', 'Playoff'])]
        else:
            filtered_matches = filtered_matches[filtered_matches['MATCH_TYPE'] == team_match_type]
            
        if season_filter != "All Seasons":
            filtered_matches = filtered_matches[filtered_matches['SEASON'] == season_filter]
        if opp_filter != "All Opponents":
            filtered_matches = filtered_matches[filtered_matches['OPPONENT_TEAM'] == opp_filter]
            
        if app_mode == "🏏 Batting Stats" and selected_position != "All Positions":
            filtered_matches = filtered_matches[filtered_matches['BATTING_POSITION'] == selected_position]

    # --- ADVANCED METRICS FILTERS ---
    if app_mode != "🏆 Trophy Cabinet":
        st.sidebar.markdown("### 📊 Advanced Metrics")

        # 1. HOF ONLY Aggregation Toggle
        if app_mode == "🏔️ Hall of Fame":
            agg_method = st.sidebar.radio(
                "Calculation Method", 
                ["Total (Sum)", "Per Game / Dismissal (Average)"],
                help="Toggle between total stats or average stats per match/dismissal."
            )
            math_func = 'mean' if agg_method == "Per Game / Dismissal (Average)" else 'sum'
            metric_label = "Avg" if math_func == 'mean' else "Total"
        else:
            agg_method = "Total (Sum)"
            math_func = 'sum'
            metric_label = "Total"

        # 2. Max Games Dynamic Bounds
        max_historical_games = int(df_matches.groupby('PLAYER_NAME')['MATCH_LOG_ID'].nunique().max())
        if max_historical_games < 1: max_historical_games = 1
        
        min_games = st.sidebar.slider(
            "Minimum Games Played", 
            min_value=1, 
            max_value=max_historical_games, 
            value=1, 
            step=1,
            help="Filter out players with small sample sizes."
        )

        # Apply Dynamic Slider bounds
        if app_mode in ["🏔️ Hall of Fame", "🏏 Batting Stats", "🎯 Bowling Stats", "🦅 Fielding Stats", "📈 Winning Impact"]:
            if not filtered_matches.empty:
                games_played = filtered_matches.groupby('PLAYER_NAME')['MATCH_LOG_ID'].nunique()
                valid_players = games_played[games_played >= min_games].index
                filtered_matches = filtered_matches[filtered_matches['PLAYER_NAME'].isin(valid_players)]

                if filtered_matches.empty:
                    st.warning("No players meet the current filter criteria. Try lowering the Minimum Games Played.")

    # ==========================================
    # MODE 1: HALL OF FAME (Mount Rushmore & Top 5s)
    # ==========================================
    if app_mode == "🏔️ Hall of Fame":
        col_logo, col_title = st.columns([1, 7])
        with col_logo:
            if os.path.exists(logo_path):
                st.image(logo_path, width='stretch')
        with col_title:
            st.markdown(f"""
                <div style="padding-top: 30px;">
                    <h1 style="font-size: 3.5rem; margin-bottom: 0px;">Cypress Warriorz | Hall of Fame</h1>
                    <h3 style="color: #cccccc; margin-top: 0px;">🏔️ Mount Rushmore & Top 5 Leaders</h3>
                </div>
            """, unsafe_allow_html=True)
        st.divider()

        team_leaderboard = filtered_matches.groupby('PLAYER_NAME').agg(
            TOTAL_PTS=('FANTASY_PTS', 'sum'), RUNS=('BATTING_RUNS', 'sum'),
            DISMISSALS=('DISMISSALS', 'sum'), BATTED_INNINGS=('BATTED_INNING', 'sum'),
            WICKETS=('WICKETS', 'sum'), RUNS_CONCEDED=('RUNS_CONCEDED', 'sum'),
            BALLS_BOWLED=('BALLS_BOWLED', 'sum'), BOWLED_INNINGS=('BOWLED_INNING', 'sum'),
            CATCHES=('CATCHES', 'sum'), RUN_OUTS=('RUN_OUTS', 'sum'),
            WK_CATCHES=('WK_CATCHES', 'sum'), STUMPINGS=('STUMPINGS', 'sum'),
            MOTM_AWARDS=('MOTM_AWARDS', 'sum'), GAMES_PLAYED=('MATCH_LOG_ID', 'nunique')
        ).reset_index()
        
        team_leaderboard['BATTING_AVERAGE'] = team_leaderboard.apply(lambda r: r['RUNS']/r['DISMISSALS'] if r['DISMISSALS'] > 0 else float(r['RUNS']), axis=1)
        team_leaderboard['ECONOMY_RATE'] = team_leaderboard.apply(lambda r: r['RUNS_CONCEDED']/(r['BALLS_BOWLED']/6) if r['BALLS_BOWLED'] > 0 else 0.0, axis=1)
        team_leaderboard['WK_TOTAL_DISMISSALS'] = team_leaderboard['WK_CATCHES'] + team_leaderboard['STUMPINGS']

        # Manual math decoupling with True Batting Average updates
        if math_func == 'mean':
            # FILTER STEP: Drop players with infinite averages (0 dismissals but runs scored)
            team_leaderboard = team_leaderboard[team_leaderboard['DISMISSALS'] > 0]
            
            team_leaderboard['TOTAL_PTS'] = team_leaderboard['TOTAL_PTS'] / team_leaderboard['GAMES_PLAYED']
            
            # True traditional batting average logic (Runs divided by Times Out)
            team_leaderboard['RUNS'] = team_leaderboard['RUNS'] / team_leaderboard['DISMISSALS']
            
            # Bowling wickets per inning
            team_leaderboard['WICKETS'] = team_leaderboard.apply(lambda r: r['WICKETS']/r['BOWLED_INNINGS'] if r['BOWLED_INNINGS'] > 0 else 0.0, axis=1)
            
            # Fielding variables remain aggregated per game appearances
            team_leaderboard['CATCHES'] = team_leaderboard['CATCHES'] / team_leaderboard['GAMES_PLAYED']
            team_leaderboard['WK_TOTAL_DISMISSALS'] = team_leaderboard['WK_TOTAL_DISMISSALS'] / team_leaderboard['GAMES_PLAYED']
            team_leaderboard['MOTM_AWARDS'] = team_leaderboard['MOTM_AWARDS'] / team_leaderboard['GAMES_PLAYED']
            team_leaderboard['RUN_OUTS'] = team_leaderboard['RUN_OUTS'] / team_leaderboard['GAMES_PLAYED']
            
            team_leaderboard = team_leaderboard.round(1)

        if math_func == 'mean':
            st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🏔️ Mount Rushmore ({metric_label} Fantasy Pts / Game)</h2>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h2 style='text-align: center; color: #d4af37;'>🏔️ Mount Rushmore ({metric_label} Fantasy Pts)</h2>", unsafe_allow_html=True)
            
        st.write("")
        
        top_overall = team_leaderboard.nlargest(4, 'TOTAL_PTS')
        rush_cols = st.columns(4)
        for i, (index, row) in enumerate(top_overall.iterrows()):
            pts_display = f"{row['TOTAL_PTS']:.1f}" if math_func == 'mean' else f"{int(row['TOTAL_PTS'])}"
            
            with rush_cols[i]:
                st.markdown(f"""
                <div class="rushmore-card">
                    <div style="font-size: 2rem;">👑</div>
                    <div class="rushmore-name">{row['PLAYER_NAME']}</div>
                    <div class="rushmore-stat">{pts_display} Pts</div>
                </div>
                """, unsafe_allow_html=True)
        st.divider()

        def create_top_5_row(dataframe, sort_col, display_mode):
            top_5 = dataframe.nlargest(5, sort_col)
            top_5 = top_5[top_5[sort_col] > 0]
            if top_5.empty:
                st.info(f"No active statistical records found for this filter combination.")
                return
            cols = st.columns(5)
            for i, (index, row) in enumerate(top_5.iterrows()):
                if display_mode == "batting": delta_str = f"Avg: {row['BATTING_AVERAGE']:.2f} | Inn: {int(row['BATTED_INNINGS'])}"
                elif display_mode == "bowling": delta_str = f"Econ: {row['ECONOMY_RATE']:.2f} | Inn: {int(row['BOWLED_INNINGS'])}"
                elif display_mode == "fielding": delta_str = f"Run Outs: {row['RUN_OUTS']:.1f}" if math_func=='mean' else f"Run Outs: {int(row['RUN_OUTS'])}"
                elif display_mode == "wk": delta_str = f"Stumpings: {row['STUMPINGS']:.1f}" if math_func=='mean' else f"Stumpings: {int(row['STUMPINGS'])}"
                elif display_mode == "motm": delta_str = f"Games: {int(row['GAMES_PLAYED'])}"
                else: delta_str = None
                
                with cols[i]:
                    rank_emoji = "🥇" if i == 0 else f"#{i+1}"
                    val_display = f"{row[sort_col]:.1f}" if math_func == 'mean' else f"{int(row[sort_col])}"
                    st.metric(label=f"{rank_emoji} {row['PLAYER_NAME']}", value=val_display, delta=delta_str, delta_color="off")

        st.subheader(f"🏏 Top 5 Batsmen (" + ("Average Runs / Dismissal)" if math_func=='mean' else "Total Runs)"))
        create_top_5_row(team_leaderboard, sort_col='RUNS', display_mode="batting")
        st.write("")
        st.subheader(f"🎯 Top 5 Bowlers (" + ("Average Wickets / Innings)" if math_func=='mean' else "Total Wickets)"))
        create_top_5_row(team_leaderboard, sort_col='WICKETS', display_mode="bowling")
        st.write("")
        st.subheader(f"🦅 Top 5 Fielders (" + ("Average Catches / Game)" if math_func=='mean' else "Total Catches)"))
        create_top_5_row(team_leaderboard, sort_col='CATCHES', display_mode="fielding")
        st.write("")
        st.subheader(f"🧤 Top 5 Wicket Keepers (" + ("Average Dismissals / Game)" if math_func=='mean' else "Total Dismissals)"))
        wk_filtered = team_leaderboard[team_leaderboard['WK_TOTAL_DISMISSALS'] > 0]
        create_top_5_row(wk_filtered, sort_col='WK_TOTAL_DISMISSALS', display_mode="wk")
        st.write("")
        st.subheader(f"🏅 Top 5 Match Winners (" + ("Average MOTM Awards / Game)" if math_func=='mean' else "Total MOTM Awards)"))
        create_top_5_row(team_leaderboard, sort_col='MOTM_AWARDS', display_mode="motm")

    # ==========================================
    # MODE 2: THE TROPHY CABINET
    # ==========================================
    elif app_mode == "🏆 Trophy Cabinet":
        col_logo, col_title = st.columns([1, 7])
        with col_logo:
            if os.path.exists(logo_path):
                st.image(logo_path, width='stretch')
        with col_title:
            st.markdown(f"""
                <div style="padding-top: 30px;">
                    <h1 style="font-size: 3.5rem; margin-bottom: 0px;">Cypress Warriorz | Trophy Cabinet</h1>
                    <h3 style="color: #cccccc; margin-top: 0px;">🏆 Celebrating Franchise Tournament Accolades</h3>
                </div>
            """, unsafe_allow_html=True)
        st.divider()

        if not df_awards.empty:
            seasons = sorted(df_awards['SEASON'].unique(), reverse=True)
            for season in seasons:
                st.markdown(f"<h3 style='color: #d4af37; border-bottom: 1px solid #333; padding-bottom: 10px;'>{season} Season</h3>", unsafe_allow_html=True)
                st.write("")
                
                season_awards = df_awards[df_awards['SEASON'] == season]
                cols = st.columns(3)
                
                for i, row in season_awards.reset_index().iterrows():
                    award_name = str(row['AWARD_TYPE']).lower()
                    occasion_name = str(row['OCCASION']).lower()
                    
                    if any(kw in award_name for kw in ["mvp", "league", "tournament", "best"]):
                        card_style = "trophy-league"
                        badge_style = "badge-league"
                        badge_text = "★ LEAGUE ELITE"
                        icon = "👑"
                    elif "playoff" in award_name or "final" in award_name or "playoff" in occasion_name or "final" in occasion_name:
                        card_style = "trophy-playoff"
                        badge_style = "badge-playoff"
                        badge_text = "⚡ PLAYOFF CLUTCH"
                        icon = "🔥"
                    else:
                        card_style = "trophy-season"
                        badge_style = "badge-season"
                        badge_text = "📋 SEASON AWARD"
                        icon = "🏆"
                        
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div class="{card_style}">
                            <div class="badge-tag {badge_style}">{badge_text}</div>
                            <div class="trophy-icon">{icon}</div>
                            <div class="trophy-title">{row['AWARD_TYPE']}</div>
                            <div class="trophy-winner">{row['PLAYER_NAME']}</div>
                            <div class="trophy-divider"></div>
                            <div class="trophy-stats"><b>Performance:</b> {row['STATS']}</div>
                            <div class="trophy-occasion">{row['OCCASION']} vs {row['OPPONENT']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                st.write("")
                st.write("")
        else:
            st.info("No league awards have been recorded in the database yet.")

    # ==========================================
    # MODE 3: BATTING STATS
    # ==========================================
    elif app_mode == "🏏 Batting Stats":
        col_logo, col_title = st.columns([1, 7])
        with col_logo:
            if os.path.exists(logo_path):
                st.image(logo_path, width='stretch')
        with col_title:
            st.markdown(f"""
                <div style="padding-top: 30px;">
                    <h1 style="font-size: 3.5rem; margin-bottom: 0px;">Cypress Warriorz | Batting Center</h1>
                    <h3 style="color: #cccccc; margin-top: 0px;">🏏 Run Scoring, Milestones & Strike Rates ({selected_position if selected_position != "All Positions" else "Squad Overall"})</h3>
                </div>
            """, unsafe_allow_html=True)
        st.divider()

        bat_df = filtered_matches.groupby('PLAYER_NAME').agg(
            Innings=('BATTED_INNING', 'sum'),
            Runs=('BATTING_RUNS', 'sum'),
            Dismissals=('DISMISSALS', 'sum'),
            Balls=('BALLS_FACED', 'sum'),
            Fours=('FOURS', 'sum'),
            Sixes=('SIXES', 'sum'),
            Thirties=('BATTING_RUNS', lambda x: ((x >= 30) & (x < 50)).sum()),
            Fifties=('BATTING_RUNS', lambda x: ((x >= 50) & (x < 100)).sum()),
            Hundreds=('BATTING_RUNS', lambda x: (x >= 100).sum())
        ).reset_index()
        
        bat_df['Average'] = bat_df.apply(lambda r: r['Runs']/r['Dismissals'] if r['Dismissals'] > 0 else float(r['Runs']), axis=1)
        bat_df['Strike Rate'] = bat_df.apply(lambda r: (r['Runs']/r['Balls'] * 100) if r['Balls'] > 0 else 0.0, axis=1)
        
        bat_df = bat_df[['PLAYER_NAME', 'Innings', 'Runs', 'Average', 'Strike Rate', 'Sixes', 'Fours', 'Thirties', 'Fifties', 'Hundreds']]
        bat_df = bat_df[bat_df['Innings'] > 0]

        st.dataframe(
            bat_df.sort_values(by='Runs', ascending=False),
            column_config={
                "PLAYER_NAME": "Player Name",
                "Innings": "Innings Batted",
                "Runs": st.column_config.NumberColumn("Total Runs", format="%d 🏏"),
                "Strike Rate": st.column_config.ProgressColumn("Strike Rate", min_value=0, max_value=250, format="%.2f"),
                "Average": st.column_config.NumberColumn("Average", format="%.2f"),
                "Sixes": st.column_config.NumberColumn("Total 6s", format="%d 🚀"),
                "Fours": st.column_config.NumberColumn("Total 4s", format="%d 💥"),
                "Thirties": "Total 30s", "Fifties": "Total 50s", "Hundreds": "Total 100s"
            },
            hide_index=True,
            width='stretch'
        )

    # ==========================================
    # MODE 4: BOWLING STATS
    # ==========================================
    elif app_mode == "🎯 Bowling Stats":
        col_logo, col_title = st.columns([1, 7])
        with col_logo:
            if os.path.exists(logo_path):
                st.image(logo_path, width='stretch')
        with col_title:
            st.markdown(f"""
                <div style="padding-top: 30px;">
                    <h1 style="font-size: 3.5rem; margin-bottom: 0px;">Cypress Warriorz | Bowling Center</h1>
                    <h3 style="color: #cccccc; margin-top: 0px;">🎯 Wickets, Economies & Dot Balls</h3>
                </div>
            """, unsafe_allow_html=True)
        st.divider()

        bowl_df = filtered_matches.groupby('PLAYER_NAME').agg(
            Innings=('BOWLED_INNING', 'sum'),
            Total_Balls=('BALLS_BOWLED', 'sum'),
            Wickets=('WICKETS', 'sum'),
            Runs_Conceded=('RUNS_CONCEDED', 'sum'),
            Dot_Balls=('DOT_BALLS', 'sum')
        ).reset_index()
        
        bowl_df['Overs'] = bowl_df.apply(lambda r: (r['Total_Balls'] // 6) + (r['Total_Balls'] % 6)/10, axis=1)
        bowl_df['Average'] = bowl_df.apply(lambda r: r['Runs_Conceded']/r['Wickets'] if r['Wickets'] > 0 else 0.0, axis=1)
        bowl_df['Economy'] = bowl_df.apply(lambda r: r['Runs_Conceded']/(r['Total_Balls']/6) if r['Total_Balls'] > 0 else 0.0, axis=1)
        
        bowl_df = bowl_df[bowl_df['Innings'] > 0]
        bowl_df = bowl_df[['PLAYER_NAME', 'Innings', 'Overs', 'Dot_Balls', 'Wickets', 'Average', 'Economy']]

        st.dataframe(
            bowl_df.sort_values(by='Wickets', ascending=False),
            column_config={
                "PLAYER_NAME": "Player Name",
                "Innings": "Innings Bowled",
                "Overs": "Total Overs",
                "Wickets": st.column_config.NumberColumn("Total Wickets", format="%d 🎯"),
                "Dot_Balls": st.column_config.NumberColumn("Total Dot Balls", format="%d 🛑"),
                "Economy": st.column_config.ProgressColumn("Economy Rate", min_value=0, max_value=15, format="%.2f"),
                "Average": st.column_config.NumberColumn("Average", format="%.2f")
            },
            hide_index=True,
            width='stretch'
        )

    # ==========================================
    # MODE 5: FIELDING STATS
    # ==========================================
    elif app_mode == "🦅 Fielding Stats":
        col_logo, col_title = st.columns([1, 7])
        with col_logo:
            if os.path.exists(logo_path):
                st.image(logo_path, width='stretch')
        with col_title:
            st.markdown(f"""
                <div style="padding-top: 30px;">
                    <h1 style="font-size: 3.5rem; margin-bottom: 0px;">Cypress Warriorz | Fielding Center</h1>
                    <h3 style="color: #cccccc; margin-top: 0px;">🦅 Catches, Stumpings & Run Outs</h3>
                </div>
            """, unsafe_allow_html=True)
        st.divider()

        fld_df = filtered_matches.groupby('PLAYER_NAME').agg(
            Games=('MATCH_LOG_ID', 'nunique'),
            Catches=('CATCHES', 'sum'),
            WK_Catches=('WK_CATCHES', 'sum'),
            Run_Outs=('RUN_OUTS', 'sum'),
            Stumpings=('STUMPINGS', 'sum')
        ).reset_index()
        
        fld_df = fld_df[(fld_df['Catches'] > 0) | (fld_df['WK_Catches'] > 0) | (fld_df['Run_Outs'] > 0) | (fld_df['Stumpings'] > 0)]

        st.dataframe(
            fld_df.sort_values(by='Catches', ascending=False),
            column_config={
                "PLAYER_NAME": "Player Name",
                "Games": st.column_config.NumberColumn("Games Played", format="%d 🏟️"),
                "Catches": st.column_config.NumberColumn("Total Fielder Catches", format="%d 👐"),
                "WK_Catches": "Total Keeper Catches",
                "Run_Outs": st.column_config.NumberColumn("Total Run Outs", format="%d ⚡"),
                "Stumpings": "Total Stumpings"
            },
            hide_index=True,
            width='stretch'
        )

    # ==========================================
    # MODE 6: WINNING IMPACT
    # ==========================================
    elif app_mode == "📈 Winning Impact":
        col_logo, col_title = st.columns([1, 7])
        with col_logo:
            if os.path.exists(logo_path):
                st.image(logo_path, width='stretch')
        with col_title:
            st.markdown(f"""
                <div style="padding-top: 30px;">
                    <h1 style="font-size: 3.5rem; margin-bottom: 0px;">Cypress Warriorz | Winning Impact</h1>
                    <h3 style="color: #cccccc; margin-top: 0px;">📈 Player Win-Loss Records & Win Percentages</h3>
                </div>
            """, unsafe_allow_html=True)
        st.divider()

        if 'MATCH_RESULT' not in filtered_matches.columns:
            st.error("MATCH_RESULT column not found! Please add 'ffp.Match_Result AS MATCH_RESULT' to your load_data() SQL query.")
        else:
            win_df = filtered_matches.groupby(['PLAYER_NAME', 'MATCH_RESULT'])['MATCH_LOG_ID'].nunique().unstack(fill_value=0).reset_index()
            win_df.columns = [str(c).upper() for c in win_df.columns]
            
            if 'WIN' not in win_df.columns: win_df['WIN'] = 0
            if 'LOSS' not in win_df.columns: win_df['LOSS'] = 0
            
            win_df['Matches Played'] = win_df['WIN'] + win_df['LOSS']
            win_df['Win-Loss Record'] = win_df['WIN'].astype(str) + "-" + win_df['LOSS'].astype(str)
            win_df['Winning %'] = (win_df['WIN'] / win_df['Matches Played'] * 100).fillna(0)
            
            win_df = win_df[win_df['Matches Played'] >= min_games]
            
            display_df = win_df[['PLAYER_NAME', 'Matches Played', 'Win-Loss Record', 'Winning %']].sort_values(
                by=['Winning %', 'Matches Played'], ascending=[False, False]
            )

            st.dataframe(
                display_df,
                column_config={
                    "PLAYER_NAME": "Player Name",
                    "Matches Played": st.column_config.NumberColumn("Matches Played", format="%d 🏟️"),
                    "Win-Loss Record": "Record (W-L)",
                    "Winning %": st.column_config.ProgressColumn("Winning Percentage", min_value=0, max_value=100, format="%.1f%%")
                },
                hide_index=True,
                width='stretch'
            )

    # ==========================================
    # MODE 7: INDIVIDUAL PLAYER ANALYSIS
    # ==========================================
    elif app_mode == "⚡ Individual Profile":
        st.sidebar.header("🔍 Player Filter Menu")
        
        player_list = sorted(df_matches['PLAYER_NAME'].dropna().unique().tolist())
        selected_player = st.sidebar.selectbox("Select Player", player_list)
        
        # NEW ERA FILTER FOR INDIVIDUAL MODE
        era_filter_ind = st.sidebar.selectbox(
            "Franchise Era", 
            ["All Eras", "Cypress Warriors (2023-2024)", "Cypress Warriorz (2025 & Beyond)"]
        )
        
        match_types = ["Career (All)", "Regular Season", "Playoff", "Practice"]
        selected_match_type = st.sidebar.selectbox("Match Format", match_types)
        seasons = ["All Seasons"] + sorted(df_matches['SEASON'].dropna().unique().tolist(), reverse=True)
        selected_season = st.sidebar.selectbox("Season", seasons)
        opponents = ["All Opponents"] + sorted(df_matches['OPPONENT_TEAM'].dropna().unique().tolist())
        selected_opponent = st.sidebar.selectbox("Vs Opponent", opponents)
        
        st.sidebar.divider()
        st.sidebar.subheader("Card Metrics Display")
        available_metrics = [
            "Matches Played", "Runs", "Highest Score", "Strike Rate", 
            "Batting Average", "Wickets", "Bowling Average", 
            "Economy Rate", "Catches", "Fantasy Points", "MOTM Awards"
        ]
        selected_metrics = st.sidebar.multiselect(
            "Select up to 5 stats to view dynamically:", 
            options=available_metrics, default=["Matches Played", "Runs", "Highest Score", "Wickets", "Fantasy Points"], max_selections=5
        )
        
        # Explicit .copy() to prevent SettingWithCopyWarning
        filtered_df = df_matches[df_matches['PLAYER_NAME'] == selected_player].copy()
        
        # Apply Era Filter Logic
        filtered_df['SEASON_YEAR'] = filtered_df['SEASON'].apply(lambda x: int(re.search(r'\d{4}', str(x)).group()) if re.search(r'\d{4}', str(x)) else 0)
        if era_filter_ind == "Cypress Warriors (2023-2024)":
            filtered_df = filtered_df[(filtered_df['SEASON_YEAR'] >= 2023) & (filtered_df['SEASON_YEAR'] <= 2024)]
        elif era_filter_ind == "Cypress Warriorz (2025 & Beyond)":
            filtered_df = filtered_df[filtered_df['SEASON_YEAR'] >= 2025]

        # Base Filters
        if selected_match_type == "Career (All)":
            filtered_df = filtered_df[filtered_df['MATCH_TYPE'].isin(['Regular Season', 'Playoff'])]
        else:
            filtered_df = filtered_df[filtered_df['MATCH_TYPE'] == selected_match_type]
        if selected_season != "All Seasons":
            filtered_df = filtered_df[filtered_df['SEASON'] == selected_season]
        if selected_opponent != "All Opponents":
            filtered_df = filtered_df[filtered_df['OPPONENT_TEAM'] == selected_opponent]
        
        local_games = filtered_df['MATCH_LOG_ID'].nunique()
        
        col_logo, col_title = st.columns([1, 7])
        with col_logo:
            if os.path.exists(logo_path):
                st.image(logo_path, width='stretch')
        with col_title:
            st.markdown(f"""
                <div style="padding-top: 30px;">
                    <h1 style="font-size: 3.5rem; margin-bottom: 0px;">Cypress Warriorz | Player Analysis</h1>
                    <h3 style="color: #cccccc; margin-top: 0px;">⚡ {selected_player} | Performance Profile</h3>
                </div>
            """, unsafe_allow_html=True)
        st.divider()
        
        if local_games < min_games:
            st.warning(f"This player has only played {local_games} match(es), which is fewer than the required Minimum Games Played threshold ({min_games}) set in the sidebar.")
        
        total_matches = len(filtered_df)
        metrics_computed = {}
        if total_matches > 0:
            runs = int(filtered_df['BATTING_RUNS'].sum())
            balls_faced = int(filtered_df['BALLS_FACED'].sum())
            dismissals = int(filtered_df['DISMISSALS'].sum())
            wickets = int(filtered_df['WICKETS'].sum())
            runs_conceded = int(filtered_df['RUNS_CONCEDED'].sum())
            balls_bowled = int(filtered_df['BALLS_BOWLED'].sum())
            
            metrics_computed["Matches Played"] = total_matches
            metrics_computed["Runs"] = runs
            metrics_computed["Highest Score"] = int(filtered_df['BATTING_RUNS'].max()) if pd.notna(filtered_df['BATTING_RUNS'].max()) else 0
            metrics_computed["Strike Rate"] = (runs / balls_faced * 100) if balls_faced > 0 else 0.0
            metrics_computed["Batting Average"] = (runs / dismissals) if dismissals > 0 else float(runs)
            metrics_computed["Wickets"] = wickets
            metrics_computed["Bowling Average"] = (runs_conceded / wickets) if wickets > 0 else 0.0
            metrics_computed["Economy Rate"] = (runs_conceded / (balls_bowled / 6)) if balls_bowled > 0 else 0.0
            metrics_computed["Catches"] = int(filtered_df['CATCHES'].sum())
            metrics_computed["Fantasy Points"] = int(filtered_df['FANTASY_PTS'].sum())
            metrics_computed["MOTM Awards"] = int(filtered_df['MOTM_AWARDS'].sum())
        else:
            for m in available_metrics: metrics_computed[m] = 0

        st.markdown(f"<h3 style='color: #d4af37; margin-bottom: 15px;'>📊 {selected_player} | Highlight Metrics</h3>", unsafe_allow_html=True)
        if len(selected_metrics) > 0:
            cols = st.columns(len(selected_metrics))
            for i, metric in enumerate(selected_metrics):
                val = metrics_computed[metric]
                if isinstance(val, float): cols[i].metric(metric, f"{val:.2f}")
                else: cols[i].metric(metric, val)
        st.divider()
        
        left_col, right_col = st.columns([2, 1])
        with left_col:
            st.subheader("Match-by-Match Fantasy Points")
            if total_matches > 0:
                fig = px.bar(
                    filtered_df, x="MATCH_LOG_ID", y="FANTASY_PTS", color="MATCH_TYPE",
                    color_discrete_map={"Regular Season": "#d4af37", "Playoff": "#8a6d25", "Practice": "#443410"},
                    hover_data={"OPPONENT_TEAM": True, "BATTING_RUNS": True, "WICKETS": True, "CATCHES": True},
                    template="plotly_dark", title=f"{selected_player} Points Tracker"
                )
                fig.update_xaxes(showticklabels=False, title_text="Match Timeline") 
                fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, width='stretch')
            else: st.info("No match data available.")
        
        with right_col:
            st.subheader("Filtered Match Logs")
            if total_matches > 0:
                display_cols = ['MATCH_LOG_ID', 'OPPONENT_TEAM', 'BATTING_RUNS', 'WICKETS', 'CATCHES', 'FANTASY_PTS']
                st.dataframe(filtered_df[display_cols].sort_values(by="MATCH_LOG_ID", ascending=False), hide_index=True, width='stretch')
        
        st.divider()
        st.subheader(f"🏆 {selected_player} | Complete View Table Breakdown")
        
        player_view_data = df_view[df_view['PLAYER_NAME'] == selected_player]
        if not player_view_data.empty:
            view_player_df = player_view_data.copy().drop(columns=['PLAYER_NAME'], errors='ignore').T
            view_player_df.columns = ["Aggregates"]
            
            prefix_map = {
                "Career (All)": "CAREER_",
                "Regular Season": "RS_",
                "Playoff": "PLAYOFF_",
                "Practice": "PRACTICE_"
            }
            target_prefix = prefix_map.get(selected_match_type, "CAREER_")
            
            view_player_df = view_player_df[
                view_player_df.index.str.startswith(target_prefix) | 
                view_player_df.index.isin(['IS_ACTIVE', 'ACTIVE_IN_PRACTICE_LEAGUE', 'CAREER_LEAGUE_AWARDS'])
            ]
            st.dataframe(view_player_df, width='stretch')