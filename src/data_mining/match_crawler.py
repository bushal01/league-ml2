# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 19:34:18 2017

Match Crawler
    - Take in raw match data as a DF and extract the list of player ids
    - Add new player ids to the list
    - Take in a player id and pull their match history.  Return it as raw match data
    

@author: Albert
"""

import pandas as pd
import data_constants as dc
import datetime
import requests
import time
import os.path

def extractPlayers(match_df, scanned, unscanned):
    """ Goes through each row in the match_df, pulls out all the currentAccountId
    and currentPlatformId in each match, DF that will store summoner IDs, 
    platform (NA/EUW,etc, whether that summoner's match history has been 
    crawled, and the last crawl date)
    """
    player_ctr = 0
    for index, row in match_df.iterrows():
        pids = row['participantIdentities']
        for j in pids:
            if j['player']['accountId'] not in scanned and j['player']['accountId'] not in unscanned:
                #unscanned[j['player']['accountId']] = {'currentPlatformId':j['player']['currentPlatformId']}
                unscanned[j['player']['accountId']] = j['player']['currentPlatformId']
                #print(str(j['player']['currentPlatformId']))
                player_ctr = player_ctr + 1
    print(str(player_ctr) + " new summoner IDs added to the list")
        
def extractMatchIds(match_history, scanned, unscanned, num_matches_to_pull = 10):
    if num_matches_to_pull == 'max':
        num_matches_to_pull = len(match_history['matches'])
    matches = pd.DataFrame(match_history['matches'])
    for index in range(0,matches.shape[0]):
        if matches.iloc[index]['gameId'] not in scanned and matches.iloc[index]['gameId'] not in unscanned:
            unscanned[matches.iloc[index]['gameId']] = matches.iloc[index]['platformId']
            num_matches_to_pull = num_matches_to_pull - 1
            if num_matches_to_pull == 0:
                break

def pullMatchHistory(player_id, region = 'na1'):
    print('Pulling match history for player ' + str(player_id))
    url = 'https://' + region + '.api.riotgames.com/lol/match/v3/matchlists/by-account/' + str(player_id) + '?api_key=' + dc.getApiKey()
    r = requests.get(url)
    if dc.checkRateLimiting(r.json()):
        time.sleep(120)
        r = requests.get(url)
    return(r.json())

def pullMatchData(match_id, region = 'na1'):
    print('Pulling match ' + str(match_id))
    url = 'https://' + region + '.api.riotgames.com/lol/match/v3/matches/' + str(match_id) + '?api_key=' + dc.getApiKey()
    r = requests.get(url)
    if dc.checkRateLimiting(r.json()):
        time.sleep(120)
        r = requests.get(url)
    return(r.json())    

def scanPlayer(player_id, scanned, unscanned):
    cpid = ''
    if player_id in unscanned:
        cpid = unscanned[player_id]
        del unscanned[player_id]
    else:
        cpid = scanned[player_id]
    scanned[player_id] = cpid

# Take all unscanned matches, pull their data, and add their match ids to scanned
def scanMatches(scanned, unscanned):
    match_data = []
    unscanned_keys = list(unscanned.keys())
    for i in unscanned_keys:
        match_data.append(pullMatchData(i,unscanned[i]))
        scanned[i] = unscanned[i]
        del unscanned[i]               
    return(pd.DataFrame(match_data))

def dictToCsv(dict_to_convert, file_name):
    df = pd.DataFrame(dict_to_convert, index = [0])
    df = df.transpose()
    df.columns = ['region']
    df['id'] = df.index
    df = df[['id','region']]
    df.to_csv(file_name, index = False)

def csvToDict(file_name):
    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
        return(dict(zip(df['id'], df['region'])))
    else:
        return({})