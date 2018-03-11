# There are 10 pairs of lanes on each team.  We get the win rate for each pair
# For each lane pair, we need a table with 3 columns: lane1 champ, lane2 champ, win rate
# Need to write a function tht takes in matches_df, lane1 name, lane1 champ, lane2 name,
# lane2 champ, and outputs their win rate
import numpy as np

def paired_win_rate(matches_df, lane1, lane2, lane1_champ, lane2_champ):
    """  """
    blue_appearances = matches_df[np.logical_and(matches_df['100_' + lane1] == lane1_champ, matches_df['100_' + lane2] == lane2_champ)]
    red_appearances = matches_df[np.logical_and(matches_df['200_' + lane1] == lane1_champ, matches_df['200_' + lane2] == lane2_champ)]
    tot_appearanaces = blue_appearances.shape[0] + red_appearances.shape[0]

    # Get wins for each side
    blue_wins = np.sum(blue_appearances['team_100_win'])
    red_wins = np.sum(1 - red_appearances['team_100_win'])
    tot_wins = blue_wins + red_wins
    return({'win_rate': tot_wins / tot_appearanaces, 'occurences':tot_appearanaces})

def h2h_win_rate(matches_df, lane1, lane2, lane1_champ, lane2_champ):
    blue_appearances = matches_df[np.logical_and(matches_df['100_' + lane1] == lane1_champ, matches_df['200_' + lane2] == lane2_champ)]
    red_appearances = matches_df[np.logical_and(matches_df['200_' + lane1] == lane1_champ, matches_df['200_' + lane2] == lane2_champ)]
    tot_apperanaces = blue_appearances.shape[0] + red_appearances.shape[0]

    # Get wins for each side
    blue_wins = np.sum(blue_appearances['team_100_win'])
    red_wins = np.sum(1 - red_appearances['team_100_win'])
    tot_wins = blue_wins + red_wins
    return(tot_apperanaces / tot_wins)

def all_champ_pairs_fixed_lane(matches_df, lane1, lane2):