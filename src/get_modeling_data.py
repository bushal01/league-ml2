import pandas as pd

train_file = '../data/processed/train.csv'
validation_file = '../data/processed/validation.csv'
test_file = '../data/processed/test.csv'


def get_train():
    train = pd.read_csv(train_file, index_col=[0])
    return train


def get_validation():
    validation = pd.read_csv(validation_file, index_col=[0])
    return validation


def get_test():
    test = pd.read_csv(test_file, index_col=[0])
    return test


def get_non_modeling_cols():
    return ['match_id', 'game_version', 'queue_id', 'game_duration',
            '100_TOP_SOLO', '100_JUNGLE_NONE', '100_MIDDLE_SOLO', '100_BOTTOM_DUO_CARRY', '100_BOTTOM_DUO_SUPPORT',
            '200_TOP_SOLO', '200_JUNGLE_NONE', '200_MIDDLE_SOLO', '200_BOTTOM_DUO_CARRY', '200_BOTTOM_DUO_SUPPORT']
