# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 13:40:57 2017

Data constants and setup
 - Set up dictionary of team ID to team color
 - Set up dictionary of summoner spell IDs - spell names
 - Set up dictionary of champ IDs - champ names
 - Set up list of traditional team comp positions

@author: Albert Bush
"""

import pandas as pd
import json
import requests
import time
import os
import dotenv


project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
dotenv_path = os.path.join(project_dir, '.env')
dotenv.load_dotenv(dotenv_path)
#os.getenv('MINED_DATA_DIR') = '../../data/mined_data/'
#API_KEY_FILE = '../../data/api_key.txt'

#def getApiKey():
#	with open (API_KEY_FILE, "r") as myfile:
#		data=myfile.readlines()[0]
#	return(data)

def getTeams():
    teams = ['100','200']
    teams_colors = ['BLUE','RED']
    teams_dict = dict(zip(teams, teams_colors))
    return(teams_dict)

def getValidQueueIds():
    # 400 - 5v5 SR Draft Pick
    # 420 - 5v5 SR Ranked Solo Q
    # 430 - 5v5 SR Blind Pick 
    # 440 - 5v5 SR Ranked Flex
    five_v_five_sr = [400, 420, 440]
    return(five_v_five_sr)

def getLanesPositions():
    return(['TOP_SOLO','MIDDLE_SOLO','BOTTOM_DUO_CARRY','BOTTOM_DUO_SUPPORT','JUNGLE_NONE'])

def getTraditionalPositions():
    return(['DUO_CARRY','DUO_SUPPORT','NONE','SOLO','SOLO'])

def getTeamsLanesRolesChamps():
    teams = getTeams().keys()
    positions = getLanesPositions()
    team_positions = []
    for i in teams:
        for j in positions:
            team_positions.append(i+'_'+j)
            
    champ_ids = list(getChampIds().keys())
    champ_ids.sort()
    team_positions_champions = []
    for i in team_positions:
        for j in champ_ids:
            team_positions_champions.append(i + '_' + str(j))
    return(team_positions_champions)

def getTeamsLanesRoles():
    teams = getTeams().keys()
    positions = getLanesPositions()
    team_positions = []
    for i in teams:
        for j in positions:
            team_positions.append(i+'_'+j)
    return(team_positions)

def getMatchDataCols():
    game_cols = ['match_id','queue_id','game_version','game_duration','team_100_win']
    teams_lanes_roles = getTeamsLanesRoles()
    return game_cols + teams_lanes_roles
    #champ_cols = getTeamsLanesRolesChamps()    
    #return game_cols + champ_cols

def getChampIds():
    """ Read in champions data to get champion IDs and names
    This is initially a dictionary with one key: data
    Inside data is a dictionary where every key is the champ
    name, and the rows are the id, key, name, and title"""
    with open(os.getenv('MINED_DATA_DIR') + 'champions.json', 'r') as f:
        champ_data_init = json.load(f)
    
    # Pull out the single key dictionary    
    champ_data = champ_data_init['data']
    # Convert to a DataFrame where every column is a champ
    champ_data = pd.DataFrame(champ_data)
    # Transpose the data
    champ_data = champ_data.T
    champ_data.loc['MonkeyKing','key'] = 'Wukong'
    # Pull out the 'id'
    champ_ids = champ_data['id'].tolist()
    # Pull out the names
    champ_names = champ_data['name'].tolist()
    # Zip them together into a dict
    champ_id_dict = dict(zip(champ_ids, champ_names))
    return(champ_id_dict)

def getChampsFourLetters():
    champ_id_dict = getChampIds()
    champs = pd.Series(list(champ_id_dict.values()))
    champs = champs.str.slice(0,4)
    return(champs)

def getSmite():
    return(11)

def getHeal():
    return(7)

def getBarrier():
    return(21)

def checkRateLimiting(request):
    '''print(request)'''
    if 'status' in request.keys():
        if request['status']['status_code'] == 429:
            print('Rate limited')
            return(True)
        else:
            print(request['status'])
            return(False)
    else:
        return(False)

def updateChampList(region = 'na1'):
    print('Updating Champ List')
    url = 'https://' + region + '.api.riotgames.com/lol/static-data/v3/champions/' + '?api_key=' + getApiKey()
    r = requests.get(url)
    if checkRateLimiting(r.json()):
        time.sleep(120)
        r = requests.get(url)
    with open(os.getenv('MINED_DATA_DIR') + 'champions.json', 'w') as outfile:
        json.dump(r.json(), outfile)
    
#    url = 'https://' + region + '.api.riotgames.com/lol/match/v3/matches/' + str(match_id) + '?api_key=' + dc.API_KEY
