import joblib
import os
import streamlit as st
import platform

# --- WINDOWS ENVIRONMENT PATCH ---
platform.libc_ver = lambda *args, **kwargs: ("", "")

from ml_pipeline import engineer_all_features, calculate_pairwise_synergy, train_ai_predictor

if __name__ == "__main__":
    print("❄️ Connecting to Warehouse Layer [CYPRESS_WARRIORZ_DW]...")
    conn = st.connection("snowflake")
    
    # Unified Star Schema SQL Extraction Engine
    ml_data_query = """
        SELECT 
            dp.PLAYER_NAME,
            ffp.File_Name AS MATCH_LOG_ID,
            ffp.Season AS SEASON,
            COALESCE(fb.Runs, 0) AS RUNS_SCORED,
            COALESCE(fb.Balls, 0) AS BALLS_FACED,
            COALESCE(fb.Batting_Position, 'N/A') AS BATTING_POSITION,
            COALESCE(fbo.Wickets, 0) AS WICKETS_TAKEN,
            COALESCE(fbo.Runs, 0) AS RUNS_CONCEDED,
            COALESCE(fbo.Overs, 0) AS OVERS_BOWLED,
            COALESCE(fma.Catches, 0) AS CATCHES,
            COALESCE(fma.Stumpings, 0) AS STUMPINGS,
            COALESCE(fma.Run_Outs, 0) AS RUN_OUTS,
            ffp.Total_Pts AS FANTASY_PTS
        FROM CYPRESS_WARRIORZ_DW.RAW_DATA.DIM_PLAYER dp
        JOIN CYPRESS_WARRIORZ_DW.RAW_DATA.FACT_FANTASY_POINTS ffp ON dp.PLAYER_NAME = ffp.Player_Name
        LEFT JOIN CYPRESS_WARRIORZ_DW.RAW_DATA.FACT_BATTING fb ON dp.PLAYER_NAME = fb.BatsMan AND ffp.File_Name = fb.File_Name
        LEFT JOIN CYPRESS_WARRIORZ_DW.RAW_DATA.FACT_BOWLING fbo ON dp.PLAYER_NAME = fbo.Bowler AND ffp.File_Name = fbo.File_Name
        LEFT JOIN (
            SELECT 
                dp2.PLAYER_NAME,
                ff.File_Name,
                SUM(CASE WHEN (LOWER(ff."How Out") LIKE '%ct%' OR LOWER(ff."How Out") LIKE '%c%') AND LOWER(ff."How Out") NOT LIKE '%ctw%' THEN 1 ELSE 0 END) AS Catches,
                SUM(CASE WHEN LOWER(ff."How Out") LIKE '%st%' THEN 1 ELSE 0 END) AS Stumpings,
                SUM(CASE WHEN LOWER(ff."How Out") LIKE '%ro%' OR LOWER(ff."How Out") LIKE '%run%' THEN 1 ELSE 0 END) AS Run_Outs
            FROM CYPRESS_WARRIORZ_DW.RAW_DATA.FACT_FIELDING ff
            JOIN CYPRESS_WARRIORZ_DW.RAW_DATA.DIM_PLAYER dp2 ON ff.Fielder = dp2.FIELDING_ALIAS
            GROUP BY dp2.PLAYER_NAME, ff.File_Name
        ) fma ON dp.PLAYER_NAME = fma.PLAYER_NAME AND ffp.File_Name = fma.File_Name;
    """
    
    raw_data = conn.query(ml_data_query, ttl=0)
    
    # Run structural pipelines
    df_engineered = engineer_all_features(raw_data)
    df_synergy = calculate_pairwise_synergy(df_engineered)
    models_dict, training_features = train_ai_predictor(df_engineered)
    
    # Exporting serialized artifacts
    os.makedirs('models', exist_ok=True)
    print("💾 Archiving pipeline artifacts...")
    joblib.dump(models_dict, 'models/rf_lineup_models_dict.joblib')
    joblib.dump(training_features, 'models/training_features.joblib')
    joblib.dump(df_synergy, 'models/synergy_matrix.joblib')
    joblib.dump(df_engineered, 'models/historical_features.joblib')
    
    print("✅ Model refresh tracking complete. Assets exported successfully.")