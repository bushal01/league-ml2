# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 12:31:25 2017

Main data mining script
Iteratively pulls player's match histories from Riot's API, pulls
data from the 10 most recent matches, stores all playerIds
seen, and builds a pd.DataFrame of matches pulled. At runtime,
asks for user input to specify how many hours to run.

@author: bushal01
"""
import pandas as pd
import json
import numpy as np
import process_match as pm
import match_crawler as mc
import os
import time
import dotenv

# Loading the .env file which stores API_KEY and MINED_DATA_DIR
project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
dotenv_path = os.path.join(project_dir, '.env')
dotenv.load_dotenv(dotenv_path)

MAX_UNSCANNED_PLAYERS = 10000000  # To prevent too large of a playerId file
OUTPUT_FILE = 'processed_match_data.csv'
desired_run_time = float(input("Enter desired run time in hours: ")) * 3600  # convert to seconds

# Load CSV of scanned and unscanned playerIds and convert to dictionary
# If no such files exist, uses seed data supplied from Riot to get an initial player base to scan
# Note: file existence is checked inside mc.csv_to_dict()
scanned_players = mc.csv_to_dict( os.getenv('MINED_DATA_DIR') + 'scanned_players.csv')
unscanned_players = mc.csv_to_dict(os.getenv('MINED_DATA_DIR') + 'unscanned_players.csv')
if unscanned_players == {}:
    print(os.getenv('MINED_DATA_DIR'))
    with open(os.path.join(os.getenv('MINED_DATA_DIR'), 'matches1.json'), 'r') as f:
        match1_data = json.load(f)
    match1_data = pd.DataFrame(match1_data['matches'])
    mc.extract_players(match1_data, scanned_players, unscanned_players)

# Load CSV of scanned and unscanned matches.  File existence is checked inside mc.csv_to_dict()
scanned_matches = mc.csv_to_dict(os.getenv('MINED_DATA_DIR') + 'scanned_matches.csv')
unscanned_matches = mc.csv_to_dict(os.getenv('MINED_DATA_DIR') + 'unscanned_matches.csv')
    
match_dfs = []  # This will store a list of DataFrames to be concatenated later

# ** Still need to do a 'season' filter so I don't pull too old matches **
matches_pulled_ctr = 0
start_time = time.time()
# While loop that runs for the specified amount of time
# Inside, for loop takes an unscanned playerId, pulls its match history,
# pulls 10 most recent matches and adds any ranked/normal draft 5v5 SR
# to a DataFrame. Then takes all playerIds from those matches and stores
# them for scanning later
while time.time() - start_time < desired_run_time:
    unscanned_playerids = list(unscanned_players.keys())
    for player_id in unscanned_playerids:
        print(player_id)
        mc.scan_player(player_id, scanned_players, unscanned_players)  # Move player id from unscanned to scanned
        match_hist = mc.pull_match_history(player_id, region='na1')  # Pull match history
        if 'matches' not in match_hist.keys():  # Ensures valid match history is returned
            continue
        mc.extract_match_ids(match_hist, scanned_matches, unscanned_matches)  # Add the new match ids to the match_id_dict
        raw_match_data = mc.scan_matches(scanned_matches, unscanned_matches)  # Get match data
        raw_match_data = raw_match_data.dropna(thresh=raw_match_data.shape[1] - 1)  # Drop bad match data
        if len(unscanned_players) < MAX_UNSCANNED_PLAYERS:
            mc.extract_players(raw_match_data, scanned_players, unscanned_players)  # Get unscanned playerIds
        print(len(unscanned_players))
        if raw_match_data.shape[0] != 0:  # Check match data is non-empty
            processed_match_df = pm.build_processed_match_df(raw_match_data)  # Transform JSON into DataFrame
            matches_pulled_ctr = matches_pulled_ctr + processed_match_df.shape[0]
            match_dfs.append(processed_match_df)  # Store DF in a list of DFs to be concatenated later
        print('Number of players scanned ' + str(len(scanned_players)))
        print('Number of matches pulled ' + str(matches_pulled_ctr))
        print('Run time: ' + time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time)))
        if time.time() - start_time > desired_run_time:
            break

# Compile small DFs into a large one, format it, and append it to a file
compiled_pm_dfs = pd.concat(match_dfs, ignore_index=True)  # Compile small DFs into a large one
pref_column_order = ['match_id', 'game_version', 'queue_id', 'game_duration', 'team_100_win', '100_TOP_SOLO',
                     '100_JUNGLE_NONE', '100_MIDDLE_SOLO', '100_BOTTOM_DUO_CARRY', '100_BOTTOM_DUO_SUPPORT',
                     '200_TOP_SOLO', '200_JUNGLE_NONE', '200_MIDDLE_SOLO', '200_BOTTOM_DUO_CARRY',
                     '200_BOTTOM_DUO_SUPPORT']
compiled_pm_dfs = compiled_pm_dfs[pref_column_order]
# Convert some columns to int or int64
int_cols = ['queue_id', 'game_duration', 'team_100_win']
compiled_pm_dfs[int_cols] = compiled_pm_dfs[int_cols].astype(int)
int64_cols = ['match_id']
compiled_pm_dfs[int64_cols] = compiled_pm_dfs[int64_cols].astype(np.int64)
if os.path.exists(os.getenv('MINED_DATA_DIR') + OUTPUT_FILE):
    compiled_pm_dfs.to_csv(os.getenv('MINED_DATA_DIR') + OUTPUT_FILE, index=False, mode='a', header=False)
else:
    compiled_pm_dfs.to_csv(os.getenv('MINED_DATA_DIR') + OUTPUT_FILE, index=False)

# Write players and matches to a file
mc.dict_to_csv(scanned_players, os.getenv('MINED_DATA_DIR') + 'scanned_players.csv')
mc.dict_to_csv(unscanned_players, os.getenv('MINED_DATA_DIR') + 'unscanned_players.csv')
mc.dict_to_csv(scanned_matches, os.getenv('MINED_DATA_DIR') + 'scanned_matches.csv')
mc.dict_to_csv(unscanned_matches, os.getenv('MINED_DATA_DIR') + 'unscanned_matches.csv')
