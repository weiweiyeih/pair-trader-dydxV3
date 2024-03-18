import boto3
from boto3.dynamodb.conditions import Key, Attr
from decouple import config
import datetime

import pandas as pd

db = boto3.resource(
    'dynamodb',
    aws_access_key_id = config('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key = config('AWS_SECRET_ACCESS_KEY'),
    region_name = 'us-east-1'
    )

# for export
db_table = db.Table('Cointegration') # partition key: 'name' 

'''
def store_market_prices_dynamoBD(dataFrame, db_table):
    
    
    tickers = dataFrame.columns.to_list()
    
    ## Get close prices for each tradeable market
    item_dict = {}
    close_prices = []
    latest_datetime = dataFrame.index[-1]
    timeframe = str(len(dataFrame))
    for ticker in tickers:
        close_price = dataFrame[ticker].values.tolist()
        close_prices.append({ticker: close_price})
        
    item_dict = {
        'item_name': 'dydxV3_prices',
        'latest_datetime': latest_datetime,
        'interval': '1hr',
        'timeframe': timeframe,
        'close_prices': close_prices
    }
    
    # DELETE item
    db_table.delete_item(
        Key={
            'item_name': 'dydxV3_prices'
    })
    
    # PUT item
    db_table.put_item(Item=item_dict)
    
    print(f'item_name: "dydxV3_prices" updated in table: "{db_table.name}" in DynamoDB successfully') # time cost: 1m42s
    
def store_cointegration_results_dynamoDB(db_table, latest_datetime, criteria_met_pairs):
    
    # structure item
    item_dict = {
        'item_name': 'dydxV3_cointegrated_pairs',
        'latest_datetime': latest_datetime,
        'cointegrated_pairs': criteria_met_pairs
    }
    
    # DELETE item
    db_table.delete_item(
        Key={
            'item_name': 'dydxV3_cointegrated_pairs'
    })
    
    # PUT item
    db_table.put_item(Item=item_dict)
    
    # Return result
    print(f'"dydxV3_cointegrated_pairs" successfully updated in "{db_table.name}" in DynamoDB.')
'''


def store_cointegration_results_zscore_dynamoDB(db_table, dataFrame):

    cointegrated_pairs = []
    
    # loop through each row in the dataframe
    for index, row in dataFrame.iterrows():
        pair = {
            # convert a list of floats to a list of strings
            
            "base_market": row["base_market"],
            "quote_market": row["quote_market"],
            "hedge_ratio": str(row["hedge_ratio"]),
            "p_value": str(row["Coint P"]),
            "half_life": str(row["half_life"]),
            "z_score": str(row["zscore_latest"]),
        }
        cointegrated_pairs.append(pair)
        
    item_dict = {
        'item_name': 'dydxV3_cointegrated_pairs',
        'updated/UTC': datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        'cointegrated_pairs': cointegrated_pairs
    }
        
    # DELETE item
    db_table.delete_item(
        Key={
            'item_name': 'dydxV3_cointegrated_pairs'
    })
    
    # PUT item
    db_table.put_item(Item=item_dict)
    
    # Return result
    print(f'"dydxV3_cointegrated_pairs" successfully updated in "{db_table.name}" in DynamoDB.')