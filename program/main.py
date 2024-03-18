from constants import ABORT_ALL_POSITIONS, FIND_COINTEGRATED, PLACE_TRADES, MANAGE_EXITS, MODE
from func_connections import connect_dydx
from func_private import abort_all_positions
from func_public import construct_market_prices
from func_cointegration import store_cointegration_results
from func_entry_pairs import open_positions
from func_exit_pairs import manage_trade_exits
from func_messaging import send_message
from w_func_backtest import backtest # W's note: Added backtest
import datetime # W's note: make FIND_COINTEGRATED run every 24 hours

next_timestamp_to_update = 0 # W's note: make FIND_COINTEGRATED run every 12 or 24 hours

# MAIN FUNCTION
if __name__ == "__main__":
    
    # Message on start
    send_message("Bot launched")

    print("")
    print("===== CONNECTION =====")
    
    # Connect to client
    # try/except -> In case anything goes wrong, we want to exit the code immediately and get notified
    try:
        print(f"Connecting to Client...{MODE} mode")
        client = connect_dydx()
    except Exception as e:
        print("Error connecting to client: ", e) # For log file
        send_message(f"Error connecting to client: {e}")
        exit(1) # Kill the Python script 
        
    # Abort all open positions
    if ABORT_ALL_POSITIONS:
        
        print("")
        print("===== ABORT ALL POSITIONS =====")
        
        try:
            
            print("Closing all positions...")
            close_orders = abort_all_positions(client)
        except Exception as e:
            print("Error closing all positions: ", e)
            send_message(f"Error closing all positions: {e}")
            exit(1)
    
    # Run as always on
    while True:
           
        # Find Cointegrated Pairs
        if FIND_COINTEGRATED:
            
            # convert datetime.datetime.now().timestamp() to human readable time
            
            
            if datetime.datetime.now().timestamp() > next_timestamp_to_update:
                next_timestamp_to_update = datetime.datetime.now().timestamp() + 61*60 # W's note: make FIND_COINTEGRATED run every 61 mins
                print("Updating cointegrated pairs...")
                send_message("Updating cointegrated pairs...")
                
                print("")
                print("===== FIND COINTEGRATION =====")
                
                # Construct Market Prices
                try:
                    print("Fetching market prices, please allow 3 mins...")
                    df_market_prices = construct_market_prices(client)
                except Exception as e:
                    print("Error constructing market prices: ", e)
                    send_message(f"Error constructing market prices: {e}")
                    exit(1)
                
                # Stored cointegrated pairs
                try:
                    print("Storing cointegrated pairs...")
                    stores_result = store_cointegration_results(df_market_prices)
                    
                    # W's note: backtest -> Coint_backtest.csv
                    backtest()
                    
                    date_object = datetime.datetime.fromtimestamp(next_timestamp_to_update)
                    print("Next time to update 3_coint_backtest.csv: ", date_object)
                    print("")
                    
                    if stores_result != "saved":
                        print("Error saving cointegrated pairs")
                        exit(1) # Even no logic error, if no cointegrated pairs, we stop the script
                except Exception as e:
                    print("Error saving cointegrated pairs: ", e)
                    send_message(f"Error saving cointegrated pairs: {e}")
                    exit(1)
        
    # # Run as always on
    # while True:
    
        if MANAGE_EXITS:
            
            print("")
            print("===== MANAGE EXITS =====")
            
            try:
                print("Managing exits...")
                result = manage_trade_exits(client)
                print(result)
            except Exception as e:
                print("Error managing exiting positions: ", e)
                send_message(f"Error managing exiting positions: {e}")
                exit(1)
            
        # Place trades for opening positions
        if PLACE_TRADES:
            
            print("")
            print("===== PLACE TRADES =====")
            
            try:
                print("Finding trading opportunities...")
                open_positions(client)
            except Exception as e:
                print("Error opening trades: ", e)
                send_message(f"Error opening trades: {e}")
                exit(1)
