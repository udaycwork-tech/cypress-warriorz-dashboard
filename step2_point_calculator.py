import pandas as pd
import numpy as np
import os

print("Loading Master Data...")
try:
    bat_df = pd.read_csv('data_clean/cypress_warriorz_master_batting.csv')
    bowl_df = pd.read_csv('data_clean/cypress_warriorz_master_bowling.csv')
    field_df = pd.read_csv('data_clean/cypress_warriorz_master_fielding.csv')
    motm_df = pd.read_csv('data_clean/cypress_warriorz_master_motm.csv')
    players_df = pd.read_csv('DIM_PLAYER.csv')
except FileNotFoundError as e:
    print(f"Error: Could not find file. Make sure you are in the root directory. {e}")
    exit()

alias_to_name = dict(zip(players_df['FIELDING_ALIAS'], players_df['PLAYER_NAME']))
match_performances = []
all_matches = set(bat_df['File_Name']).union(set(bowl_df['File_Name']))

def overs_to_balls(overs_val):
    try:
        val = float(overs_val)
        completed_overs = int(val)
        extra_balls = int(round((val - completed_overs) * 10))
        return (completed_overs * 6) + extra_balls
    except:
        return 0

print("Calculating Game-by-Game Fantasy Points...")

for match in all_matches:
    match_players = {}
    
    def get_player_record(name):
        real_name = alias_to_name.get(name, name.strip())
        if real_name not in match_players:
            match_players[real_name] = {
                'Player_Name': real_name, 'File_Name': match,
                'Batting_Pts': 0.0, 'Bowling_Pts': 0.0, 'Fielding_Pts': 0.0, 'MOTM_Pts': 0.0,
                'Total_Pts': 0.0
            }
        return match_players[real_name]

    # BATTING POINTS
    match_bat = bat_df[bat_df['File_Name'] == match]
    for _, row in match_bat.iterrows():
        player = get_player_record(row['BatsMan'])
        pts = 0.0
        
        runs = pd.to_numeric(row['Runs'], errors='coerce')
        runs = runs if pd.notna(runs) else 0.0
        balls = pd.to_numeric(row['Balls'], errors='coerce')
        balls = balls if pd.notna(balls) else 0.0
        fours = pd.to_numeric(row['Fours'], errors='coerce')
        fours = fours if pd.notna(fours) else 0.0
        sixes = pd.to_numeric(row['Sixers'], errors='coerce')
        sixes = sixes if pd.notna(sixes) else 0.0
        how_out = str(row['How Out']).strip().lower()
        
        pts += (runs * 1.0)
        pts += (fours * 1.0)
        pts += (sixes * 2.0)
        
        not_out_statuses = ['not out', 'dnb', 'did not bat', 'retired', 'rt', 'nan', '', '*']
        if runs == 0 and how_out not in not_out_statuses:
            pts -= 2.0
            
        if runs >= 10 and balls > 0:
            sr = (runs / balls) * 100.0
            if sr < 50: pts -= 6.0
            elif sr < 75: pts -= 4.0
            elif sr < 100: pts -= 2.0
            elif sr < 125: pts += 1.0
            elif sr < 150: pts += 3.0
            elif sr < 175: pts += 5.0
            elif sr < 200: pts += 7.0
            else: pts += 9.0
            
        if runs >= 50: pts += 8.0
        elif runs >= 40: pts += 6.0
        elif runs >= 30: pts += 4.0
        elif runs >= 20: pts += 2.0
        elif runs >= 10: pts += 1.0
        
        if runs >= 100: pts += 20.0
        elif runs >= 50: pts += 8.0
        
        player['Batting_Pts'] += pts

    # BOWLING POINTS
    match_bowl = bowl_df[bowl_df['File_Name'] == match]
    for _, row in match_bowl.iterrows():
        player = get_player_record(row['Bowler'])
        pts = 0.0
        
        wickets = pd.to_numeric(row['Wickets'], errors='coerce')
        wickets = wickets if pd.notna(wickets) else 0.0
        maidens = pd.to_numeric(row['Madiens'], errors='coerce')
        maidens = maidens if pd.notna(maidens) else 0.0
        runs_allowed = pd.to_numeric(row['Runs'], errors='coerce')
        runs_allowed = runs_allowed if pd.notna(runs_allowed) else 0.0
        overs = str(row['Overs'])
        total_balls = overs_to_balls(overs)
        
        pts += (wickets * 20.0)
        pts += (maidens * 15.0)
        
        if wickets >= 5: pts += 12.0
        elif wickets == 4: pts += 8.0
        elif wickets == 3: pts += 5.0
        elif wickets == 2: pts += 3.0
        
        if total_balls >= 12:
            true_overs = total_balls / 6.0
            eco = runs_allowed / true_overs if true_overs > 0 else 0.0
            
            if eco < 2.0: pts += 10.0
            elif eco < 4.0: pts += 7.0
            elif eco < 6.0: pts += 5.0
            elif eco < 8.0: pts += 2.0
            elif eco < 10.0: pts -= 1.0
            elif eco < 12.0: pts -= 3.0
            else: pts -= 5.0
            
        player['Bowling_Pts'] += pts

    # FIELDING POINTS
    match_field = field_df[field_df['File_Name'] == match]
    player_catches = {}
    
    for _, row in match_field.iterrows():
        fielder_raw = str(row['Fielder']).strip()
        how_out = str(row['How Out']).strip().lower()
        
        fielders = [f.strip() for f in fielder_raw.split('/')] if '/' in fielder_raw else [fielder_raw]
        
        for f in fielders:
            if not f or f == 'nan': continue
            player = get_player_record(f)
            real_name = player['Player_Name']
            pts = 0.0
            
            if 'ct' in how_out or 'c' in how_out:
                pts += 8.0
                player_catches[real_name] = player_catches.get(real_name, 0) + 1
            elif 'st' in how_out:
                pts += 12.0
            elif 'ro' in how_out or 'run' in how_out:
                pts += 6.0
            
            player['Fielding_Pts'] += pts
            
    for p_name, catches in player_catches.items():
        if catches >= 3:
            match_players[p_name]['Fielding_Pts'] += 4.0

    # MOTM POINTS
    match_motm = motm_df[motm_df['File_Name'] == match]
    for _, row in match_motm.iterrows():
        player = get_player_record(row['Player_Name'])
        player['MOTM_Pts'] += 25.0
        
    for p in match_players.values():
        p['Total_Pts'] = p['Batting_Pts'] + p['Bowling_Pts'] + p['Fielding_Pts'] + p['MOTM_Pts']
        match_performances.append(p)

fantasy_df = pd.DataFrame(match_performances)
metadata = bat_df[['File_Name', 'Season', 'Match_Type', 'Playoff_Round', 'Opponent', 'Match_Result']].drop_duplicates()
final_df = pd.merge(fantasy_df, metadata, on='File_Name', how='left')

cols = ['Player_Name', 'Season', 'Match_Type', 'Playoff_Round', 'Opponent', 'Match_Result', 
        'Batting_Pts', 'Bowling_Pts', 'Fielding_Pts', 'MOTM_Pts', 'Total_Pts', 'File_Name']
final_df = final_df[cols].sort_values(by=['File_Name', 'Total_Pts'], ascending=[True, False])
final_df.to_csv("data_clean/cypress_warriorz_match_fantasy_points.csv", index=False)
print("SUCCESS! Fantasy points generated at: data_clean/cypress_warriorz_match_fantasy_points.csv")