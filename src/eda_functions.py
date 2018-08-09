# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 21:50:26 2018

EDA Functions

@author: Albert
"""
import numpy as np
import os
import data_constants as dc
import importlib
import pandas as pd
importlib.reload(dc)

def get_champ_win_rate(champ, data):
    teams_lanes_roles = dc.getTeamsLanesRoles()
    num_wins = 0
    tot_appearances = 0
    for lane in teams_lanes_roles:
        appearances = data[lane] == champ
        tot_appearances = tot_appearances + np.sum(appearances)
        if lane[0] == 1:
            num_wins = num_wins + np.sum(data['team_100_win'][appearances])
        else:
            num_wins = num_wins + (np.sum(1 - data['team_100_win'][appearances]))
    if tot_appearances < 1:
        return([np.nan, tot_appearances])
    else:
        return([num_wins / tot_appearances, tot_appearances])
            
def get_all_champ_win_rate(data):
    champs = dc.getChampsFourLetters()
    win_rate_dict = {}
    for i in champs:
        win_rate_dict[i] = get_champ_win_rate(i, data)
    win_rate_df = pd.DataFrame(win_rate_dict)
    return(win_rate_df)            