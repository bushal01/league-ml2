import numpy as np
import pandas as pd
import os
import dotenv


project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
dotenv_path = os.path.join(project_dir, '.env')
dotenv.load_dotenv(dotenv_path)

def ks_gini(loss, score):
    """Calculate KS and Gini score"""
    df = pd.DataFrame({'loss':loss, 'score':score})
    df = df.sort_values(by=['score'])

    iden = np.ones(df.shape[0])
    iden = np.cumsum(iden) / df.shape[0]

    cumsum_score = np.cumsum(df['loss']) / np.sum(df['loss'])

    ks = np.max(np.abs(iden - cumsum_score))
    gini = np.sum(iden - cumsum_score) / df.shape[0]
    return {'ks': ks, 'gini': gini}


def gains_chart(loss, score):
    """Show gains chart of binned scores along with KS and Gini."""

    return


def mse(loss, score):
    """Calculate the mean squared error."""
    return np.mean(np.power(loss - score, 2))


def correct_prediction_rate(loss, score, threshold=0.5):
    """Calculate the percentage of games correctly predicted."""
    correct_blue_team_win = np.sum(np.logical_and(score >= threshold, loss == 1))
    correct_red_team_win = np.sum(np.logical_and(score < threshold, loss == 0))
    return (correct_blue_team_win + correct_red_team_win)/len(loss)


def best_threshold(loss, score, step_size = .01):
    """Calculate the best threshold to use for binary prediction."""
    best_thresh = 0
    best_score = 0
    for i in np.arange(0, 1, step_size):
        current_score = correct_prediction_rate(loss, score, i)
        if current_score > best_score:
            best_score = current_score
            best_thresh = i
    return {'threshold': best_thresh, 'prediction_rate': best_score}


def record_gbm_performance(description='', learning_rate='', max_depth='', n_estimators='', min_samples_split='',
                           min_samples_leaf='',  random_state='', best_iter='', num_vars='', train_rows='',
                           valid_rows='', correct_pred_train='', correct_pred_validation='', ks_train='', ks_valid='',
                           gini_train='', gini_valid='', mse_train='', mse_valid='', train_time='',
                           file=os.getenv('MODEL_PERF_DATA_DIR') + 'gbm_eval.csv'):
    results = pd.DataFrame(index=np.arange(0,1),
                           columns=['description', 'learning_rate', 'max_depth', 'n_estimators', 'min_samples_split',
                                    'min_samples_leaf', 'random_state', 'best_iter', 'num_vars', 'train_rows',
                                    'valid_rows', 'correct_pred_train', 'correct_pred_validation', 'ks_train',
                                    'ks_valid', 'gini_train', 'gini_valid', 'mse_train', 'mse_valid', 'train_time'])
    results.iloc[0,:] = [description, learning_rate, max_depth, n_estimators, min_samples_split, min_samples_leaf,
                         random_state, best_iter, num_vars, train_rows, valid_rows, correct_pred_train,
                         correct_pred_validation, ks_train, ks_valid, gini_train, gini_valid, mse_train, mse_valid,
                         train_time]
    if os.path.isfile(file):
        results.to_csv(file, mode='a')
    else:
        results.to_csv(file, mode='w')
    return results


def gbm_best_iter(model, validation, actual, evaluation_metric='ks'):
    """Determines value of n_estimators that performed the best in tree ensemble model."""
    scores = []
    if evaluation_metric == 'mse':
        for x in model.staged_predict(validation):
            scores = scores.append(mse(actual, x))
            best_iter = np.argmax(scores) + 1
    else:
        for x in model.staged_predict(validation):
            ks = ks_gini(actual, x)['ks']
            scores = scores + [ks]
            best_iter = np.argmax(scores) + 1
    return {'scores': scores, 'best_iter': best_iter}