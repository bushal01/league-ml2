library(dplyr)
library(ggplot2)

#### Script with various model performance functions ####
ks_gini = function(actual, pred) {
  # Order them
  actual = actual[order(pred)]
  pred = pred[order(pred)]

  n = length(actual)
  tot = sum(actual)
  ident_line = integer(n) + 1/(n)
  ident_line = cumsum(ident_line)
  
  pred_line = cumsum(actual) / tot

  ks = max(abs(ident_line - pred_line))
  gini = sum((ident_line - pred_line)) / n
  
  actual = actual[order(actual)]
  actual_line = cumsum(actual) / tot
  max_ks = max(abs(ident_line - actual_line))
  max_gini = sum((ident_line - actual_line)) / n
  temp_df = data.frame('xaxis' = (1:n) / n,
                       'values' = c(ident_line, pred_line, actual_line),
                       'data_source' = c(rep('ident', n), rep('pred',n), rep('actual',n)))
  #p = ggplot(temp_df, aes(x = xaxis, y = values, group = data_source)) +
  #geom_line(aes(color = data_source))
  #print(p)
  
  return(setNames(c(ks, gini, max_ks, max_gini), c('ks','gini','max_possible_ks','max_possible_gini')))
}

precision_recall = function(actual, pred, threshold = 0) {
  true_positives = sum(actual == 1 & pred > threshold)
  false_positives = sum(actual == 0 & pred > threshold)
  true_negatives = sum(actual == 0 & pred < threshold)
  false_negatives = sum(actual == 0 & pred < threshold)
  recall = true_positives / (true_positives + false_positives)
  precision = true_positives / (true_positives + false_negatives)
  return(setNames(c(precision,recall), c('precision','recall')))
}

rank_comparison_auc <- function(labels, scores){
  score_order <- order(scores, decreasing=TRUE)
  labels <- as.logical(labels[score_order])
  scores <- scores[score_order]
  pos_scores <- scores[labels]
  neg_scores <- scores[!labels]
  n_pos <- sum(labels)
  n_neg <- sum(!labels)
  M <- outer(sum(labels):1, 1:sum(!labels), 
             function(i, j) (1 + sign(pos_scores[i] - neg_scores[j]))/2)
  
  AUC <- mean (M)
  return(AUC)
}
# 
#   # Break up into bins
#   n = length(actual)
#   breaks = quantile(pred, seq(from = 0, to = 1, by = 1 / num_bins) )
#   bins = integer(n)
#   for(i in 1:num_bins) {
#     bins[pred > breaks[i] & pred <= breaks[i+1]] = i
#   }
#   
#   data.frame()
#   # Calculate averages for each bin
#   avgs = group_by
#   
#   # Calculate KS and Gini
# }