import pandas as pd
import dotenv
import os

project_dir = os.path.join(os.path.dirname(__file__), os.pardir)
dotenv_path = os.path.join(project_dir, '.env')
dotenv.load_dotenv(dotenv_path)
train_file = os.getenv('DATA_DIR') + 'processed\\train_v2.csv'
validation_file = os.getenv('DATA_DIR') + 'processed\\validation_v2.csv'
test_file = os.getenv('DATA_DIR') + 'processed\\test_v2.csv'
all_data_file = os.getenv('MINED_DATA_DIR') + 'processed_match_data.csv'

def get_train():
    train = pd.read_csv(train_file, index_col=[0])
    return train


def get_validation():
    validation = pd.read_csv(validation_file, index_col=[0])
    return validation


def get_test():
    test = pd.read_csv(test_file, index_col=[0])
    return test


def get_all_data():
    data = pd.read_csv(all_data_file)
    return data

def get_non_modeling_cols():
    return ['match_id', 'game_version', 'queue_id', 'game_duration',
            '100_TOP_SOLO', '100_JUNGLE_NONE', '100_MIDDLE_SOLO', '100_BOTTOM_DUO_CARRY', '100_BOTTOM_DUO_SUPPORT',
            '200_TOP_SOLO', '200_JUNGLE_NONE', '200_MIDDLE_SOLO', '200_BOTTOM_DUO_CARRY', '200_BOTTOM_DUO_SUPPORT']
