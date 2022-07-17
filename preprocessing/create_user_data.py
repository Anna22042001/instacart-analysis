import os

import pandas as pd


def parse_order(x):
    # order as the key feature
    series1 = pd.Series(dtype='float64')
    
    series1['products'] = '_'.join(x['product_id'].values.astype(str).tolist())
    # series['x'] - "xid1_xid2..." in the order 
    series1['reorders'] = '_'.join(x['reordered'].values.astype(str).tolist())
    # series['x'] - "xid1_xid2..." in the order
    series1['aisles'] = '_'.join(x['aisle_id'].values.astype(str).tolist())
    # series['x'] - "xid1_xid2..." in the order
    series1['departments'] = '_'.join(x['department_id'].values.astype(str).tolist())
    # series['x'] - "xid1_xid2..." in the order

    # Identify features
    series1['order_number'] = x['order_number'].iloc[0]
    series1['order_dow'] = x['order_dow'].iloc[0]
    series1['order_hour'] = x['order_hour_of_day'].iloc[0]
    series1['days_since_prior_order'] = x['days_since_prior_order'].iloc[0]

    return series1


def parse_user(x):
    parsed_orders = x.groupby('order_id', sort=False).apply(parse_order)

    series = pd.Series()
    # series['x'] - "xid1 xid2..." in the order 
    series['order_ids'] = ' '.join(parsed_orders.index.map(str).tolist())
    series['order_numbers'] = ' '.join(parsed_orders['order_number'].map(str).tolist())
    series['order_dows'] = ' '.join(parsed_orders['order_dow'].map(str).tolist())
    series['order_hours'] = ' '.join(parsed_orders['order_hour'].map(str).tolist())
    series['days_since_prior_orders'] = ' '.join(parsed_orders['days_since_prior_order'].map(str).tolist())
    # series['x'] - "xid11-xid12 xid2-xid21..." in the order 
    series['product_ids'] = ' '.join(parsed_orders['products'].values.astype(str).tolist())
    series['aisle_ids'] = ' '.join(parsed_orders['aisles'].values.astype(str).tolist())
    series['department_ids'] = ' '.join(parsed_orders['departments'].values.astype(str).tolist())
    series['reorders'] = ' '.join(parsed_orders['reorders'].values.astype(str).tolist())

    series['eval_set'] = x['eval_set'].values[-1]

    return series

if __name__ == '__main__':
    #orders: order_id; user_id; eval_set; order_number; order_dow; order_hour_of_day; days_since_prior
    orders = pd.read_csv('../data/raw/orders.csv')
    # prior-train: order_id; product_id; add_to_cart_order; reordered
    prior_products = pd.read_csv('../data/raw/order_products__prior.csv')
    train_products = pd.read_csv('../data/raw/order_products__train.csv')
    # order-product: prior + order
    order_products = pd.concat([prior_products, train_products], axis=0)
    # product: product_id; product_name; aisle_id; department_id
    products = pd.read_csv('../data/raw/products.csv')
    
    # Merge by order_id; product_id: "productid1_productid2"
    df = orders.merge(order_products, how='left', on='order_id')
    # Merge by order_id; product_id: "productid1_productid2"
    df = df.merge(products, how='left', on='product_id')
    df['days_since_prior_order'] = df['days_since_prior_order'].fillna(0).astype(int)
    null_cols = ['product_id', 'aisle_id', 'department_id', 'add_to_cart_order', 'reordered']
    df[null_cols] = df[null_cols].fillna(0).astype(int)

    if not os.path.isdir('../data/processed'):
        os.makedirs('../data/processed')
    # user_data: order_ids; product_ids; product_name; aisle_id; department_id; add_to_cart_order; reordered; user_id; eval_set; order_number; order_dow; order_hour_of_day; days_since_prior
    user_data = df.groupby('user_id', sort=False).apply(parse_user).reset_index()
    user_data.to_csv('../data/processed/user_data.csv', index=False)
