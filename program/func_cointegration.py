import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint # For finding cointegration
from constants import MAX_HALF_LIFE, WINDOW
# from func_db import store_cointegration_results_dynamoDB, db_table

from datetime import datetime

# Calculate Half Life
# https://www.pythonforfinance.net/2016/05/09/python-backtesting-mean-reversion-part-2/

def calculate_half_life(spread):
    df_spread = pd.DataFrame(spread, columns=["spread"])
    spread_lag = df_spread.spread.shift(1) # aka # move row[0] to row[1], row[1] to row[2] and so on (df_spread.spread == df_spread["spread"])
    spread_lag.iloc[0] = spread_lag.iloc[1] # make row[0] == row[1] to avoid NaN value
    spread_ret = df_spread.spread - spread_lag
    spread_ret.iloc[0] = spread_ret.iloc[1]
    spread_lag2 = sm.add_constant(spread_lag)
    model = sm.OLS(spread_ret, spread_lag2)
    res = model.fit()
    halflife = round(-np.log(2) / res.params.iloc[1], 0) # To fix a future warning, "res.params[1]" -> "res.params.iloc[1]"
    return halflife

# Calculate Z-score
def calculate_zscore(spread):
    spread_series = pd.Series(spread)
    mean = spread_series.rolling(center=False, window=WINDOW).mean()
    std = spread_series.rolling(center=False, window=WINDOW).std()
    x = spread_series.rolling(center=False, window=1).mean()
    zscore = (x - mean) / std
    return zscore

# Calculate Cointegration
# Updated version in Lesson 34 will cause error. Do not use it!
# series_1 and series_2 are lists of closing prices of two markets
def calculate_cointegration(series_1, series_2):
    series_1 = np.array(series_1).astype(float) # To fix error: "(np.float)" -> "(float)"
    series_2 = np.array(series_2).astype(float)
    coint_flag = 0
    coint_res = coint(series_1, series_2)
    coint_t = coint_res[0]
    p_value = coint_res[1]
    critical_value = coint_res[2][1]
    model = sm.OLS(series_1, series_2).fit()
    hedge_ratio = model.params[0]
    spread = series_1 - (hedge_ratio * series_2)
    half_life = calculate_half_life(spread)
    t_check = coint_t < critical_value
    coint_flag = 1 if p_value < 0.05 and t_check else 0
    return coint_flag, hedge_ratio, half_life, p_value # W's note: Added p_value to return

# Store cointegration results -> argument from func_public.py/construct_market_prices()
def store_cointegration_results(df_market_prices):
    
    # Initialize 
    markets = df_market_prices.columns.to_list() # Get a list of markets (cryptos)
    criteria_met_pairs = []
    criteria_met_pairs_db = [] # for DynamoDB
    latest_datetime = df_market_prices.index[-1] # for DynamoDB
    
    # Find cointegrated pairs
    # Start with our base pair (column[0] in df and so on)
    for index, base_market in enumerate(markets[:-1]): # We don't need to loop through the last market
        # >>> This is how we get a series from df <<<
        series_1 = df_market_prices[base_market].values.astype(float).tolist()
        
        # Get quote pair
        for quote_market in markets[index +1:]:
            series_2 = df_market_prices[quote_market].values.astype(float).tolist()
            
            # Check cointegration
            coint_flag, hedge_ratio, half_life, p_value = calculate_cointegration(series_1, series_2)

            # Log pair
            if coint_flag == 1 and half_life <= MAX_HALF_LIFE and half_life > 0:
                criteria_met_pairs.append({
                    "base_market": base_market,
                    "quote_market": quote_market,
                    "hedge_ratio": hedge_ratio,
                    "half_life": half_life,
                    "Coint P": round(p_value, 4)
                })
                
                # for DynamoDB
                criteria_met_pairs_db.append({
                    "base_market": base_market,
                    "quote_market": quote_market,
                    "hedge_ratio": str(hedge_ratio),
                    "half_life": str(half_life),
                    "Coint P": str(round(p_value, 4))
                })
    
    # store_cointegration_results_dynamoDB(db_table, latest_datetime, criteria_met_pairs_db)
         
    # Create and save DataFrame
    df_criteria_met = pd.DataFrame(criteria_met_pairs)
    # currentTime = datetime.now()
    df_criteria_met.to_csv(f"2_cointegrated_pairs.csv")
    del df_criteria_met # Manage memory
    
    # Return result
    print("Cointegrated pairs successfully saved.")
    return "saved"