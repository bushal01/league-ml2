# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 12:31:25 2017

Main script that builds the DataFrame to hold processed match data

@author: Albert
"""
import pandas as pd
import os
import json
import numpy as np
import data_constants as dc
import process_match as pm
import match_crawler as mc
import importlib
import datetime
import requests
import time
importlib.reload(dc)
importlib.reload(pm)
importlib.reload(mc)

""" For the initial run
- load seed data
- initialize match DataFrame
while loop
    - process each match
    - extract player IDs
    - extract match ID
    - extract match info and add to DataFrame
    - append to CSV
    - pull a player's match history from the player ID list
    - repeat
"""
MAX_UNSCANNED_PLAYERS = 10000000
# Load seed data and convert to a DataFrame

with open(dc.DATA_DIR + 'matches1.json', 'r') as f:
    match1_data = json.load(f)
match1_data = pd.DataFrame(match1_data['matches'])
#print(match1_data.keys())

# extract initial list of players
scanned_players = mc.csvToDict(dc.DATA_DIR + 'scanned_players.csv')
unscanned_players = mc.csvToDict(dc.DATA_DIR + 'unscanned_players.csv')
if unscanned_players == {}:
    mc.extractPlayers(match1_data,scanned_players,unscanned_players)

# set up initial match_id_lists
scanned_matches = mc.csvToDict(dc.DATA_DIR + 'scanned_matches.csv')
unscanned_matches = mc.csvToDict(dc.DATA_DIR + 'unscanned_matches.csv')
    
match_dfs = []
# Scan all unscanned players and extract their matches
# ** Still need to do a 'season' filter so I don't pull too old matches **
# Desired number of matches to pull
num_matches_to_pull = 25000
matches_pulled_ctr = 0
while(matches_pulled_ctr < num_matches_to_pull):
    unscanned_playerids = list(unscanned_players.keys())
    for player_id in unscanned_playerids: # loop through unscanned player ids
        print(player_id)
        mc.scanPlayer(player_id, scanned_players, unscanned_players) # move player id from unscanned to scanned
        match_hist = mc.pullMatchHistory(player_id, region = 'na1') # pull that player's match history
        if 'matches' not in match_hist.keys(): # ensure valid match history
            continue
        mc.extractMatchIds(match_hist, scanned_matches, unscanned_matches) # add the new match ids to the match_id_dict
        raw_match_data = mc.scanMatches(scanned_matches, unscanned_matches)
        raw_match_data = raw_match_data.dropna(thresh = raw_match_data.shape[1] - 1)
        if(len(unscanned_players) < MAX_UNSCANNED_PLAYERS):
            mc.extractPlayers(raw_match_data,scanned_players,unscanned_players)
        print(len(unscanned_players))
        # scan all the new matches
        processed_match_df = pm.build_processed_match_df(raw_match_data)
        matches_pulled_ctr = matches_pulled_ctr + processed_match_df.shape[0]
        match_dfs.append(processed_match_df)
        print('Number of players scanned ' + str(len(scanned_players)))
        print('Number of matches pulled ' + str(matches_pulled_ctr))
        if(matches_pulled_ctr >= num_matches_to_pull):
            break

#compiled_pm_dfs = compile_processed_match_dfs(match_dfs)
compiled_pm_dfs = pd.concat(match_dfs, ignore_index = True)
pref_column_order = ['match_id','game_version','queue_id','game_duration','team_100_win','100_TOP_SOLO','100_JUNGLE_NONE','100_MIDDLE_SOLO','100_BOTTOM_DUO_CARRY','100_BOTTOM_DUO_SUPPORT','200_TOP_SOLO','200_JUNGLE_NONE','200_MIDDLE_SOLO','200_BOTTOM_DUO_CARRY','200_BOTTOM_DUO_SUPPORT']
compiled_pm_dfs = compiled_pm_dfs[pref_column_order]
int_cols = ['queue_id','game_duration','team_100_win']
compiled_pm_dfs[int_cols] = compiled_pm_dfs[int_cols].astype(int)
int64_cols = ['match_id']
compiled_pm_dfs[int64_cols] = compiled_pm_dfs[int64_cols].astype(np.int64)
if os.path.exists(dc.DATA_DIR + 'compiled_pm_dfs_test15.csv'):
    compiled_pm_dfs.to_csv(dc.DATA_DIR + 'compiled_pm_dfs_test15.csv', index = False, mode = 'a', header = False)
else:
    compiled_pm_dfs.to_csv(dc.DATA_DIR + 'compiled_pm_dfs_test15.csv', index = False)

mc.dictToCsv(scanned_players, dc.DATA_DIR + 'scanned_players.csv')
mc.dictToCsv(unscanned_players, dc.DATA_DIR + 'unscanned_players.csv')
mc.dictToCsv(scanned_matches, dc.DATA_DIR + 'scanned_matches.csv')
mc.dictToCsv(unscanned_matches, dc.DATA_DIR + 'unscanned_matches.csv')

    
    #{'message': 'Rate limit exceeded', 'status_code': 429}
    # 
    # (optional) load list of player ids
    # (optional) load list of match ids
    # (optional, might supercede above) load MatchCrawler object
    # 
      
