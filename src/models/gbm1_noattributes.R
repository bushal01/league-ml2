#### GBM1 No extra attributes ####
# Author: Albert Bush
# Date: 4 March 2018
# An initial GBM to get a rough sketch of what will be possible
# in this modeling process.  The models will mostly be built in R
# due to scikitlearn not having native support for categorical
# variables in its models.  

# Load packages
library(gbm)
library(data.table)
library(bit64)
library(dplyr)

#### Load training set ####
setwd("C:/Users/Albert/Desktop/Programming/league-ml2/src/models")
source('../model_evaluation/model_performance_functions.R')
ALL_MATCHES = '../../data/raw/matches_100k_3_10_2018.csv'
all_data = fread(ALL_MATCHES, data.table = FALSE)

#### Preprocess to prep for input to GBM ####
# Specify attributes to use in model, slim the training set,
# rename attributes (100_ is not valid), and convert to factors
attributes_for_modeling = c('100_TOP_SOLO',
                            '100_JUNGLE_NONE',
                            '100_MIDDLE_SOLO',
                            '100_BOTTOM_DUO_CARRY',
                            '100_BOTTOM_DUO_SUPPORT',
                            '200_TOP_SOLO',
                            '200_JUNGLE_NONE',
                            '200_MIDDLE_SOLO',
                            '200_BOTTOM_DUO_CARRY',
                            '200_BOTTOM_DUO_SUPPORT')

all_data = all_data[ ,c('team_100_win', attributes_for_modeling)]

all_data = rename(all_data, blue_top = '100_TOP_SOLO',
               blue_jg = '100_JUNGLE_NONE',
               blue_mid = '100_MIDDLE_SOLO',
               blue_adc = '100_BOTTOM_DUO_CARRY',
               blue_supp = '100_BOTTOM_DUO_SUPPORT',
               red_top = '200_TOP_SOLO',
               red_jg = '200_JUNGLE_NONE',
               red_mid = '200_MIDDLE_SOLO',
               red_adc = '200_BOTTOM_DUO_CARRY',
               red_supp = '200_BOTTOM_DUO_SUPPORT')

attributes_for_modeling = names(all_data)[2:length(all_data)]

# Create formula and convert columns to factors
basic_formula = 'team_100_win ~ '
for(attr in attributes_for_modeling) {
  basic_formula = paste0(basic_formula, attr, ' + ')
  all_data[[attr]] = as.factor(all_data[[attr]])
}
set.seed(1)
train_recs = sample(1:nrow(all_data), .8 * nrow(all_data))
train = all_data[train_recs,]
validation = all_data[!(1:nrow(all_data) %in% train_recs),]

# Get rid of extra + at the end
basic_formula = substr(basic_formula, 1, nchar(basic_formula) - 3)
basic_formula = as.formula(basic_formula)

interaction_depth = c(1,2,4,6,8,10)
shrinkage_rate = c(.1, .05, .01)
bag_fraction = c(.3, .6, .9)
cv_folds = c(2,5)
num_trees = c(1000)

param_df = setNames(expand.grid(interaction_depth, shrinkage_rate, bag_fraction, cv_folds,num_trees),
                    c('interaction_depth','shrinkage_rate','bag_fraction','cv_folds','num_trees'))

results_df = setNames(data.frame(matrix(nrow = 0, ncol = 19)),
                      c('inter_dpth','shrink','bag_fr','cv_fo','n.trees','best.iter','ks_train','gini_train',
                        'ks_valid','gini_valid','precision_train','recall_train','precision_valid',
                        'recall_valid','auc_train','auc_valid','train_time','train_size','valid_size'))

for(i in 1:nrow(param_df)) {
  start_time = Sys.time()
  print(param_df[i,])
  #### Train model ####
  gbm1_noattr = gbm(basic_formula,
                    distribution = 'bernoulli',
                    data = train,
                    interaction.depth = param_df[i,'interaction_depth'],
                    shrinkage = param_df[i,'shrinkage_rate'],
                    bag.fraction = param_df[i,'bag_fraction'],
                    train.fraction = 1.0,
                    n.trees = param_df[i,'num_trees'],
                    verbose = TRUE,
                    cv.folds = param_df[i,'cv_folds'])
  
  #### Evaluate Model ####
  best.iter = gbm.perf(gbm1_noattr, method = 'cv')
  train_pred = predict.gbm(gbm1_noattr, train, best.iter)
  valid_pred = predict.gbm(gbm1_noattr, validation, best.iter)
  ks_gini_train = ks_gini(train$team_100_win, train_pred)
  ks_gini_valid = ks_gini(validation$team_100_win, valid_pred)
  precision_recall_train = precision_recall(train$team_100_win, train_pred) 
  precision_valid = precision_recall(validation$team_100_win, valid_pred)
  #auc_train = rank_comparison_auc(train$team_100_win, train_pred)
  auc_valid = rank_comparison_auc(validation$team_100_win, valid_pred)
  end_time = Sys.time()
  total_time = end_time - start_time
  results_df[i,] = c(as.numeric(param_df[i,]), 
                     best.iter, 
                     ks_gini_train[1:2], 
                     ks_gini_valid[1:2],
                     precision_recall_train,
                     precision_valid,
                     'NA',
                     auc_valid,
                     total_time,
                     nrow(train),
                     nrow(validation))
  print(results_df[i,])
  # Write results as well as gbm parameters to a file with append = true to save a running tally of what ive done before
    write.csv(results_df[i,], '../../data/model_performance/gbm1_noattributes_75k.csv', 
              quote = FALSE, row.names = FALSE, col.names = (i == 1), append = TRUE)
}
#write.csv(results_df, '../../data/model_performance/gbm1_noattributes_75k.csv', 
#          quote = FALSE, row.names = FALSE)

for(i in c('inter_dpth','shrink','bag_fr','cv_fo','n.trees','best.iter','ks_valid')) {
  results_df[[i]] = as.numeric(results_df[[i]])
}

lm_results_analysis = lm(ks_valid ~ inter_dpth + shrink +	bag_fr + cv_fo + n.trees + best.iter, results_df)
print(summary(lm_results_analysis))
# higher bag fraction, lower inter depth, lower shrinkage