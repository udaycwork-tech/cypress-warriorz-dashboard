import joblib
import os
import pandas as pd
from sqlalchemy import create_engine, text
import platform

platform.libc_ver = lambda *args, **kwargs: ("", "")

from ml_pipeline import engineer_all_features, calculate_pairwise_synergy, train_ai_predictor

def get_db_url():
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            for line in f:
                if line.strip().startswith("url"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return os.environ.get("NEON_DATABASE_URL")

if __name__ == "__main__":
    db_url = get_db_url()
    if not db_url:
        print("❌ Error: Connection URL not found in .streamlit/secrets.toml")
        exit(1)
        
    print("🔌 Connecting to Neon PostgreSQL Warehouse Layer...")
    engine = create_engine(db_url)
    
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
        FROM raw_data.DIM_PLAYER dp
        JOIN raw_data.FACT_FANTASY_POINTS ffp ON dp.PLAYER_NAME = ffp.Player_Name
        LEFT JOIN raw_data.FACT_BATTING fb ON dp.PLAYER_NAME = fb.BatsMan AND ffp.File_Name = fb.File_Name
        LEFT JOIN raw_data.FACT_BOWLING fbo ON dp.PLAYER_NAME = fbo.Bowler AND ffp.File_Name = fbo.File_Name
        LEFT JOIN (
            SELECT 
                dp2.PLAYER_NAME,
                ff.File_Name,
                SUM(CASE WHEN (LOWER(ff."How Out") LIKE '%ct%' OR LOWER(ff."How Out") LIKE '%c%') AND LOWER(ff."How Out") NOT LIKE '%ctw%' THEN 1 ELSE 0 END) AS Catches,
                SUM(CASE WHEN LOWER(ff."How Out") LIKE '%st%' THEN 1 ELSE 0 END) AS Stumpings,
                SUM(CASE WHEN LOWER(ff."How Out") LIKE '%ro%' OR LOWER(ff."How Out") LIKE '%run%' THEN 1 ELSE 0 END) AS Run_Outs
            FROM raw_data.FACT_FIELDING ff
            JOIN raw_data.DIM_PLAYER dp2 ON ff.Fielder = dp2.FIELDING_ALIAS
            GROUP BY dp2.PLAYER_NAME, ff.File_Name
        ) fma ON dp.PLAYER_NAME = fma.PLAYER_NAME AND ffp.File_Name = fma.File_Name;
    """
    
    with engine.connect() as conn:
        raw_data = pd.read_sql_query(text(ml_data_query), conn)
        
    raw_data.columns = [c.upper() for c in raw_data.columns]
    
    print("Running structural feature engineering...")
    df_engineered = engineer_all_features(raw_data)
    df_synergy = calculate_pairwise_synergy(df_engineered)
    models_dict, training_features = train_ai_predictor(df_engineered)
    
    os.makedirs('models', exist_ok=True)
    print("💾 Archiving pipeline artifacts...")
    joblib.dump(models_dict, 'models/rf_lineup_models_dict.joblib')
    joblib.dump(training_features, 'models/training_features.joblib')
    joblib.dump(df_synergy, 'models/synergy_matrix.joblib')
    joblib.dump(df_engineered, 'models/historical_features.joblib')
    
    print("✅ Model refresh tracking complete. Assets exported successfully.")