from multiprocessing import Pool, cpu_count

import numpy as np
import pandas as pd

import numpy as np


class F1Optimizer():

    def __init__(self):
        pass

    @staticmethod
    def get_expectations(P, pNone=None):
        expectations = []
        P = np.sort(P)[::-1]

        n = np.array(P).shape[0]
        DP_C = np.zeros((n + 2, n + 1))
        if pNone is None:
            pNone = (1.0 - P).prod()

        DP_C[0][0] = 1.0
        for j in range(1, n):
            DP_C[0][j] = (1.0 - P[j - 1]) * DP_C[0, j - 1]

        for i in range(1, n + 1):
            DP_C[i, i] = DP_C[i - 1, i - 1] * P[i - 1]
            for j in range(i + 1, n + 1):
                DP_C[i, j] = P[j - 1] * DP_C[i - 1, j - 1] + (1.0 - P[j - 1]) * DP_C[i, j - 1]

        DP_S = np.zeros((2 * n + 1,))
        DP_SNone = np.zeros((2 * n + 1,))
        for i in range(1, 2 * n + 1):
            DP_S[i] = 1. / (1. * i)
            DP_SNone[i] = 1. / (1. * i + 1)
        for k in range(n + 1)[::-1]:
            f1 = 0
            f1None = 0
            for k1 in range(n + 1):
                f1 += 2 * k1 * DP_C[k1][k] * DP_S[k + k1]
                f1None += 2 * k1 * DP_C[k1][k] * DP_SNone[k + k1]
            for i in range(1, 2 * k - 1):
                DP_S[i] = (1 - P[k - 1]) * DP_S[i] + P[k - 1] * DP_S[i + 1]
                DP_SNone[i] = (1 - P[k - 1]) * DP_SNone[i] + P[k - 1] * DP_SNone[i + 1]
            expectations.append([f1None + 2 * pNone / (2 + k), f1])

        return np.array(expectations[::-1]).T

    @staticmethod
    def maximize_expectation(P, pNone=None):
        expectations = F1Optimizer.get_expectations(P, pNone)

        ix_max = np.unravel_index(expectations.argmax(), expectations.shape)
        max_f1 = expectations[ix_max]

        predNone = True if ix_max[0] == 0 else False
        best_k = ix_max[1]

        return best_k, predNone, max_f1


def select_products(x):
    series = pd.Series()

    true_products = [str(prod) if prod != 0 else 'None' for prod in x['product_id'][x['label'] > 0.5].values]
    true_products = ' '.join(true_products) if true_products else 'None'

    prod_preds_dict = dict(zip(x['product_id'].values, x['prediction'].values))
    none_prob = prod_preds_dict.get(0, None)
    del prod_preds_dict[0]

    other_products = np.array(prod_preds_dict.keys())
    other_probs = np.array(prod_preds_dict.values())

    idx = np.argsort(-1*other_probs)
    other_products = other_products[idx]
    other_probs = other_probs[idx]

    opt = F1Optimizer.maximize_expectation(other_probs, none_prob)
    best_prediction = ['None'] if opt[1] else []
    best_prediction += list(other_products[:opt[0]])

    predicted_products = ' '.join(map(str, best_prediction)) if best_prediction else 'None'

    series['products'] = predicted_products
    series['true_products'] = true_products

    return true_products, predicted_products


gbm_df = pd.DataFrame({
    'order_id': np.load('predictions_gbm/order_ids.npy'),
    'product_id': np.load('predictions_gbm/product_ids.npy'),
    'prediction_gbm': np.load('predictions_gbm/predictions.npy'),
    'label': np.load('predictions_gbm/labels.py')
})


pred_df = gbm_df
pred_df['prediction'] = pred_df['prediction_gbm']

gb = pred_df.groupby('order_id')
dfs, order_ids = zip(*[(df, key) for key, df in gb])
p = Pool(cpu_count())
true_products, predicted_products = zip(*p.map(select_products, dfs))

pred_df = pd.DataFrame({'products': predicted_products, 'true_products': true_products, 'order_id': order_ids})
pred_df[['order_id', 'products']].to_csv('sub.csv', index=False)
