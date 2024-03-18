from constants import USD_PER_TRADE, USD_MIN_COLLATERAL, SIGNALS # Refactor_01
from func_utils import format_number
from func_public import get_candles_recent
from func_cointegration import calculate_zscore
from func_private import is_open_positions
# from func_bot_agent import BotAgent
from w2_func_bot_agent import BotAgent # debug
from func_messaging import send_message
import pandas as pd
import json
import time
import statsmodels.api as sm # compare hedge_ratio & hedge_ratio_new

from pprint import pprint

# Open positions
def open_positions(client):
    
    """
        Manage finding triggers for trade entry 
        Store trades for managing later on on exit function
    """
    
    # Load cointegrated pairs
    df = pd.read_csv("3_coint_backtest.csv") # default: cointegrated_pairs.csv # Refactor_01
    
    # Get markets from referencing of min order size, tick size etc
    markets = client.public.get_markets().data
    
    # Initialize container for BotAgent results
    bot_agents = []
    # Opening JSON file
    try:
        open_positions_file = open("4_bot_agents.json")
        open_positions_dict = json.load(open_positions_file)
        for p in open_positions_dict:
            bot_agents.append(p)
        
    except:
        # In case no file exists
        bot_agents = []
    
    print(f"Checking {len(df.index)} pairs in 3_coint_backtest.csv") # default: cointegrated_pairs.csv # Refactor_01
    
    # Find ZScore triggers
    for index, row in df.iterrows():
        
        # print(f"Checking entry opportunity for {index + 1} of {len(df.index)} pairs in csv")
        
        # Extract variables
        base_market = row["base_market"]
        quote_market = row["quote_market"]                                
        hedge_ratio = row["hedge_ratio"]
        half_life = row["half_life"]
        
        # Refactor_01: Get ZScore entry signal(here both 1.5)
        keys = df.columns[df.columns.str.startswith("ROI")]
        
        print("")
        print(f"----- Checking entry opportunity for {index + 1} of {len(df.index)}: {base_market} & {quote_market} -----") # W's note
        print(f"ROI_{keys[0]}: {round(row[keys[0]], 4)} | ROI_{keys[1]}: {round(row[keys[1]], 4)}") 
        # if both backtest results are negative, skip
        if row[keys[0]] <= 0.1 and row[keys[1]] <= 0.1:
            print(f"Both backtest results are below 0.1 -> pass") # W's note
            continue
        
        if row[keys[0]] >= row[keys[1]]:
            zscore_entry_signal = SIGNALS[keys[0]]['zscore_entry']
            zscore_exit_signal = SIGNALS[keys[0]]['zscore_exit']    
        else:
            zscore_entry_signal = SIGNALS[keys[1]]['zscore_entry']
            zscore_exit_signal = SIGNALS[keys[1]]['zscore_exit']
        
        
        # Get latest 100 close prices
        series_1 = get_candles_recent(client, base_market)
        time.sleep(0.5) # Fix dydx Error opening trades:  DydxApiError(status_code=429...)
        series_2 = get_candles_recent(client, quote_market)
        
        
        
        # Get ZScore
        if len(series_1) > 0 and len(series_1) == len(series_2):
            # TODO: Calculate updated hedge_ratio???
            spread = series_1 - (hedge_ratio * series_2)
            z_score = calculate_zscore(spread).values.tolist()[-1] # get the last value
            
            
            
            
            
            # W's note:
            # model = sm.OLS(series_1, series_2).fit()
            # hedge_ratio_new = model.params[0]
            # spread_new = series_1 - (hedge_ratio_new * series_2)
            # z_score_new = calculate_zscore(spread_new).values.tolist()[-1]
            # print(f"Zscore with hedge_ratio: {round(z_score, 2)}")
            # print(f"Zscore with hedge_ratio_new: {round(z_score_new, 2)}")
            
            print(f"ZScore: {round(z_score, 2)} -> proceed") if abs(z_score) >= zscore_entry_signal else print(f"ZScore: {round(z_score, 2)} -> pass") # W's note
            
            # Establish if potential trade
            if abs(z_score) >= zscore_entry_signal:
                
                # Ensure like-for-like not already open (diversify trading)
                is_base_open = is_open_positions(client, base_market)
                time.sleep(0.5) # Fix dydx Error opening trades:  DydxApiError(status_code=429...)
                is_quote_open = is_open_positions(client, quote_market)

                print(f"Both markets not in existing positions -> proceed") if not is_base_open and not is_quote_open else print(f"One or both of the markets in existing positions -> pass") # W's note

                # Place trade
                if not is_base_open and not is_quote_open:
                    
                    # Determine side
                    base_side = "BUY" if z_score < 0 else "SELL"
                    quote_side = "BUY" if z_score > 0 else "SELL"
                    
                    # Get acceptable price in string format with correct number of decimals
                    base_price = series_1[-1]
                    quote_price = series_2[-1]
                    accept_base_price = float(base_price) * 1.01 if z_score < 0 else float(base_price) * 0.99 # default: 1.01 / 0.99
                    accept_quote_price = float(quote_price) * 1.01 if z_score > 0 else float(quote_price) * 0.99 # default: 1.01 / 0.99
                    failsafe_base_price = float(base_price) * 0.3 if z_score < 0 else float(base_price) * 1.7
                    base_tick_size = markets["markets"][base_market]["tickSize"] 
                    quote_tick_size = markets["markets"][quote_market]["tickSize"] 

                    # Format prices
                    accept_base_price = format_number(accept_base_price, base_tick_size)
                    accept_quote_price = format_number(accept_quote_price, quote_tick_size)
                    failsafe_base_price = format_number(failsafe_base_price, base_tick_size)
                    
                    # Get size
                    base_quantity = 1 / base_price * USD_PER_TRADE
                    quote_quantity = 1 / quote_price * USD_PER_TRADE
                    base_step_size = markets["markets"][base_market]["stepSize"]
                    quote_step_size = markets["markets"][quote_market]["stepSize"] 
                    
                    # Format sizes
                    base_size = format_number(base_quantity, base_step_size)
                    quote_size = format_number(quote_quantity, quote_step_size)
                    
                    # Ensure size
                    base_min_order_size = markets["markets"][base_market]["minOrderSize"]
                    quote_min_order_size = markets["markets"][quote_market]["minOrderSize"]
                    check_base = float(base_quantity) > float(base_min_order_size)
                    check_quote = float(quote_quantity) > float(quote_min_order_size)
                    
                    print(f"Both markets' qty > min. order sizes -> proceed") if check_base and check_quote else print(f"One or both of the markets' qty < min. order sizes -> pass") # W's note
                    
                    # If checks pass, place trades
                    if check_base and check_quote:
                                              
                        # Check account balance
                        account = client.private.get_account()
                        free_collateral = float(account.data["account"]["freeCollateral"])
                        print("")
                        
                        print(f"Balance: {free_collateral} > minimum: {USD_MIN_COLLATERAL} -> proceed to placing trades") if free_collateral > USD_MIN_COLLATERAL else print(f"Balance: {free_collateral} < minimum: {USD_MIN_COLLATERAL} -> pass & break the loop") # W's note
                        
                        # Guard: Ensure collateral
                        if free_collateral < USD_MIN_COLLATERAL:
                            break
                        
                        # Create Bot Agent
                        bot_agent = BotAgent(
                            client,
                            market_1=base_market,
                            market_2=quote_market,
                            base_side=base_side,
                            base_size=base_size,
                            base_price=accept_base_price,
                            quote_side=quote_side,
                            quote_size=quote_size,
                            quote_price=accept_quote_price,
                            accept_failsafe_base_price=failsafe_base_price,
                            z_score=z_score, # z-score entered
                            half_life=half_life,
                            hedge_ratio=hedge_ratio,
                        )
                        
                        bot_agent.order_dict["z_score_entry_signal"] = zscore_entry_signal # W's note
                        bot_agent.order_dict["z_score_exit_signal"] = zscore_exit_signal # W's note
                        # Open trades
                        # Call functions on the instance of BotAgent
                        bot_open_dict = bot_agent.open_trades()
                        
                        # Guard: Handle failure
                        if bot_open_dict["pair_status"] ==  "ERROR":
                            # print(f"ERROR for pair: {base_market} & {quote_market}") 
                            print("Moving to next pair...")
                            continue
                        
                        # Handle success in opening trades
                        if bot_open_dict["pair_status"] == "LIVE":
                            
                            print(f"Pair Status: LIVE")
                            # Append to list of bot agents
                            bot_agents.append(bot_open_dict)
                            del(bot_open_dict) # Free memory
                            
                            print("Appended to BotAgent.json")
                            print("LIVE bot_agents: ", len(bot_agents)) # debug



    # Save agents
    # ============ debug - start ================
    
    # warning if num of positions on dydx != on json file
    all_positions = client.private.get_positions(status="OPEN").data["positions"]
    if len(all_positions) / 2 != len(bot_agents):
        print("Error: num of positions on dydx != on json file")
        send_message("Error: num of positions on dydx != on json file")
        exit(1)
    
    # ============ debug - end ==================
    
    if len(bot_agents) > 0:
        with open("4_bot_agents.json", "w") as f:
            json.dump(bot_agents, f)
            print("")
            print(f"{len(bot_agents)} pairs LIVE and saved to 4_bot_agents.json file")
            # send_message(bot_agents) # debug
            # send_message(f"bot_agents: {len(bot_agents)}") # debug
                        
                        

                        
                        
                    
                    
                    
            
    
        
        
    
    
    

