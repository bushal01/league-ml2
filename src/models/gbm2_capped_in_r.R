# gbm2
library(gbm)
library(data.table)
library(stringr)

setwd("C:/Users/Albert/Desktop/Programming/league-ml2/src/models")
source('../model_evaluation/model_performance_functions.R')
RESULTS_OUTPUT = '../../data/model_performance/gbm2_testr.csv'
PARAMS_LM_OUT = '../../data/model_performance/gbm2_testr.txt'

x_train = fread('../../data/interim/x_train.csv', data.table=FALSE, nrows = 50000)
x_validation = fread('../../data/interim/x_validation.csv', data.table=FALSE)
y_train = fread('../../data/interim/y_train.csv', data.table=FALSE, nrows = 50000)
y_validation = fread('../../data/interim/y_validation.csv', data.table=FALSE)

names(x_train) = str_replace_all(names(x_train), '100', 'blue')
names(x_train) = str_replace_all(names(x_train), '200', 'red')
names(x_validation) = str_replace_all(names(x_validation), '100', 'blue')
names(x_validation) = str_replace_all(names(x_validation), '200', 'red')
names(y_train) = str_replace_all(names(y_train), '100', 'blue')
names(y_train) = str_replace_all(names(y_train), '200', 'red')
names(y_validation) = str_replace_all(names(y_validation), '100', 'blue')
names(y_validation) = str_replace_all(names(y_validation), '200', 'red')

y_train = y_train$V2
y_validation = y_validation$V2

x_train$y = y_train
x_validation$y = y_validation

x_train$V1 = NULL
x_validation$V1 = NULL

interaction_depth = c(5)
shrinkage_rate = c(.1)
bag_fraction = c(1.0)
cv_folds = c(5)
num_trees = c(500)
train_size = c(1:5) * 10000

param_df = setNames(expand.grid(interaction_depth, shrinkage_rate, bag_fraction, cv_folds,num_trees,train_size),
                    c('interaction_depth','shrinkage_rate','bag_fraction','cv_folds','num_trees','train_size'))

results_df = setNames(data.frame(matrix(nrow = 0, ncol = 20)),
                      c('inter_dpth','shrink','bag_fr','cv_fo','n.trees','train_size','best.iter','ks_train','gini_train',
                        'ks_valid','gini_valid','precision_train','recall_train','precision_valid',
                        'recall_valid','auc_train','auc_valid','train_time','train_size','valid_size'))

basic_formula = as.formula("y ~ .")

for(i in 1:nrow(param_df)) {
  start_time = Sys.time()
  print(param_df[i,])
  #### Train model ####
  gbm2_capped = gbm(as.formula('y ~ .'),
                    distribution = 'bernoulli',
                    data = x_train[1:param_df[i,'train_size'],],
                    interaction.depth = param_df[i,'interaction_depth'],
                    shrinkage = param_df[i,'shrinkage_rate'],
                    bag.fraction = param_df[i,'bag_fraction'],
                    train.fraction = 1.0,
                    n.trees = param_df[i,'num_trees'],
                    verbose = TRUE,
                    cv.folds = param_df[i,'cv_folds'])
  
  #### Evaluate Model ####
  best.iter = gbm.perf(gbm2_capped, method = 'cv')
  train_pred = predict.gbm(gbm2_capped, x_train, best.iter)
  valid_pred = predict.gbm(gbm2_capped, x_validation, best.iter)
  ks_gini_train = ks_gini(x_train$y, train_pred)
  ks_gini_valid = ks_gini(x_validation$y, valid_pred)
  precision_recall_train = precision_recall(x_train$y, train_pred) 
  precision_valid = precision_recall(x_validation$y, valid_pred)
  #auc_train = rank_comparison_auc(train$team_100_win, train_pred)
  #  auc_valid = rank_comparison_auc(validation$team_blue_win, valid_pred)
  end_time = Sys.time()
  total_time = end_time - start_time
  cur_row = nrow(results_df)+1
  results_df[cur_row,] = c(as.numeric(param_df[i,]), 
                           best.iter, 
                           ks_gini_train[1:2], 
                           ks_gini_valid[1:2],
                           precision_recall_train,
                           precision_valid,
                           'NA',
                           'NA',
                           total_time,
                           nrow(x_train),
                           nrow(x_validation))
  print(results_df)
  # Write results as well as gbm parameters to a file with append = true to save a running tally of what ive done before
  write.table(results_df[cur_row,], RESULTS_OUTPUT, sep = ',', 
              quote = FALSE, row.names = FALSE, col.names = (i == 1), append = TRUE)
}
#write.csv(results_df, '../../data/model_performance/gbm1_noattributes_75k.csv', 
#          quote = FALSE, row.names = FALSE)

for(i in c('inter_dpth','shrink','bag_fr','cv_fo','n.trees','best.iter','ks_valid')) {
  results_df[[i]] = as.numeric(results_df[[i]])
}