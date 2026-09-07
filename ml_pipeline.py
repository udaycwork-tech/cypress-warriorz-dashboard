import pandas as pd
import numpy as np
import itertools
import re
from sklearn.ensemble import RandomForestRegressor
import platform

platform.libc_ver = lambda *args, **kwargs: ("", "")

def parse_season_chronology(season_str):
    if not isinstance(season_str, str):
        return (2000, 0)
    
    season_str = season_str.strip().lower()
    year_match = re.search(r'\d{4}', season_str)
    year = int(year_match.group()) if year_match else 2026
    
    if 'spring' in season_str:
        order = 1
    elif 'summer' in season_str:
        order = 2
    elif 'fall' in season_str:
        order = 3
    elif 'adgo' in season_str:
        order = 4
    else:
        order = 0
        
    return (year, order)

def engineer_all_features(df):
    print("⚙️ Engineering chronological form features...")
    df = df.copy()
    
    # Ensure uppercase columns
    df.columns = [c.upper() for c in df.columns]
    
    if 'SEASON' not in df.columns:
        df['SEASON'] = 'Summer 2026'
    
    chrono_tuples = df['SEASON'].apply(parse_season_chronology)
    df['CHRONO_YEAR'] = [t[0] for t in chrono_tuples]
    df['CHRONO_ORDER'] = [t[1] for t in chrono_tuples]
    
    df = df.sort_values(by=['CHRONO_YEAR', 'CHRONO_ORDER', 'MATCH_LOG_ID']).reset_index(drop=True)
    
    df['form_last_3_pts'] = df.groupby('PLAYER_NAME')['FANTASY_PTS'].transform(
        lambda x: x.shift(1).rolling(window=3, min_periods=1).mean()
    ).fillna(0)
    
    df['career_avg_pts'] = df.groupby('PLAYER_NAME')['FANTASY_PTS'].transform(
        lambda x: x.shift(1).expanding().mean()
    ).fillna(0)
    
    df['career_runs_avg'] = df.groupby('PLAYER_NAME')['RUNS_SCORED'].transform(
        lambda x: x.shift(1).expanding().mean()
    ).fillna(0)
    
    df['form_runs_last_3'] = df.groupby('PLAYER_NAME')['RUNS_SCORED'].transform(
        lambda x: x.shift(1).rolling(window=3, min_periods=1).mean()
    ).fillna(0)
    
    df['form_wickets_last_3'] = df.groupby('PLAYER_NAME')['WICKETS_TAKEN'].transform(
        lambda x: x.shift(1).rolling(window=3, min_periods=1).mean()
    ).fillna(0)
    
    df['career_wickets_avg'] = df.groupby('PLAYER_NAME')['WICKETS_TAKEN'].transform(
        lambda x: x.shift(1).expanding().mean()
    ).fillna(0)
    
    df['career_fielding_avg'] = df.groupby('PLAYER_NAME')['CATCHES'].transform(
        lambda x: x.shift(1).expanding().mean()
    ).fillna(0)
    
    match_totals = df.groupby('MATCH_LOG_ID')['FANTASY_PTS'].sum().reset_index()
    match_totals.rename(columns={'FANTASY_PTS': 'team_total_match_pts'}, inplace=True)
    df = pd.merge(df, match_totals, on='MATCH_LOG_ID', how='left')
    df['team_synergy_score'] = df.groupby('PLAYER_NAME')['team_total_match_pts'].transform(
        lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
    ).fillna(0)
    df['opponent_difficulty_zscore'] = np.random.normal(0, 1, len(df))
    
    return df

def calculate_pairwise_synergy(df_matches):
    # FIXED: Added .copy() so uppercasing columns doesn't leak out and crash the main pipeline
    df = df_matches.copy()
    df.columns = [c.upper() for c in df.columns]
    match_rosters = df.groupby('MATCH_LOG_ID')['PLAYER_NAME'].apply(list).reset_index()
    match_scores = df.groupby('MATCH_LOG_ID')['FANTASY_PTS'].sum().reset_index()
    roster_scores = pd.merge(match_rosters, match_scores, on='MATCH_LOG_ID')
    
    synergy_records = []
    for _, row in roster_scores.iterrows():
        players_in_match = row['PLAYER_NAME']
        match_score = row['FANTASY_PTS']
        pairs = itertools.combinations(sorted(players_in_match), 2)
        for pair in pairs:
            synergy_records.append({'Player_A': pair[0], 'Player_B': pair[1], 'Match_Score': match_score})
            
    df_pairs = pd.DataFrame(synergy_records)
    if df_pairs.empty: return pd.DataFrame()
    
    duo_synergy = df_pairs.groupby(['Player_A', 'Player_B']).agg(
        games_played_together=('Match_Score', 'count'),
        avg_score_together=('Match_Score', 'mean')
    ).reset_index()
    
    return duo_synergy[duo_synergy['games_played_together'] >= 3]

def train_ai_predictor(df_ml_ready):
    features = [
        'form_last_3_pts', 'career_avg_pts', 'team_synergy_score', 'opponent_difficulty_zscore',
        'career_runs_avg', 'form_runs_last_3', 'career_wickets_avg', 'form_wickets_last_3', 'career_fielding_avg'        
    ]
    
    df_clean = df_ml_ready.dropna(subset=features + ['FANTASY_PTS'])
    X = df_clean[features]
    
    models = {
        'pts': RandomForestRegressor(n_estimators=100, random_state=42).fit(X, df_clean['FANTASY_PTS']),
        'runs': RandomForestRegressor(n_estimators=100, random_state=42).fit(X, df_clean['RUNS_SCORED']),
        'wkts': RandomForestRegressor(n_estimators=100, random_state=42).fit(X, df_clean['WICKETS_TAKEN'])
    }
    return models, features