# -*- coding: utf-8 -*-
"""
Created on Fri Sep 29 13:40:57 2017

Data constants and setup
 - Set up dictionary of team ID to team color
 - Set up dictionary of summoner spell IDs - spell names
 - Set up dictionary of champ IDs - champ names
 - Set up list of traditional team comp roles

@author: Albert Bush
"""

import pandas as pd
import json
import requests
import time
import os
import dotenv


project_dir = os.path.join(os.path.dirname(__file__), os.pardir)
dotenv_path = os.path.join(project_dir, '.env')
dotenv.load_dotenv(dotenv_path)
# '../data/mined_data/'


def get_raw_data():
    return pd.read_csv(os.getenv('MINED_DATA_DIR') + 'processed_match_data.csv')

def get_teams():
    teams = ['100','200']
    teams_colors = ['BLUE','RED']
    teams_dict = dict(zip(teams, teams_colors))
    return(teams_dict)

def get_valid_queue_ids():
    # 400 - 5v5 SR Draft Pick
    # 420 - 5v5 SR Ranked Solo Q
    # 430 - 5v5 SR Blind Pick 
    # 440 - 5v5 SR Ranked Flex
    five_v_five_sr = [400, 420, 440]
    return(five_v_five_sr)

def get_lanes_roles():
    return(['TOP_SOLO','MIDDLE_SOLO','BOTTOM_DUO_CARRY','BOTTOM_DUO_SUPPORT','JUNGLE_NONE'])

def get_traditional_roles():
    return(['DUO_CARRY','DUO_SUPPORT','NONE','SOLO','SOLO'])

def get_teams_lanes_roles_champs():
    teams = get_teams().keys()
    roles = get_lanes_roles()
    team_roles = []
    for i in teams:
        for j in roles:
            team_roles.append(i+'_'+j)
            
    champ_ids = list(get_champ_ids().keys())
    champ_ids.sort()
    team_roles_champions = []
    for i in team_roles:
        for j in champ_ids:
            team_roles_champions.append(i + '_' + str(j))
    return(team_roles_champions)

def get_teams_lanes_roles():
    teams = get_teams().keys()
    roles = get_lanes_roles()
    team_roles = []
    for i in teams:
        for j in roles:
            team_roles.append(i+'_'+j)
    return(team_roles)

def get_match_data_cols():
    game_cols = ['match_id','queue_id','game_version','game_duration','team_100_win']
    teams_lanes_roles = get_teams_lanes_roles()
    return game_cols + teams_lanes_roles
    #champ_cols = get_teams_lanes_roles_champs()    
    #return game_cols + champ_cols

def get_champ_ids():
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

def get_champs_four_letters():
    champ_id_dict = get_champ_ids()
    champs = pd.Series(list(champ_id_dict.values()))
    champs = champs.str.slice(0,4)
    return(champs)

def get_smite():
    return(11)

def get_heal():
    return(7)

def get_barrier():
    return(21)

def check_rate_limiting(request):
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

def update_champ_list(region = 'na1'):
    print('Updating Champ List')
    url = 'https://' + region + '.api.riotgames.com/lol/static-data/v3/champions/' + '?api_key=' + os.getenv('API_KEY')
    r = requests.get(url)
    if check_rate_limiting(r.json()):
        time.sleep(120)
        r = requests.get(url)
    with open(os.getenv('MINED_DATA_DIR') + 'champions.json', 'w') as outfile:
        json.dump(r.json(), outfile)
