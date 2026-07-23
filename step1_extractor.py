import pandas as pd
import os
import glob
import re

def extract_clean_data(file_path, section_keyword):
    try:
        df = pd.read_csv(file_path, header=None, encoding='latin1')
    except Exception:
        return None

    section_rows = df[df.apply(lambda row: 
        row.astype(str).str.contains('Cypress', case=False).any() and 
        row.astype(str).str.contains(section_keyword, case=False).any()
    , axis=1)].index.tolist()
    
    if not section_rows:
        return None
        
    start_idx = section_rows[0] + 2
    temp_df = df.iloc[start_idx:].reset_index(drop=True)
    
    end_rows = temp_df[temp_df.isnull().all(axis=1) | temp_df.apply(lambda row: row.astype(str).str.contains('Byes:|Total', case=False).any(), axis=1)].index.tolist()
    
    if end_rows:
        end_idx = end_rows[0]
    else:
        end_idx = len(temp_df)
        
    clean_df = temp_df.iloc[:end_idx].copy()
    
    if len(clean_df) == 0:
        return None
        
    clean_df.columns = clean_df.iloc[0]
    clean_df = clean_df[1:].reset_index(drop=True)
    clean_df.columns = clean_df.columns.astype(str).str.replace('\t', '').str.strip()
    
    for col in clean_df.columns:
        if clean_df[col].dtype == 'object':
            clean_df[col] = clean_df[col].astype(str).str.replace('\t', '').str.strip()
            
    primary_col = 'BatsMan' if section_keyword == 'Batting' else 'Bowler'
    if primary_col in clean_df.columns:
        clean_df = clean_df[clean_df[primary_col] != '']
        clean_df = clean_df[clean_df[primary_col] != 'nan']

    return clean_df

def extract_fielding_data(file_path):
    try:
        df = pd.read_csv(file_path, header=None, encoding='latin1')
    except Exception:
        return None

    section_rows = df[df.apply(lambda row: 
        row.astype(str).str.contains('Batting', case=False).any() and 
        not row.astype(str).str.contains('Cypress', case=False).any()
    , axis=1)].index.tolist()
    
    if not section_rows:
        return None
        
    start_idx = section_rows[0] + 2
    temp_df = df.iloc[start_idx:].reset_index(drop=True)
    end_rows = temp_df[temp_df.isnull().all(axis=1) | temp_df.apply(lambda row: row.astype(str).str.contains('Byes:|Total', case=False).any(), axis=1)].index.tolist()
    
    end_idx = end_rows[0] if end_rows else len(temp_df)
    clean_df = temp_df.iloc[:end_idx].copy()
    
    if len(clean_df) == 0:
        return None
        
    clean_df.columns = clean_df.iloc[0]
    clean_df = clean_df[1:].reset_index(drop=True)
    clean_df.columns = clean_df.columns.astype(str).str.replace('\t', '').str.strip()
    
    for col in clean_df.columns:
        if clean_df[col].dtype == 'object':
            clean_df[col] = clean_df[col].astype(str).str.replace('\t', '').str.strip()
            
    if 'Fielder' in clean_df.columns and 'BatsMan' in clean_df.columns:
        fielding_df = clean_df[clean_df['Fielder'].astype(str).str.strip() != '']
        fielding_df = fielding_df[fielding_df['Fielder'].astype(str).str.lower() != 'nan']
        
        if len(fielding_df) == 0:
            return None
            
        cols_to_keep = ['Fielder', 'How Out', 'BatsMan', 'Bowler']
        existing_cols = [c for c in cols_to_keep if c in fielding_df.columns]
        return fielding_df[existing_cols]
        
    return None

def get_team_totals(file_path, team_name_hint):
    try:
        df = pd.read_csv(file_path, header=None, encoding='latin1')
    except Exception:
        return 0, 0, 0
        
    section_rows = df[df.apply(lambda row: 
        row.astype(str).str.contains(team_name_hint, case=False).any() and 
        row.astype(str).str.contains('Batting', case=False).any()
    , axis=1)].index.tolist()
         
    if not section_rows:
        return 0, 0, 0
        
    start_idx = section_rows[0] + 2
    temp_df = df.iloc[start_idx:].reset_index(drop=True)
    end_rows = temp_df[temp_df.apply(lambda row: row.astype(str).str.contains('Byes:', case=False).any(), axis=1)].index.tolist()
    
    if end_rows:
        target_row = temp_df.iloc[end_rows[0]]
        runs, overs = 0, 0
        vals = [str(x).strip() for x in target_row if str(x).strip() != '' and str(x).lower() != 'nan']
        for val in reversed(vals):
            if re.match(r'^\d+(\.\d+)?$', val):
                if overs == 0:
                    overs = float(val)
                elif runs == 0:
                    runs = int(float(val))
                    break
                    
        batting_rows = temp_df.iloc[1:end_rows[0]]
        how_out_col = batting_rows.iloc[:, 1].astype(str).str.strip().str.lower()
        non_wicket_statuses = ['*', 'dnb', 'not out', 'nan', 'none', '', 'rt', 'retired']
        wickets = how_out_col[~how_out_col.isin(non_wicket_statuses)].count()
            
        return runs, int(wickets), overs
        
    return 0, 0, 0

def parse_match_metadata(file_path):
    try:
        df = pd.read_csv(file_path, header=None, encoding='latin1', nrows=5)
    except Exception:
        return None, None, None, None
        
    row0 = str(df.iloc[0, 0])
    row1 = str(df.iloc[1, 0] if len(df) > 1 else "")
        
    row0_lower = row0.lower()
    if "tie" in row0_lower:
        result = "Tie"
    elif "abandoned" in row0_lower:
        result = "No Result"
    elif "forfeited" in row0_lower:
        if "cypress warrior" in row0_lower:
            result = "Win (Forfeit)"
        else:
            result = "Loss (Forfeit)"
    elif "cypress warrior" in row0_lower and "won" in row0_lower:
        result = "Win"
    else:
        result = "Loss"
        
    playoff_round = "N/A"
    if "quarter final" in row0_lower:
        playoff_round = "Quarter Final"
    elif "semi final" in row0_lower:
        playoff_round = "Semi Final"
    elif "final" in row0_lower and "quarter" not in row0_lower and "semi" not in row0_lower:
        playoff_round = "Final"
        
    opponent = "Unknown"
    if "Vs" in row1 or "vs" in row1.lower():
        teams = re.split(r'\s+[Vv]s\s+', row1.strip())
        if len(teams) == 2:
            if "cypress" in teams[0].lower():
                opponent = teams[1].strip()
            else:
                opponent = teams[0].strip()
                
    opponent = opponent.replace(u'\xa0', u' ').strip()
    
    mvp = "N/A"
    for cell in df.iloc[0]:
        cell_str = str(cell)
        if "MVP:" in cell_str:
            extracted_mvp = cell_str.split("MVP:")[-1].strip()
            if extracted_mvp != "":
                mvp = extracted_mvp
            break
                
    return opponent, result, playoff_round, mvp

all_batting_dfs = []
all_bowling_dfs = []
all_fielding_dfs = []
team_stats_list = []
motm_list = []

search_path = os.path.join("data", "**", "*.csv")
all_files = glob.glob(search_path, recursive=True)

for file in all_files:
    file_path_lower = file.lower()
    if "league awards" in file_path_lower:
        continue
        
    season_match = re.search(r'(spring|fall|summer)\s*20\d{2}|20\d{2}\s*(spring|fall|summer)', file_path_lower)
    if season_match:
        season_str = season_match.group(0)
        word = re.search(r'[a-z]+', season_str).group(0).title()
        year = re.search(r'\d{4}', season_str).group(0)
        season = f"{word} {year}"
    elif "practice" in file_path_lower:
        season = "Practice League"
    else:
        season = "Unknown"
            
    match_type = "Practice" if "practice" in file_path_lower else "Regular Season"
    if "playoff" in file_path_lower or "sf" in file_path_lower or "qf" in file_path_lower or "finals" in file_path_lower:
        match_type = "Playoff"

    metadata = parse_match_metadata(file)
    if metadata:
        opponent, result, playoff_round, mvp = metadata
    else:
        continue

    cypress_runs, cypress_wickets, cypress_overs = get_team_totals(file, 'Cypress')
    opponent_runs, opponent_wickets, opponent_overs = get_team_totals(file, opponent[:5]) 

    team_stats_list.append({
        'Season': season,
        'Match_Type': match_type,
        'Playoff_Round': playoff_round,
        'Opponent': opponent,
        'Match_Result': result,
        'Cypress_Runs': cypress_runs,
        'Cypress_Wickets': cypress_wickets,
        'Cypress_Overs': cypress_overs,
        'Opponent_Runs': opponent_runs,
        'Opponent_Wickets': opponent_wickets,
        'Opponent_Overs': opponent_overs,
        'File_Name': os.path.basename(file)
    })
    
    if mvp != "N/A":
        motm_list.append({
            'Season': season,
            'Match_Type': match_type,
            'Playoff_Round': playoff_round,
            'Opponent': opponent,
            'Match_Result': result,
            'Player_Name': mvp,
            'File_Name': os.path.basename(file)
        })

    try:
        bat_df = extract_clean_data(file, 'Batting')
        if bat_df is not None and not bat_df.empty:
            # Drop unnecessary columns
            cols_to_drop = [c for c in bat_df.columns if str(c).lower() in ['fielder', 'bowler', 'nan', 'none', '']]
            bat_df = bat_df.drop(columns=cols_to_drop, errors='ignore')
            
            # --- CALCULATE BATTING POSITION ---
            batting_positions = []
            batting_order = 1
            for _, row in bat_df.iterrows():
                how_out = str(row.get('How Out', '')).strip().lower()
                if how_out in ['dnb', 'did not bat']:
                    batting_positions.append('DNB')
                else:
                    if batting_order <= 2:
                        batting_positions.append('Opener')
                    else:
                        batting_positions.append(f'{batting_order - 2} Down')
                    batting_order += 1
            bat_df['Batting_Position'] = batting_positions
            # ----------------------------------
            
            bat_df['Season'] = season
            bat_df['Match_Type'] = match_type
            bat_df['Playoff_Round'] = playoff_round
            bat_df['Opponent'] = opponent
            bat_df['Match_Result'] = result
            bat_df['File_Name'] = os.path.basename(file)
            all_batting_dfs.append(bat_df)
            
        bowl_df = extract_clean_data(file, 'Bowling')
        if bowl_df is not None and not bowl_df.empty:
            bowl_df['5_Wicket_Haul'] = bowl_df['Wickets'].apply(lambda x: 1 if str(x).isdigit() and int(x) >= 5 else 0)
            
            bowl_df['Season'] = season
            bowl_df['Match_Type'] = match_type
            bowl_df['Playoff_Round'] = playoff_round
            bowl_df['Opponent'] = opponent
            bowl_df['Match_Result'] = result
            bowl_df['File_Name'] = os.path.basename(file)
            all_bowling_dfs.append(bowl_df)
            
        field_df = extract_fielding_data(file)
        if field_df is not None and not field_df.empty:
            field_df['Season'] = season
            field_df['Match_Type'] = match_type
            field_df['Playoff_Round'] = playoff_round
            field_df['Opponent'] = opponent
            field_df['Match_Result'] = result
            field_df['File_Name'] = os.path.basename(file)
            all_fielding_dfs.append(field_df)
            
    except Exception as e:
        print(f"Skipping {file} due to internal error.")

os.makedirs("data_clean", exist_ok=True)

if team_stats_list:
    pd.DataFrame(team_stats_list).to_csv("data_clean/cypress_warriorz_team_stats.csv", index=False)
    print("Team stats saved!")

if motm_list:
    pd.DataFrame(motm_list).to_csv("data_clean/cypress_warriorz_master_motm.csv", index=False)
    print("MOTM data saved!")

if all_batting_dfs:
    pd.concat(all_batting_dfs, ignore_index=True).to_csv("data_clean/cypress_warriorz_master_batting.csv", index=False)
    print("Batting data saved!")

if all_bowling_dfs:
    pd.concat(all_bowling_dfs, ignore_index=True).to_csv("data_clean/cypress_warriorz_master_bowling.csv", index=False)
    print("Bowling data saved!")
    
if all_fielding_dfs:
    pd.concat(all_fielding_dfs, ignore_index=True).to_csv("data_clean/cypress_warriorz_master_fielding.csv", index=False)
    print("Fielding data saved!")

def build_dim_player():
    full_df = pd.read_csv("Data/Roster/fullroster.csv")
    prac_df = pd.read_csv("Data/Roster/practiceleagueroster.csv")

    # 2. Rename columns to match the target database schema
    full_df = full_df.rename(columns={"PLAYER": "PLAYER_NAME"})

    # 3. Convert 'Is Active' ('Y'/'N') to boolean True/False
    full_df['IS_ACTIVE'] = full_df['Is Active'].apply(
        lambda x: True if str(x).strip().upper() == 'Y' else False
    )
    full_df = full_df.drop(columns=['Is Active'])

    # 4. Handle NaN values to prevent errors
    full_df['PLAYER_NAME'] = full_df['PLAYER_NAME'].fillna("")
    prac_df['PLAYER'] = prac_df['PLAYER'].fillna("")

    # 5. Create the IS_PRACTICE_LEAGUE flag
    practice_players = prac_df['PLAYER'].str.strip().tolist()
    full_df['IS_PRACTICE_LEAGUE'] = full_df['PLAYER_NAME'].str.strip().isin(practice_players)

    # 6. Generate the Fielding Alias (Includes middle names, no periods)
    def generate_fielding_alias(full_name):
        if not full_name:
            return "" # Handles empty rows
            
        # .split() automatically handles multiple spaces and removes them
        name_parts = str(full_name).strip().split()
        if not name_parts:
            return ""
        
        # If there's only one name listed
        if len(name_parts) == 1:
            return name_parts[0]
            
        # Join all names except the last one (First + Middle), then add the first letter of the last name
        first_and_middle = " ".join(name_parts[:-1])
        last_initial = name_parts[-1][0]
        return f"{first_and_middle} {last_initial}"

    full_df['FIELDING_ALIAS'] = full_df['PLAYER_NAME'].apply(generate_fielding_alias)

    # 7. Generate the sequential PLAYER_ID (1 to N)
    full_df.insert(0, 'PLAYER_ID', range(1, len(full_df) + 1))

    # 8. Save to CSV
    full_df.to_csv("DIM_PLAYER.csv", index=False)
    print("Transformation complete. Saved to DIM_PLAYER.csv!")
    
    return full_df

build_dim_player()