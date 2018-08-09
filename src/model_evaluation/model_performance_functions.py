import numpy as np
import pandas as pd
import os
import dotenv
import matplotlib.pyplot as plt


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
    gini = 2 * np.sum(iden - cumsum_score) / df.shape[0]
    return {'ks': ks, 'gini': gini}


def lorenz_curve(loss_pred, score_pred, loss_valid, score_valid, title='Lorenz Curve'):
    loss_pred = pd.Series(loss_pred)
    score_pred = pd.Series(score_pred)

    n = len(loss_pred)
    df = pd.concat([loss_pred, score_pred], axis=1)
    df.columns =['loss_pred', 'score_pred']
    df = df.sort_values(by='score_pred')
    total_loss_pred = np.sum(df['loss_pred'])
    cum_loss_pred = np.cumsum(df['loss_pred']) / total_loss_pred

    base_line = np.cumsum(np.ones(n)) / n

    best_line = np.cumsum(df['loss_pred'].sort_values()) / total_loss_pred

    plt.plot(np.arange(n)/n, cum_loss_pred, label='Train')
    plt.plot(np.arange(n)/n, base_line, label='Base Line')
    plt.plot(np.arange(n)/n, best_line, label='Perfect Predictions')

    loss_valid = pd.Series(loss_valid)
    score_valid = pd.Series(score_valid)

    n = len(loss_valid)
    df = pd.concat([loss_valid, score_valid], axis=1)
    df.columns =['loss_valid', 'score_valid']
    df = df.sort_values(by='score_valid')
    total_loss_valid = np.sum(df['loss_valid'])
    cum_loss_valid = np.cumsum(df['loss_valid']) / total_loss_valid

    plt.plot(np.arange(n)/n, cum_loss_valid, label='Validation')

    plt.xlabel('% of Records')
    plt.ylabel('% of Total Actual')

    train_gini = "{:.3f}".format(ks_gini(loss_pred, score_pred)['gini'])
    valid_gini = "{:.3f}".format(ks_gini(loss_valid, score_valid)['gini'])

    plt.suptitle(title)
    plt.title('Train gini: ' + train_gini + ', Valid gini: ' + valid_gini)
    plt.legend(bbox_to_anchor=(1.15, 1), loc=2, borderaxespad=0.)
    plt.show()
    plt.close()


def gains_chart(loss, score, num_bins=10, title='Gains Chart', return_table=True, include_scores=True):
    """Show gains chart of binned scores along with KS and Gini."""
    loss = pd.Series(loss)




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
    return {'threshold': best_thresh, 'accuracy': best_score}


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
        results.to_csv(file, mode='a', header=False)
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