# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 12:31:25 2017

Build the training set as well as wrapper functions to get the training/valid/test set.

@author: bushal01
"""

import pandas as pd
import dotenv
import sys
import features.win_rates as wr
import data_constants as dc
indiv_win_rate_file = '../data/win_rates/all_champ_all_lanes_win_rates.csv'
paired_win_rate_file = '../data/win_rates/all_pairs_all_lanes_win_rates.csv'
h2h_win_rate_file = '../data/win_rates/all_h2h_all_lanes_win_rates.csv'

def build_win_rates(indiv_win_rates=True, paired_win_rates=True, h2h_win_rates=True):
    if indiv_win_rates:
        wr.all_champ_all_lanes_win_rates(raw_data, indiv_win_rate_file)
    if paired_win_rates:
        wr.all_champ_pairs_all_lanes(raw_data, paired_win_rate_file)
    if h2h_win_rates:
        wr.all_h2h_pairs_all_lanes(raw_data, h2h_win_rate_file)


def main():
    # Load match data
    data = pd.read_csv(os.getenv('MINED_DATA_DIR') + 'processed_match_data.csv')

    # Build win rates (optional)
    if len(sys.argv) > 1:
        indiv_wr_boolean = sys.argv[1]
        if len(sys.argv) > 2:
            paired_wr_boolean = sys.argv[2]
            if len(sys.argv) > 3:
                h2h_wr_boolean = sys.argv[3]

    # Load win rates
    indiv_win_rates = pd.read_csv(indiv_win_rate_file)
    paired_win_rates = pd.read_csv(paired_win_rate_file)
    h2h_win_rates = pd.read_csv(h2h_win_rate_file)

    indiv_win_rates = indiv_win_rates.rename({'Unnamed: 0':'champ'}, axis='columns')
    paired_win_rates = paired_win_rates.rename({'Unnamed: 0':'champ_pair'}, axis='columns')
    h2h_win_rates = h2h_win_rates.rename({'Unnamed: 0':'champ_pair'}, axis='columns')

    #### Win rate significance ####
    # Filter out low games played win rates with win_rates.win_rate_significance()

    #### Join win rates ####
    teams_lanes_roles = dc.get_teams_lanes_roles()
    teams = dc.get_teams()
    lanes_roles = dc.get_lanes_roles()

    # Join individ win rates
    for tlr in teams_lanes_roles:
        # want to take index of indiv win rates and a single column of it
        data = pd.merge(data, indiv_win_rates[['champ', tlr[4:] + '_win_rate']], how='left',
                        left_on=tlr, right_on='champ')
        data = data.rename({tlr[4:] + '_win_rate': tlr + '_wr'}, axis=1)
        data = data.drop(['champ'], axis=1)

    # Join paired win rates
    teams = dc.get_teams()
    for lr1 in lanes_roles:
        print(lr1)
        for lr2 in lanes_roles:
            if lr1 != lr2:
                for team in teams:
                    # create join key
                    tlr1 = team + '_' + lr1
                    tlr2 = team + '_' + lr2
                    data[tlr1 + '_' + tlr2] = data[tlr1].str.cat(data[tlr2], sep='_')
                    data = pd.merge(data, paired_win_rates[['champ_pair', tlr1[4:] + '_' + tlr2[4:] + '_win_rate']],
                                    how='left', left_on=tlr1 + '_' + tlr2, right_index=True)
                    data = data.rename({tlr1[4:] + '_' + tlr2[4:] + '_win_rate': tlr1 + '_' + tlr2[4:] + '_wr'}, axis=1)
                    data = data.drop(['champ_pair', tlr1 + '_' + tlr2], axis=1)



    # Get rid of categorical columns

    # Train, validation, test split


if __name__ == 'main':
    # sys.argv[i] are booleans where
    # sys.argv[1] = build individual win rates
    # sys.argv[2] = build paired win rates
    # sys.argv[3] = build head to head win rates
    main()
