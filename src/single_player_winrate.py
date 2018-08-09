# -*- coding: utf-8 -*-
"""
Created on Fri Mar  2 18:51:09 2018

Pull a single player's match history and get their win rates on each champion

@author: Albert
"""
import os
import data_constants as dc
import process_match as pm
import match_crawler as mc
import eda_functions
import importlib
importlib.reload(dc)
importlib.reload(pm)
os.chdir('C:/Users/Albert/Desktop/Programming/league-ml2/src/data-mining/')
importlib.reload(mc)

scanned_matches = {}
unscanned_matches = {}
nortikdos = 33009952
jackperi646 = 33308711
player_id = nortikdos

match_hist = mc.pullMatchHistory(player_id, region = 'na1') # pull that player's match history
mc.extractMatchIds(match_hist, scanned_matches, unscanned_matches, num_matches_to_pull = 'max') # add the new match ids to the match_id_dict
raw_match_data = mc.scanMatches(scanned_matches, unscanned_matches)
raw_match_data = raw_match_data.dropna(thresh = raw_match_data.shape[1] - 1)
processed_match_df = pm.build_processed_match_df(raw_match_data)

player_stats = eda_functions.get_all_champ_win_rate(processed_match_df).transpose()
player_stats.columns = ['win_rate','games_played']