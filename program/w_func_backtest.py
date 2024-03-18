import pandas as pd
import numpy as np
import statsmodels.api as sm
from func_cointegration import calculate_zscore
from constants import SIGNALS # Refactor_01
from func_db import store_cointegration_results_zscore_dynamoDB, db_table
import datetime

"""
dataFrame: consists ticker_1, ticker_2, spread, zscore, zscore_lag
fee_rate: 0.05 == 0.05 %
base_bet_rato: between 0 and 1 (0.5 == 50% for each base and quote)
"""
def get_roi(dataFrame, zscore_entry, zscore_exit, fee_rate, base_bet_rato): # dataFrame with both prices and zscore
    
    trade_fee = fee_rate / 100

    initial_capital = 1000
    bet_on_base = initial_capital * base_bet_rato
    bet_on_quote = initial_capital * (1 - base_bet_rato)
    
    base_long_entry_price = 0
    base_short_entry_price = 0
    quote_long_entry_price = 0
    quote_short_entry_price = 0

    base_long_position = 0
    base_short_position = 0
    quote_long_position = 0
    quote_short_position = 0
    
    base_long_pnl = 0 # long: exit price - entry price
    base_short_pnl = 0 # short: entry price - exit price
    quote_long_pnl = 0
    quote_short_pnl = 0
    
    base_long_pnl_pct = 0 
    base_short_pnl_pct = 0 
    quote_long_pnl_pct = 0
    quote_short_pnl_pct = 0

    unrealized_pnl = 0
    realized_pnl = 0
    
    base_long_pnl_series = [] 
    base_short_pnl_series = [] 
    quote_long_pnl_series = []
    quote_short_pnl_series = []

    base_long_pnl_pct_series = [] 
    base_short_pnl_pct_series = [] 
    quote_long_pnl_pct_series = []
    quote_short_pnl_pct_series = []

    base_long_position_series = []
    base_short_position_series = []
    quote_long_position_series = []
    quote_short_position_series = []

    unrealized_pnl_series = []
    realized_pnl_series = []
    roi_series = []
    
     # Get the name of columns
    base_market = dataFrame.columns[0]
    quote_market = dataFrame.columns[1]
    
    # loop through the rows in df_pair
    for index, row in dataFrame.iterrows():
        
        zscore_curr = row['zscore_lag']

        # If don't have any positions -> consider zscore_entry -> check abs(zscore_lag)
        if base_long_position == 0 and base_short_position == 0 and quote_long_position == 0 and quote_short_position == 0:
        
            # check abs(zscore_lag) >=  zscore_entry ->  Triggered
            if abs(zscore_curr) >= zscore_entry:
                
                # if zscore_curr < 0, long pair -> buy base, sell quote
                if zscore_curr < 0:
                    
                    # Buy base
                    base_long_position = (bet_on_base) / row[base_market]
                    base_long_entry_price = row[base_market]
                    fee = (base_long_position * base_long_entry_price) * trade_fee
                    realized_pnl -= fee
                    base_long_pnl = (row[base_market] - base_long_entry_price) * base_long_position
                    base_long_pnl_pct = base_long_pnl / (base_long_entry_price * base_long_position)
                    
                    # Sell quote
                    quote_short_position = (bet_on_quote) / row[quote_market]
                    quote_short_entry_price = row[quote_market]
                    fee = (quote_short_position * quote_short_entry_price) * trade_fee
                    realized_pnl -= fee
                    quote_short_pnl = (quote_short_entry_price - row[quote_market]) * quote_short_position
                    quote_short_pnl_pct = quote_short_pnl / (quote_short_entry_price * quote_short_position)
                    
                    unrealized_pnl = base_long_pnl + quote_short_pnl

                    
                # if zscore_curr >= 0, short pair -> sell base, buy quote
                else:
                    
                    # Sell base
                    base_short_position = (bet_on_base) / row[base_market]
                    base_short_entry_price = row[base_market]
                    fee = (base_short_position * base_short_entry_price) * trade_fee
                    realized_pnl -= fee
                    base_short_pnl = (base_short_entry_price - row[base_market]) * base_short_position
                    base_short_pnl_pct = base_short_pnl / (base_short_entry_price * base_short_position)

                    # Buy quote
                    quote_long_position = (bet_on_quote) / row[quote_market]
                    quote_long_entry_price = row[quote_market]
                    fee = (quote_long_position * quote_long_entry_price) * trade_fee
                    realized_pnl -= fee
                    quote_long_pnl = (row[quote_market] - quote_long_entry_price) * quote_long_position
                    quote_long_pnl_pct = quote_long_pnl / (quote_long_entry_price * quote_long_position)

                    unrealized_pnl = base_short_pnl + quote_long_pnl
                    
            # else: If no positions and abs(zscore_lag) < zscore_entry -> do nothing
                
        # If have positions -> consider zscore_exit
        else:
            # check abs(zscore_lag) >=  zscore_exit
            if abs(zscore_curr) >= zscore_exit:
                
                # if zscore_curr >= 0 
                if zscore_curr >= 0:
                    
                    # have positions need to exit
                    if base_long_position > 0 and quote_short_position > 0:
                    
                        # Exit base_long_position
                        fee = (base_long_position * row[base_market]) * trade_fee
                        realized_pnl -= fee
                        base_long_pnl = (row[base_market] - base_long_entry_price) * base_long_position
                        base_long_pnl_pct = base_long_pnl / (base_long_entry_price * base_long_position)
                        base_long_position = 0
                        base_long_entry_price = 0
                        
                        # Exit quote_short_position
                        fee = (quote_short_position * row[quote_market]) * trade_fee
                        realized_pnl -= fee
                        quote_short_pnl = (quote_short_entry_price - row[quote_market]) * quote_short_position
                        quote_short_pnl_pct = quote_short_pnl / (quote_short_entry_price * quote_short_position)
                        quote_short_position = 0
                        quote_short_entry_price = 0
                        
                        unrealized_pnl = 0
                        realized_pnl += (base_long_pnl + quote_short_pnl)
                        
                        # no positions -> no pnl
                        base_long_pnl = 0
                        quote_short_pnl = 0
                    
                    # No positions need to exit
                    else:
                        # update pnl (no fee)
                        if base_long_position > 0:
                            base_long_pnl = (row[base_market] - base_long_entry_price) * base_long_position
                            base_long_pnl_pct = base_long_pnl / (base_long_entry_price * base_long_position) 
                        
                        if base_short_position > 0:
                            base_short_pnl = (base_short_entry_price - row[base_market]) * base_short_position
                            base_short_pnl_pct = base_short_pnl / (base_short_entry_price * base_short_position)
                            
                        if quote_long_position > 0:
                            quote_long_pnl = (row[quote_market] - quote_long_entry_price) * quote_long_position
                            quote_long_pnl_pct = quote_long_pnl / (quote_long_entry_price * quote_long_position)
                            
                        if quote_short_position > 0:
                            quote_short_pnl = (quote_short_entry_price - row[quote_market]) * quote_short_position
                            quote_short_pnl_pct = quote_short_pnl / (quote_short_entry_price * quote_short_position)
                            
                        unrealized_pnl = base_long_pnl + quote_short_pnl + base_short_pnl + quote_long_pnl
                        

                    
                # if zscore_curr < 0 
                else:
                    # have positions need to exit
                    if base_short_position > 0 and quote_long_position > 0:
                    
                        fee = (base_short_position * row[base_market]) * trade_fee
                        realized_pnl -= fee
                        base_short_pnl = (base_short_entry_price - row[base_market]) * base_short_position
                        base_short_pnl_pct = base_short_pnl / (base_short_entry_price * base_short_position)
                        base_short_position = 0
                        base_short_entry_price = 0
                        
                        fee = (quote_long_position * row[quote_market]) * trade_fee
                        realized_pnl -= fee
                        quote_long_pnl = (row[quote_market] - quote_long_entry_price) * quote_long_position
                        quote_long_pnl_pct = quote_long_pnl / (quote_long_entry_price * quote_long_position)
                        quote_long_position = 0
                        quote_long_entry_price = 0
                        
                        unrealized_pnl = 0
                        realized_pnl += base_short_pnl + quote_long_pnl
                        
                        # no positions -> no pnl
                        base_short_pnl = 0
                        quote_long_pnl = 0
                    
                    # No positions need to exit
                    else:
                        # update pnl (no fee)
                        if base_long_position > 0:
                            base_long_pnl = (row[base_market] - base_long_entry_price) * base_long_position
                            base_long_pnl_pct = base_long_pnl / (base_long_entry_price * base_long_position) 
                        
                        if base_short_position > 0:
                            base_short_pnl = (base_short_entry_price - row[base_market]) * base_short_position
                            base_short_pnl_pct = base_short_pnl / (base_short_entry_price * base_short_position)
                            
                        if quote_long_position > 0:
                            quote_long_pnl = (row[quote_market] - quote_long_entry_price) * quote_long_position
                            quote_long_pnl_pct = quote_long_pnl / (quote_long_entry_price * quote_long_position)
                            
                        if quote_short_position > 0:
                            quote_short_pnl = (quote_short_entry_price - row[quote_market]) * quote_short_position
                            quote_short_pnl_pct = quote_short_pnl / (quote_short_entry_price * quote_short_position)
                            
                        unrealized_pnl = base_long_pnl + quote_short_pnl + base_short_pnl + quote_long_pnl
            
            # If have positions but zscore_exit not triggered -> update pnl (no fee)
            else:
                if base_long_position > 0:
                    base_long_pnl = (row[base_market] - base_long_entry_price) * base_long_position
                    base_long_pnl_pct = base_long_pnl / (base_long_entry_price * base_long_position) 
                    
                if base_short_position > 0:
                    base_short_pnl = (base_short_entry_price - row[base_market]) * base_short_position
                    base_short_pnl_pct = base_short_pnl / (base_short_entry_price * base_short_position)
                    
                if quote_long_position > 0:
                    quote_long_pnl = (row[quote_market] - quote_long_entry_price) * quote_long_position
                    quote_long_pnl_pct = quote_long_pnl / (quote_long_entry_price * quote_long_position)
                    
                if quote_short_position > 0:
                    quote_short_pnl = (quote_short_entry_price - row[quote_market]) * quote_short_position
                    quote_short_pnl_pct = quote_short_pnl / (quote_short_entry_price * quote_short_position)
                    
                unrealized_pnl = base_long_pnl + quote_short_pnl + base_short_pnl + quote_long_pnl
        
        roi = (realized_pnl + unrealized_pnl) / initial_capital
                
        base_long_pnl_series.append(base_long_pnl) 
        base_short_pnl_series.append(base_short_pnl) 
        quote_long_pnl_series.append(quote_long_pnl)
        quote_short_pnl_series.append(quote_short_pnl)

        # base_long_pnl_pct_series.append(base_long_pnl_pct) 
        # base_short_pnl_pct_series.append(base_short_pnl_pct) 
        # quote_long_pnl_pct_series.append(quote_long_pnl_pct)
        # quote_short_pnl_pct_series.append(quote_short_pnl_pct)
        
        base_long_position_series.append(base_long_position)
        base_short_position_series.append(base_short_position)
        quote_long_position_series.append(quote_long_position)
        quote_short_position_series.append(quote_short_position)

        unrealized_pnl_series.append(unrealized_pnl)
        realized_pnl_series.append(realized_pnl)
        
        roi_series.append(roi)
    
    return base_long_pnl_series, base_short_pnl_series, quote_long_pnl_series, quote_short_pnl_series, base_long_position_series, base_short_position_series, quote_long_position_series, quote_short_position_series, unrealized_pnl_series, realized_pnl_series, roi_series

def backtest():
    
    # config signals and fees
    # signals = {
    #     'ROI%-1.5-0-0.05-0.5' : {'zscore_entry': 1.5, 'zscore_exit': 0, 'fee_rate': 0.05, 'base_bet_rato': 0.5},
    #     'ROI%-1.5-1.49-0.05-0.5' : {'zscore_entry': 1.5, 'zscore_exit': 1.49, 'fee_rate': 0.05, 'base_bet_rato': 0.5},   
    # }
    signals = SIGNALS # Refactor_01
    
    # Load data
    df_coint = pd.read_csv('2_cointegrated_pairs.csv') # cointegrated pairs
    df_markets = pd.read_csv('1_all_markets_close_prices.csv') # all markets close prices
    
    # If Unnamed: 0 column exists in df_coint, remove it
    if 'Unnamed: 0' in df_coint.columns:
        df_coint = df_coint.drop(columns=['Unnamed: 0'])

    # Loop through each row in df_coint
    for index, row in df_coint.iterrows():
        
        # Gte both tickers
        base_market = row['base_market'] # e.g. 'BTC'
        quote_market = row['quote_market']
        
        # Create a new df with the close prices of both markets from df_markets
        df = df_markets[[base_market, quote_market]]
        # Add datetime as index
        df.index = df_markets['datetime']
        
        # Extract each series of prices
        series_1 = df_markets[base_market].values
        series_2 = df_markets[quote_market].values
        
        # Get spread
        model = sm.OLS(series_1, series_2).fit()
        hedge_ratio = model.params[0]
        spread = series_1 - (hedge_ratio * series_2) # an array of floats
    
        # Calculate z-score
        zscore = calculate_zscore(spread) # Proved to be working!! :)
        
        # Add z-score and spread to df
        df.loc[:, 'spread'] = spread
        df.loc[:, 'zscore'] = zscore.values
        
        # drop nan rows of zscore
        df = df.dropna()
        
        # add zscore_lag for shift(1) to avoid look ahead bias
        df.loc[:, 'zscore_lag'] = df['zscore'].shift(1)
        df.loc[df.index[0], 'zscore_lag'] = df['zscore_lag'].iloc[1] # zscores_lag[0] = zscore_lag[1]
        # Here got a df with ticker_1, ticker_2, spread, zscore, zscore_lag
        
        # Loop through each signal
        for signal, values in signals.items():
            
            # Get zscore_entry, zscore_exit, fee_rate
            zscore_entry = values['zscore_entry']
            zscore_exit = values['zscore_exit']
            fee_rate = values['fee_rate']
            base_bet_rato = values['base_bet_rato']
            
            # Get a list of roi from get_roi func
            base_long_pnl_series, base_short_pnl_series, quote_long_pnl_series, quote_short_pnl_series, base_long_position_series, base_short_position_series, quote_long_position_series, quote_short_position_series, unrealized_pnl_series, realized_pnl_series, roi_series = get_roi(df, zscore_entry, zscore_exit, fee_rate, base_bet_rato)
            
            # add last item of roi to df_coint
            df_coint.loc[index, signal] = roi_series[-1]
            
        # Get the latest zscore
        zscore_latest = df['zscore'].iloc[-1]
        # Add the latest zscore to df_coint
        df_coint.loc[index, 'zscore_latest'] = round(zscore_latest, 2)
        
    store_cointegration_results_zscore_dynamoDB(db_table, df_coint)
    
    df_coint.to_csv('3_coint_backtest.csv') 
    print("Coint_backtest file successfully saved.")
    