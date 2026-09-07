import pandas as pd
from sqlalchemy import create_engine
import psycopg2
import os

def load_secrets():
    # Read database URL from .streamlit/secrets.toml
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    db_url = None
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            for line in f:
                if line.strip().startswith("url"):
                    db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not db_url:
        db_url = os.environ.get("NEON_DATABASE_URL")
    return db_url

def migrate_to_neon():
    db_url = load_secrets()
    if not db_url:
        print("❌ Error: Neon connection URL not found in .streamlit/secrets.toml")
        return

    print("🔌 Connecting to Neon PostgreSQL warehouse...")
    
    # 1. Execute DDL using pure psycopg2 (Bypasses SQLAlchemy colon parser errors)
    print("📜 Running CWCCProject.sql schema creation...")
    try:
        pg_url = db_url.replace("postgresql://", "postgres://")
        conn = psycopg2.connect(pg_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        with open("CWCCProject.sql", "r") as f:
            sql_commands = f.read()
            
        # Strip out any accidentally doubled percentage signs from SQL
        sql_commands = sql_commands.replace("%%", "%")
        
        cursor.execute(sql_commands)
        cursor.close()
        conn.close()
        print("✅ Tables and views initialized.")
        
    except Exception as e:
        print(f"❌ SQL Execution Error: {e}")
        return

    # 2. Ingest Data Tables via SQLAlchemy
    engine = create_engine(db_url)
    datasets = [
        ("DIM_PLAYER.csv", "dim_player"),
        ("data_clean/cypress_warriorz_team_stats.csv", "dim_team_stats"),
        ("data_clean/cypress_warriorz_master_motm.csv", "dim_motm"),
        ("data_clean/cypress_warriorz_league_awards.csv", "dim_league_awards"),
        ("data_clean/cypress_warriorz_master_batting.csv", "fact_batting"),
        ("data_clean/cypress_warriorz_master_bowling.csv", "fact_bowling"),
        ("data_clean/cypress_warriorz_master_fielding.csv", "fact_fielding"),
        ("data_clean/cypress_warriorz_match_fantasy_points.csv", "fact_fantasy_points"),
    ]

    for csv_file, table_name in datasets:
        if os.path.exists(csv_file):
            print(f"📥 Loading {csv_file} -> {table_name}...")
            df = pd.read_csv(csv_file)
            
            # SMART LOWERCASE: Postgres auto-lowercases unquoted columns,
            # but strictly preserves capitalization for quoted columns (spaces/numbers)
            strict_cols = ['How Out', 'No Balls', 'Dot Balls', '5_Wicket_Haul']
            df.columns = [c if c in strict_cols else c.lower() for c in df.columns]
            
            with engine.begin() as sql_conn:
                df.to_sql(table_name, sql_conn, schema="raw_data", if_exists="append", index=False)
        else:
            print(f"⚠️ Warning: {csv_file} not found. Skipping.")

    print("\n🎉 ALL DATASETS SUCCESSFULLY MIGRATED TO NEON POSTGRESQL!")

if __name__ == "__main__":
    migrate_to_neon()