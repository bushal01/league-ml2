# -*- coding: utf-8 -*-
"""
Created on Mon Sep  4 16:15:42 2017

@author: Albert Bush

process_data.py

Script to read in JSON LoL match data 
and convert it to a more useful DataFrame format
in preparation for Machine Learning applications

"""
import pandas as pd
import data_constants as dc

def isExtractableMatch(unprocessed_match):
    necessary_keys = ['gameId','queueId','gameVersion','gameDuration','participants']
    for i in necessary_keys:
        if i not in unprocessed_match.keys():
            print('isExtractableMatch(): necessary_key not found n unprocessed_match.keys()')
            print(i)
            return(False)
        
    participants_keys = ['championId','teamId','spell1Id','spell2Id','timeline']
    participants_timeline_keys = ['lane','role']
    
    if type(unprocessed_match['participants']) != list:
        print('Type of participants error ' + str(type(unprocessed_match['participants'])))
        return(False)
    
    for player in unprocessed_match['participants']:
        for i in participants_keys:
            if i not in player.keys():
                print('3')
                return(False)
        for i in participants_timeline_keys:
            if i not in player['timeline'].keys():
                print('4')
                return(False)

    return(True)

def extractMatch(unprocessed_match):
    """ Take in the json data and extract match ID, positions, champions,
    summoner spells
    This function might be significantly changed if I create a match class.
    It will then be made into a method that creates an instance of the
    match class
    """
    match_id = unprocessed_match['gameId']
    queue_id = unprocessed_match['queueId']
    game_version = unprocessed_match['gameVersion']
    game_duration = unprocessed_match['gameDuration']
    participants = {}
    for player in unprocessed_match['participants']:
        participants[player['participantId']] = {'championId':player['championId'],
                                            'teamId':player['teamId'],
                                            'spell1Id':player['spell1Id'],
                                            'spell2Id':player['spell2Id'],
                                            'lane':player['timeline']['lane'],
                                            'role':player['timeline']['role'] }
    
    team_100_win = 0
    for team in unprocessed_match['teams']:
        if team['teamId'] == 100 and team['win'] == 'Win':
            team_100_win = 1
    
    return({'match_id':match_id, 
            'queue_id':queue_id, 
            'game_version':game_version,
            'game_duration':game_duration,
            'team_100_win':team_100_win,
            'participants':participants})            

def isValidMatch(match):
    """ Verify 5v5 SR
    Verify patch
    Verify Ranked? Don't do this initially -- maybe segment on ranked later
    """
    valid_qids = dc.getValidQueueIds()
    if match['queue_id'] in valid_qids:
        return(True)
    else:
        return(False)
    
def isValidTeamComp(match):
    """ Verify whether team comp is a valid one
    ie. solo top, solo mid, jungle, bot supp, bot carry
    """
    traditional_positions = ['BOTTOM_DUO_CARRY','BOTTOM_DUO_CARRY',
                 'BOTTOM_DUO_SUPPORT','BOTTOM_DUO_SUPPORT',
                 'JUNGLE_NONE','JUNGLE_NONE',
                 'MIDDLE_SOLO','MIDDLE_SOLO',
                 'TOP_SOLO','TOP_SOLO']
    positions = []
    for player in match['participants']:
        positions.append(match['participants'][player]['lane'] + '_' + 
                         match['participants'][player]['role'])
    
    positions.sort()
    if(positions == traditional_positions):
        return(True)
    else:
        return(False)
    
def isFixableTeamComp(match):
    """ If team comp is not seen as valid, see if it's fixable.
    As of 9/29, this will simply be a check that jungler 
    was misclassified.  It will simply check to see if there was one smite
    on each team
    """
    match = fixTeamComp(match)
    if isValidTeamComp(match):
        return True
    else:
        return False
            
def fixTeamComp(match):
    """ Scenario 1: Jungler camps a lane and gets classified as being in that lane.
        Solution 1: Check for smite.  Reassign that plyaer to jungle.  To correct
        the solo laners, if lane == 'MIDDLE' or lane == 'TOP' reassign role to
        'SOLO'.
        
        Scenario 2: Support/ADC roams and gets classified as jungler.
        Solution 2: Check JUNGLE roles to see if no smite.  If found, assign both
        BOTTOM laners to DUO and pass to Scenario 3.
        Scenario 3: Unable to distinguish between DUO_CARRY and DUO_SUPPORT.
        Solution 3: Check for HEAL or BARRIER.  That player gets DUO_CARRY, other
        gets DUO_SUPPORT.
    """
    smite = dc.getSmite()
    lanes = []
    for player in match['participants']:
        lanes.append(match['participants'][player]['lane'])
        
    num_mids = lanes.count('MIDDLE')
    num_bots = lanes.count('BOTTOM')
    num_tops = lanes.count('TOP')
    num_jung = lanes.count('JUNGLE')
    
    missing_lane = ''
    missing_role = ''
    
    if num_mids < 2:
        missing_lane = 'MIDDLE'
        missing_role = 'SOLO'
    elif num_tops < 2:
        missing_lane = 'TOP'
        missing_role = 'SOLO'
    elif num_jung < 2:
        missing_lane = 'JUNGLE'
        missing_role = 'NONE'
    elif num_bots < 4:
        missing_lane = 'BOTTOM'
        missing_role = 'DUO'

    # Scenario 1
    if missing_lane == 'JUNGLE':        
        for player in match['participants']:
            if match['participants'][player]['spell1Id'] == smite or match['participants'][player]['spell2Id'] == smite:
                match['participants'][player]['lane'] = 'JUNGLE'
                match['participants'][player]['role'] = 'NONE'
            elif match['participants'][player]['lane'] == 'MIDDLE' or match['participants'][player]['lane'] == 'TOP':
                match['participants'][player]['role'] = 'SOLO'
    
    # Scenario 2
    
    for player in match['participants']:
        if match['participants'][player]['lane'] == 'JUNGLE' and match['participants'][player]['spell1Id'] != smite and match['participants'][player]['spell2Id'] != smite:
            match['participants'][player]['lane'] = missing_lane
            match['participants'][player]['role'] = missing_role
                 
    # Scenario 3
    for player in match['participants']:
        if match['participants'][player]['lane'] == 'BOTTOM' and match['participants'][player]['role'] == 'SOLO':
            match['participants'][player]['role'] = 'DUO'
        if match['participants'][player]['role'] == 'DUO':
            if (match['participants'][player]['spell1Id'] in [dc.getHeal(),dc.getBarrier()] or match['participants'][player]['spell2Id'] in [dc.getHeal(),dc.getBarrier()]):
                match['participants'][player]['role'] = 'DUO_CARRY'
            else:
                match['participants'][player]['role'] = 'DUO_SUPPORT'
    
    return(match)
            
def processValidTeamComp(match):
    """ Function will take in a match record, and then extract the relevant
    information, and then re-organize it so it can be easily added
    as a record in our DataFrame -- get the teamId_champId_lane_role and
    team_100_win variables
    """
    champ_dict = dc.getChampIds()
    processed_match = {'match_id':[match['match_id']],
                       'queue_id':[match['queue_id']],
                       'game_version':[match['game_version']],
                       'game_duration':[match['game_duration']],
                       'team_100_win':[match['team_100_win']]}
    for i in match['participants']:
        match_col = str(match['participants'][i]['teamId']) + '_' + str(match['participants'][i]['lane']) + '_' + str(match['participants'][i]['role'])
        processed_match[match_col] = [champ_dict[match['participants'][i]['championId']][0:4]]
        #processed_match.append(str(match['participants'][i]['teamId']) + '_' + 
        #                       str(match['participants'][i]['lane']) + '_' + 
        #                       str(match['participants'][i]['role']) + '_' + 
        #                       str(match['participants'][i]['championId']))
    return(processed_match)

def build_processed_match_df(raw_match_data):
    match_cols_to_keep = ['gameDuration','gameId','gameVersion','participants','platformId','queueId','teams']
    raw_match_data = raw_match_data.loc[:,match_cols_to_keep]
    
    processed_match_df = pd.DataFrame(index = range(0,raw_match_data.shape[0]),
                                      columns = dc.getMatchDataCols())
    
    for row_num, unprocessed_match in raw_match_data.iterrows():
        #print(row_num)
        #print(unprocessed_match)
        if not isExtractableMatch(unprocessed_match):
            #print('not extractable')
            continue
        processed_match = extractMatch(unprocessed_match)
        if not isValidMatch(processed_match):
            continue
        if not isValidTeamComp(processed_match):
            if not isFixableTeamComp(processed_match):
                continue
            processed_match = fixTeamComp(processed_match)
        processed_match = processValidTeamComp(processed_match)
        processed_match_df = processed_match_df.append(pd.DataFrame(processed_match), ignore_index = True)
#        processed_match_df.iloc[row_num].loc['match_id'] = processed_match[0]
#        processed_match_df.iloc[row_num].loc['queue_id'] = processed_match[1]
#        processed_match_df.iloc[row_num].loc['game_version'] = processed_match[2]
#        processed_match_df.iloc[row_num].loc['game_duration'] = processed_match[3]
#        processed_match_df.iloc[row_num].loc['team_100_win'] = processed_match[4]
#        processed_match_df.iloc[row_num].loc[processed_match[5]] = 1
#        processed_match_df.iloc[row_num].loc[processed_match[6]] = 1
#        processed_match_df.iloc[row_num].loc[processed_match[7]] = 1
#        processed_match_df.iloc[row_num].loc[processed_match[8]] = 1
#        processed_match_df.iloc[row_num].loc[processed_match[9]] = 1
#        processed_match_df.iloc[row_num].loc[processed_match[10]] = 1
#        processed_match_df.iloc[row_num].loc[processed_match[11]] = 1
#        processed_match_df.iloc[row_num].loc[processed_match[12]] = 1
#        processed_match_df.iloc[row_num].loc[processed_match[13]] = 1
#        processed_match_df.iloc[row_num].loc[processed_match[14]] = 1
#                               
    processed_match_df = processed_match_df.fillna(0)
    processed_match_df = processed_match_df[processed_match_df['game_duration'] != 0]
    return(processed_match_df)

def compile_processed_match_dfs(match_dfs):
    total_rows = 0
    row_start_indexes = []
    row_end_indexes = []
    for i in match_dfs:
        row_start_indexes.append(total_rows)
        total_rows = total_rows + i.shape[0]
        row_end_indexes.append(total_rows - 1)
    
    compiled_dfs = pd.DataFrame(index = range(0,total_rows),
                                      columns = dc.getMatchDataCols())
    
    for i in range(0,len(match_dfs)):
        compiled_dfs.iloc[row_start_indexes[i]:row_end_indexes[i],:] = match_dfs[i]
        
    return(compiled_dfs)
