import numpy as np
import pandas as pd
import data_constants as dc


def champ_win_rate(matches_df, champ, lane='all'):
    """Calculate the win rate of a single champion.

     By default, looks in every lane.  Lane can also
     be specified (eg. TOP_SOLO)
     """
    teams_lanes_roles = dc.get_teams_lanes_roles()
    if lane != 'all':
        teams_lanes_roles = ['100_' + lane, '200_' + lane]
    num_wins = 0
    tot_appearances = 0
    for lane in teams_lanes_roles:
        appearances = matches_df[lane] == champ
        tot_appearances = tot_appearances + np.sum(appearances)
        if lane[0] == 1:
            num_wins = num_wins + np.sum(matches_df['team_100_win'][appearances])
        else:
            num_wins = num_wins + (np.sum(1 - matches_df['team_100_win'][appearances]))
    if tot_appearances < 1:
        return {'win_rate':0, 'games_played':0}
    else:
        return {'win_rate': num_wins / tot_appearances, 'games_played': tot_appearances}


def all_champ_win_rates(matches_df, lane='all'):
    """Create a DataFrame of each champion and their win rate in a particular lane."""
    champs = dc.get_champs_four_letters()
    win_rate_df = pd.DataFrame({'win_rate':[],'games_played':[]})
    for champ in champs:
        temp = champ_win_rate(matches_df, champ, lane=lane)
        temp = pd.DataFrame(temp, index=[champ])
        win_rate_df = win_rate_df.append(temp)
    return win_rate_df

def all_champ_all_lanes_win_rates(matches_df):
    df = pd.DataFrame()
    lanes = dc.get_lanes_positions()
    for lane in lanes:
        temp = all_champ_win_rates(matches_df, lane=lane)
        df[lane + '_win_rate'] = temp['win_rate']
        df[lane + '_games_played'] = temp['games_played']
    return df


def paired_win_rate(matches_df, lane1, lane2, lane1_champ, lane2_champ):
    """Calculate the win rate of a specified pair of champions on the same team.

    Returns a dict with two keys: 'win_rate' and 'appearances' """
    blue_appearances = matches_df[np.logical_and(matches_df['100_' + lane1] == lane1_champ,
                                                 matches_df['100_' + lane2] == lane2_champ)]
    red_appearances = matches_df[np.logical_and(matches_df['200_' + lane1] == lane1_champ,
                                                matches_df['200_' + lane2] == lane2_champ)]
    tot_appearanaces = blue_appearances.shape[0] + red_appearances.shape[0]

    # Get wins for each side
    blue_wins = np.sum(blue_appearances['team_100_win'])
    red_wins = np.sum(1 - red_appearances['team_100_win'])
    tot_wins = blue_wins + red_wins

    if tot_appearanaces < 1:
        return {'win_rate': 0, 'appearances': 0}
    else:
        return {'win_rate': tot_wins / tot_appearanaces, 'appearances': tot_appearanaces}


def h2h_win_rate(matches_df, lane1, lane2, lane1_champ, lane2_champ):
    blue_appearances = matches_df[np.logical_and(matches_df['100_' + lane1] == lane1_champ,
                                                 matches_df['200_' + lane2] == lane2_champ)]
    red_appearances = matches_df[np.logical_and(matches_df['200_' + lane1] == lane1_champ,
                                                matches_df['200_' + lane2] == lane2_champ)]
    tot_apperanaces = blue_appearances.shape[0] + red_appearances.shape[0]

    # Get wins for each side
    blue_wins = np.sum(blue_appearances['team_100_win'])
    red_wins = np.sum(1 - red_appearances['team_100_win'])
    tot_wins = blue_wins + red_wins
    return tot_apperanaces / tot_wins


def all_champ_pairs_fixed_lane(matches_df, lane1, lane2):
    """Create a DataFrame with every pair of champs as the key and their win rates in lane1 and lane2."""
    champs = dc.get_champs_four_letters()
    win_rate_df = pd.DataFrame({'win_rate': [], 'games_played': []})
    for champ1 in champs:
        for champ2 in champs:
            temp = paired_win_rate(matches_df, lane1, lane2, champ1, champ2)
            temp = pd.DataFrame(temp, index=[champ1 + '_' + champ2])
            win_rate_df = win_rate_df.append(temp)
    return win_rate_df
