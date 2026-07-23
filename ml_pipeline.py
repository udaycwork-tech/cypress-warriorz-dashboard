import pandas as pd
import numpy as np
import itertools
import re
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
import platform

# --- WINDOWS ENVIRONMENT PATCH ---
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
    else:
        order = 0
        
    return (year, order)

# ==========================================
# 1. CHRONOLOGICAL FEATURE ENGINEERING
# ==========================================
def engineer_all_features(df):
    print("⚙️ Engineering chronological form features...")
    df = df.copy()
    
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
    match_rosters = df_matches.groupby('MATCH_LOG_ID')['PLAYER_NAME'].apply(list).reset_index()
    match_scores = df_matches.groupby('MATCH_LOG_ID')['FANTASY_PTS'].sum().reset_index()
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

# ==========================================
# 2. OPTIMIZED COMBINATORIAL SOLVER 
# ==========================================
def generate_weekend_lineup(active_players_list, df_historical, models_dict, duo_synergy_df, features):
    df_working = df_historical.copy()
    
    df_working['PLAYER_NAME_NORM'] = df_working['PLAYER_NAME'].astype(str).str.strip().str.lower()
    active_players_norm = [str(p).strip().lower() for p in active_players_list]
    
    if 'SEASON' not in df_working.columns:
        df_working['SEASON'] = 'Summer 2026'
    
    chrono_tuples = df_working['SEASON'].apply(parse_season_chronology)
    df_working['CHRONO_YEAR'] = [t[0] for t in chrono_tuples]
    df_working['CHRONO_ORDER'] = [t[1] for t in chrono_tuples]
    
    df_latest = df_working[df_working['PLAYER_NAME_NORM'].isin(active_players_norm)].copy()
    if df_latest.empty: return pd.DataFrame()
    
    df_latest = df_latest.sort_values(by=['CHRONO_YEAR', 'CHRONO_ORDER', 'MATCH_LOG_ID']).groupby('PLAYER_NAME_NORM').tail(1).reset_index(drop=True)
    
    df_latest['AI_Projected_Points'] = models_dict['pts'].predict(df_latest[features])
    df_latest['AI_Projected_Runs'] = models_dict['runs'].predict(df_latest[features]).round(1)
    df_latest['AI_Projected_Wickets'] = models_dict['wkts'].predict(df_latest[features]).round(1)
    
    # ─── PHASE 1: CAPTAINS ONLY OVERRIDE LOCK ───
    mandatory_norms = [m.strip().lower() for m in ["Uday Chaudhary", "Garv Chaudhary"]]
    present_mandatory = [p for p in mandatory_norms if p in df_latest['PLAYER_NAME_NORM'].tolist()]
    
    df_forced = df_latest[df_latest['PLAYER_NAME_NORM'].isin(present_mandatory)].copy()
    df_pool = df_latest[~df_latest['PLAYER_NAME_NORM'].isin(present_mandatory)].copy()
    
    # Pre-calculate forced stats to speed up the loop
    forced_runs = df_forced['AI_Projected_Runs'].sum() if not df_forced.empty else 0
    forced_wkts = df_forced['AI_Projected_Wickets'].sum() if not df_forced.empty else 0
    
    # ─── PHASE 2: HIGH-SPEED COMBINATORIAL SOLVER ───
    # Capped at 16 to prevent UI freezing (11,440 combinations max)
    if len(df_pool) > 16:
        # Heavily weight runs to protect pure batsmen in the top 16 cutoff
        df_pool['selection_priority'] = (df_pool['AI_Projected_Runs'] * 2.0) + df_pool['AI_Projected_Wickets'] + (df_pool['AI_Projected_Points'] * 0.2)
        df_pool = df_pool.nlargest(16, 'selection_priority')
        
    pool_records = df_pool.to_dict('records')
    slots_needed = max(0, 11 - len(df_forced))
    
    best_combination_indices = None
    best_fitness = -99999999
    
    if len(pool_records) < slots_needed:
        best_11 = pd.DataFrame(df_forced.to_dict('records') + pool_records)
    else:
        # Extract to fast arrays for loop efficiency
        p_runs = [p['AI_Projected_Runs'] for p in pool_records]
        p_wkts = [p['AI_Projected_Wickets'] for p in pool_records]
        
        # Loop via index (vastly faster than dict iteration)
        for combo in itertools.combinations(range(len(pool_records)), slots_needed):
            total_runs = forced_runs + sum(p_runs[i] for i in combo)
            total_wkts = forced_wkts + sum(p_wkts[i] for i in combo)
            
            if 8.0 <= total_wkts <= 10.0:
                fitness = (1000000 + total_runs) if total_runs >= 150.0 else (500000 + total_runs)
            elif total_wkts < 8.0:
                fitness = (total_wkts - 8.0) * 10000 + total_runs
            else:
                fitness = (10.0 - total_wkts) * 10000 + total_runs
                
            if fitness > best_fitness:
                best_fitness = fitness
                best_combination_indices = combo
                
        if best_combination_indices:
            optimal_pool = [pool_records[i] for i in best_combination_indices]
            best_11 = pd.DataFrame(df_forced.to_dict('records') + optimal_pool)
        else:
            best_11 = pd.DataFrame(df_forced.to_dict('records') + pool_records)

    # ─── PHASE 3: BATTING POSITION ROUTING MATRIX ───
    slots = list(range(1, len(best_11) + 1))
    p_names = best_11['PLAYER_NAME'].tolist()
    df_hist_team = df_working[df_working['PLAYER_NAME'].isin(p_names)]
    
    hist_pos_means = df_hist_team.groupby(['PLAYER_NAME', 'BATTING_POSITION'])['RUNS_SCORED'].mean().to_dict()
    career_means = df_hist_team.groupby('PLAYER_NAME')['RUNS_SCORED'].mean().to_dict()
    
    pos_labels = {1:'Opener', 2:'Opener', 3:'1 Down', 4:'2 Down', 5:'3 Down', 6:'4 Down', 7:'5 Down', 8:'6 Down', 9:'7 Down', 10:'8 Down', 11:'9 Down'}
    
    final_ordered_rows = []
    pool_to_assign = best_11.to_dict('records')
    
    for slot_num in slots:
        pos_label = pos_labels.get(slot_num, 'N/A')
        best_candidate = None
        best_match_score = -999999
        
        for p_row in pool_to_assign:
            p_name = p_row['PLAYER_NAME']
            hist_avg = hist_pos_means.get((p_name, pos_label), career_means.get(p_name, 0) * 0.8)
            
            if slot_num <= 5:
                match_score = (p_row['AI_Projected_Runs'] * 0.85) + (hist_avg * 0.15)
            else:
                match_score = (hist_avg * 0.65) + (p_row['AI_Projected_Runs'] * 0.35)
                
            if match_score > best_match_score:
                best_match_score = match_score
                best_candidate = p_row
                
        if best_candidate:
            best_candidate['Optimal_Batting_Order'] = slot_num
            final_ordered_rows.append(best_candidate)
            pool_to_assign.remove(best_candidate)
            
    df_final_lineup = pd.DataFrame(final_ordered_rows)
    df_final_lineup = df_final_lineup.sort_values(by='Optimal_Batting_Order').reset_index(drop=True)
    
    display_cols = [
        'Optimal_Batting_Order', 'PLAYER_NAME', 'AI_Projected_Points', 
        'AI_Projected_Runs', 'AI_Projected_Wickets'
    ]
    return df_final_lineup[display_cols]