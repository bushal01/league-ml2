# -*- coding: utf-8 -*-
"""
Created on Sat Sep 30 12:31:25 2017

Build the training set as well as wrapper functions to get the training/valid/test set.

@author: bushal01
"""

import pandas as pd
import os
import numpy as np
import sys
import features.win_rates as wr
import data_constants as dc


indiv_win_rate_file = '../data/win_rates/all_champ_all_lanes_win_rates.csv'
paired_win_rate_file = '../data/win_rates/all_pairs_all_lanes_w_apps.csv'
h2h_win_rate_file = '../data/win_rates/all_h2h_all_lanes_w_apps.csv'
train_file = '../data/processed/train_v3.csv'
validation_file = '../data/processed/validation_v3.csv'
test_file = '../data/processed/test_v3.csv'


def build_win_rates(df, indiv_win_rates=True, paired_win_rates=True, h2h_win_rates=True):
    if indiv_win_rates:
        wr.all_champ_all_lanes_win_rates(df, indiv_win_rate_file)
    if paired_win_rates:
        wr.all_champ_pairs_all_lanes(df, paired_win_rate_file)
    if h2h_win_rates:
        wr.all_h2h_pairs_all_lanes(df, h2h_win_rate_file)


def main():
    # Load match data
    data = pd.read_csv(os.getenv('MINED_DATA_DIR') + 'processed_match_data.csv')

    # Train, validation, test split
    train = data.sample(int(.6 * data.shape[0]), random_state=410)
    validation = data[~data['match_id'].isin(train['match_id'])].sample(int(.2 * data.shape[0]), random_state=411)
    test = data[~data['match_id'].isin(pd.concat([train['match_id'],
                                                  validation['match_id']], axis=0, ignore_index=True))]

    # Build win rates (optional)
#    if len(sys.argv) > 1:
#        indiv_wr_boolean = sys.argv[1]
#        print('Fire 1')
#        if len(sys.argv) > 2:
#            paired_wr_boolean = sys.argv[2]
#            print('Fire 2')
#            if len(sys.argv) > 3:
#                h2h_wr_boolean = sys.argv[3]
#                print('Fire 3')
    #build_win_rates(train, indiv_wr_boolean, paired_wr_boolean, h2h_wr_boolean)

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
#    teams = dc.get_teams()
    lanes_roles = dc.get_lanes_roles()

    # Join individ win rates
    for tlr in teams_lanes_roles:
        # want to take index of indiv win rates and a single column of it
        data = pd.merge(data, indiv_win_rates[['champ', tlr[4:] + '_win_rate', tlr[4:] + '_games_played']], how='left',
                        left_on=tlr, right_on='champ')
        data = data.rename({tlr[4:] + '_win_rate': tlr + '_wr',
                            tlr[4:] + '_games_played': tlr + '_gp'}, axis=1)
        data = data.drop(['champ'], axis=1)

    # Join paired win rates
    teams = dc.get_teams()
    for lr1 in lanes_roles:
        print(lr1)
        for lr2 in lanes_roles:
            if lr1 != lr2:
                t2 = lr1 + '_' + lr2
                paired_win_rates[t2 + '_wins'] = paired_win_rates[t2 + '_rw'] + paired_win_rates[t2 + '_bw']
                for team in teams:
                    # create join key
                    tlr1 = team + '_' + lr1
                    tlr2 = team + '_' + lr2
                    t4 = tlr1[4:] + '_' + tlr2[4:]
                    t41 = tlr1 + '_' + tlr2[4:]
                    data[tlr1 + '_' + tlr2] = data[tlr1].str.cat(data[tlr2], sep='_')
                    data = pd.merge(data, paired_win_rates[['champ_pair',
                                                            t4 + '_wr',
                                                            t4 + '_gp',
                                                            t4 + '_wins']],
                                    how='left', left_on=tlr1 + '_' + tlr2, right_on='champ_pair')
                    data = data.rename({t4 + '_wr': t41 + '_wr',
                                        t4 + '_gp': t41 + '_gp',
                                        t4 + '_wins': t41 + '_wins',}, axis=1)
                    data = data.drop(['champ_pair', tlr1 + '_' + tlr2], axis=1)

    # Join h2h win rates
    for lr1 in lanes_roles:
        print(lr1)
        for lr2 in lanes_roles:
            # create join key
            tlr1 = '100' + '_' + lr1
            tlr2 = '200' + '_' + lr2
            data[tlr1 + '_' + tlr2] = data[tlr1].str.cat(data[tlr2], sep='_')
            data = pd.merge(data, h2h_win_rates[['champ_pair', tlr1[4:] + '_' + tlr2[4:] + '_wr',
                                                 tlr1[4:] + '_' + tlr2[4:] + '_gp',
                                                 tlr1[4:] + '_' + tlr2[4:] + '_wins']],
                            how='left', left_on=tlr1 + '_' + tlr2, right_on='champ_pair')
            data = data.rename({tlr1[4:] + '_' + tlr2[4:] + '_wr': tlr1 + '_' + tlr2 + '_wr',
                                tlr1[4:] + '_' + tlr2[4:] + '_gp': tlr1 + '_' + tlr2 + '_gp',
                                tlr1[4:] + '_' + tlr2[4:] + '_wins': tlr1 + '_' + tlr2 + '_wins'}, axis=1)
            data = data.drop(['champ_pair', tlr1 + '_' + tlr2], axis=1)

    # Drop erroneous rows with '0' as a champ name
    print(data.shape)
    lane_cols = ['100_TOP_SOLO', '100_JUNGLE_NONE', '100_MIDDLE_SOLO', '100_BOTTOM_DUO_CARRY', '100_BOTTOM_DUO_SUPPORT',
                 '200_TOP_SOLO', '200_JUNGLE_NONE', '200_MIDDLE_SOLO', '200_BOTTOM_DUO_CARRY', '200_BOTTOM_DUO_SUPPORT']
    for col in lane_cols:
        data = data[data[col] != '0']
    print(data.shape)

    train = data[data['match_id'].isin(train['match_id'])]
    validation = data[data['match_id'].isin(validation['match_id'])]
    test = data[data['match_id'].isin(test['match_id'])]

    # Adjust the paired win rates to not include that record's game in the calculation
    for lr1 in lanes_roles:
        print(lr1)
        for lr2 in lanes_roles:
            if lr1 != lr2:
                t2 = lr1 + '_' + lr2
                for team in teams:
                    # create join key
                    tlr1 = team + '_' + lr1
                    tlr2 = team + '_' + lr2
                    t41 = tlr1 + '_' + tlr2[4:]
                    if team == '100':
                        train[t41 + '_wins'] = train[t41 + '_wins'] - train['team_100_win']
                    else:
                        train[t41 + '_wins'] = train[t41 + '_wins'] - (1 - train['team_100_win'])
                    train[t41 + '_gp'] = train[t41 + '_gp'] - 1
                    train[t41 + '_gp'] = np.maximum(0, train[t41 + '_gp'])
                    train[t41 + '_wr'] = train[t41 + '_wins'] / train[t41 + '_gp']
                    train[t41 + '_wr'] = np.maximum(0, train[t41 + '_wr'])
                    train[t41 + '_wr'].fillna(0, inplace=True)
#                    validation[t41 + '_wr'] = validation[t41 + '_wins'] / validation[t41 + '_gp']
#                    validation[t41 + '_wr'] = np.maximum(0, validation[t41 + '_wr'])
#                    validation[t41 + '_wr'].fillna(0, inplace=True)
#                    test[t41 + '_wr'] = test[t41 + '_wins'] / test[t41 + '_gp']
#                    test[t41 + '_wr'] = np.maximum(0, test[t41 + '_wr'])
#                    test[t41 + '_wr'].fillna(0, inplace=True)

    # Adjust the paired h2h win rates to not include that record's game in the calculation
    for lr1 in lanes_roles:
        print(lr1)
        for lr2 in lanes_roles:
            tlr1 = '100' + '_' + lr1
            tlr2 = '200' + '_' + lr2
            t12 = tlr1 + '_' + tlr2
            train[t12 + '_wins'] = train[t12 + '_wins'] - train['team_100_win']
            train[t12 + '_gp'] = train[t12 + '_gp'] - 1
            train[t12 + '_wr'] = train[t12 + '_wins'] / train[t12 + '_gp']
            train[t12 + '_wr'] = np.maximum(0, train[t12 + '_wr'])
            train[t12 + '_wr'].fillna(0, inplace=True)

    cols_to_drop = [x for x in train.columns if x[-4:] == 'wins']
    train.drop(cols_to_drop, inplace=True, axis=1)
    validation.drop(cols_to_drop, inplace=True, axis=1)
    test.drop(cols_to_drop, inplace=True, axis=1)

    train.to_csv(train_file)
    validation.to_csv(validation_file)
    test.to_csv(test_file)

if __name__ == '__main__':
    # sys.argv[i] are booleans where
    # sys.argv[1] = build individual win rates
    # sys.argv[2] = build paired win rates
    # sys.argv[3] = build head to head win rates
    main()