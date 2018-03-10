# -*- coding: utf-8 -*-
"""
Created on Sat Mar  3 17:38:17 2018

GBM with no extra attributes added for initial testing

@author: Albert
"""

import pandas as pd
import sklearn.ensemble

import data_mining.data_constants as dc

TRAIN_SET = '../../data/raw/init_matches_3_3_2018.csv'

# Load dataset
train = pd.read_csv(TRAIN_SET)
attributes_for_modeling = dc.getTeamsLanesRoles()

# Train model
sklearn.ensemble.GradientBoostingClassifier().fit(train[attributes_for_modeling], train['team_100_win'])

# Evaluate model

