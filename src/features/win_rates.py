import numpy as np
import pandas as pd
import data_mining.data_constants as dc


def get_champ_win_rate(champ, matches_df):
    """ Calculates the win rate of a single champion """
    teams_lanes_roles = dc.getTeamsLanesRoles()
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
        return [np.nan, tot_appearances]
    else:
        return {'win_rate': num_wins / tot_appearances, 'games_played': tot_appearances}


def get_all_champ_win_rate(matches_df):
    """ Returns a DataFrame of each champion and their associated win rate """
    champs = dc.getChampsFourLetters()
    win_rate_dict = {}
    for i in champs:
        win_rate_dict[i] = get_champ_win_rate(i, matches_df)['win_rate']
    win_rate_df = pd.DataFrame(win_rate_dict)
    return win_rate_df


def paired_win_rate(matches_df, lane1, lane2, lane1_champ, lane2_champ):
    """ Returns the win rate of this champion pair """
    blue_appearances = matches_df[np.logical_and(matches_df['100_' + lane1] == lane1_champ,
                                                 matches_df['100_' + lane2] == lane2_champ)]
    red_appearances = matches_df[np.logical_and(matches_df['200_' + lane1] == lane1_champ,
                                                matches_df['200_' + lane2] == lane2_champ)]
    tot_appearanaces = blue_appearances.shape[0] + red_appearances.shape[0]

    # Get wins for each side
    blue_wins = np.sum(blue_appearances['team_100_win'])
    red_wins = np.sum(1 - red_appearances['team_100_win'])
    tot_wins = blue_wins + red_wins
    return {'win_rate': tot_wins / tot_appearanaces, 'occurences': tot_appearanaces}


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
    return lane1, lane2, matches_df
