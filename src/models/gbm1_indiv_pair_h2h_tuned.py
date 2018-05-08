import sklearn.ensemble
import get_modeling_data
import model_evaluation.model_performance_functions as mpf
import time
import dotenv
import os


if __name__ == '__main__':
    project_dir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
else:
    project_dir = os.path.join(os.getcwd(), os.pardir)
dotenv_path = os.path.join(project_dir, '.env')
dotenv.load_dotenv(dotenv_path)

train = get_modeling_data.get_train()
validation = get_modeling_data.get_validation()
train = train.fillna(0)
validation = validation.fillna(0)
non_modeling_cols = get_modeling_data.get_non_modeling_cols()
X_train = train.drop(non_modeling_cols + ['team_100_win'], axis=1)
Y_train = train['team_100_win']
X_validation = validation.drop(non_modeling_cols + ['team_100_win'], axis=1)
Y_validation = validation['team_100_win']

learning_rates = [0.01]
n_estimators = [1500]
min_samples_splits = [100, 200, 500]
max_depths = [2, 3, 5, 7]

for lr in learning_rates:
    for mss in min_samples_splits:
        for md in max_depths:

            gbm_params = {'learning_rate': lr,
                          'n_estimators': 1500,
                          'min_samples_split': mss,
                          'min_samples_leaf': 50,
                          'max_depth': md,
                          'random_state': 414}
            print(gbm_params)
            start_time = time.time()
            model = sklearn.ensemble.GradientBoostingClassifier(**gbm_params)
            model_fit = model.fit(X_train, Y_train)
            n_est_performance = mpf.gbm_best_iter(model_fit, X_validation, Y_validation)

            # Get training and validation predictions using best iteration
            ctr = 1
            for prediction in model_fit.staged_predict(X_train):
                if ctr == n_est_performance['best_iter']:
                    train_pred = prediction
                ctr = ctr + 1
            ctr = 1
            for prediction in model_fit.staged_predict(X_validation):
                if ctr == n_est_performance['best_iter']:
                    validation_pred = prediction
                ctr = ctr + 1

            train_time = time.time() - start_time

            ks_gini_train = mpf.ks_gini(Y_train, train_pred)
            ks_gini_validation = mpf.ks_gini(Y_validation, validation_pred)
            correct_pred_train = mpf.correct_prediction_rate(Y_train, train_pred)
            correct_pred_validation = mpf.correct_prediction_rate(Y_validation, validation_pred)

            model_performance = mpf.record_gbm_performance(description='GBM,Indiv,paired,h2h,230k,best_iteration',
                                       **gbm_params, best_iter=n_est_performance['best_iter'], num_vars=X_train.shape[1],
                                       train_rows=X_train.shape[0], valid_rows=X_validation.shape[0],
                                       correct_pred_train=correct_pred_train, correct_pred_validation=correct_pred_validation,
                                       ks_train=ks_gini_train['ks'], ks_valid=ks_gini_validation['ks'],
                                       gini_train=ks_gini_train['gini'], gini_valid=ks_gini_validation['gini'],
                                       mse_train=mpf.mse(Y_train, train_pred), mse_valid=mpf.mse(Y_validation, validation_pred),
                                       train_time=train_time, file=os.getenv('DATA_DIR') + 'model_performance/gbm_eval.csv')
            print(model_performance)