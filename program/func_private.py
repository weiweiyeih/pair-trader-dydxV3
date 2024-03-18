from datetime import datetime, timedelta
import time
import json
from func_utils import format_number
from pprint import pprint

# Get existing open positions
def is_open_positions(client, market):
    
    #Protect API
    time.sleep(0.2)

    # Get positions
    all_positions = client.private.get_positions(
        market=market,
        status="OPEN"
    )
    
    # Determine if open
    if len(all_positions.data["positions"]) > 0:
        return True
    else:
        return False

# Check order status
def check_order_status(client, order_id):
    order = client.private.get_order_by_id(order_id)
    if order.data:
        if "order" in order.data.keys():
            return order.data["order"]["status"]
    return "FAILED" # aka. order not exists

    '''
        == dYdX Order Statuses == 
        PENDING	    Order has yet to be processed by the matching engine.
        OPEN	    Order is active and on the orderbook. Could be partially filled.
        FILLED	    Fully filled.
        CANCELED	Canceled, for one of the cancel reasons. Could be partially filled.
        UNTRIGGERED	Triggerable order that has not yet been triggered.
        (FAILED)    Order not exists, Added by check_order_status()
        '''


# Place market order
def place_market_order(client, market, side, size, price, reduce_only):
    # Get Position Id
    account_response = client.private.get_account()
    position_id = account_response.data["account"]["positionId"]

    # Get expiration time
    server_time = client.public.get_time()
    expiration = datetime.fromisoformat(server_time.data["iso"].replace('Z','+00:00')) + timedelta(seconds=70) # minimum is 60 secs
    # Encountered "Dydx API Error: Order expiration cannot be less than 1 minute(s) in the future"
    # Fixed by replacing `.replace("Z", "")` to `.replace('Z','+00:00')`

    # Place an order
    placed_order = client.private.create_order(
        position_id=position_id,
        market=market,
        side=side,
        order_type="MARKET",
        post_only=False, # Market order -> False
        size=size, # BTC amount
        price=price, # A worst acceptable price. Must be above current market price when "BUY"
        limit_fee="0.015",
        expiration_epoch_seconds=expiration.timestamp(),
        time_in_force="FOK",
        reduce_only=reduce_only
    )
    
    # print(placed_order.data) #===========================>
    
    # Return result
    return placed_order.data

# Abort all open positions
def abort_all_positions(client):
    
    # Cancel all orders
    client.private.cancel_all_orders()
    
    # Protect API
    time.sleep(0.5) # second
    
    # Get markets (the info of all cryptos on DYDX) for reference of tickSize
    # To determine decimals when placing orders
    markets = client.public.get_markets().data

    
    # Protect API
    time.sleep(0.5)
    
    # Get all open positions
    positions = client.private.get_positions(status="OPEN")
    all_positions = positions.data["positions"]

    # Handle open positions
    close_orders = []
    if len(all_positions) > 0:
        
        # Loop through each position
        for position in all_positions:
            
            # Determine market (crypto)
            market = position["market"]

            # Determine side
            side = "BUY" # the side for the upcoming action
            if position["side"] == "LONG": # the side of the existing position
                side = "SELL"
            
            # Get price
            price = float(position["entryPrice"])
            accept_price = price * 1.7 if side == "BUY" else price * 0.3 # Accept max. 70% loss to exit
            tick_size = markets["markets"][market]["tickSize"] # Find correct decimals
            accept_price = format_number(accept_price, tick_size) # Format the decimals
            
            # Place order to close
            order = place_market_order(
                client,
                market,
                side,
                position["sumOpen"], 
                accept_price,
                True
            )
            
            # Append the result
            close_orders.append(order)
            
            # Protect API
            time.sleep(0.2)
        
        # Override json file with empty list after killing all the positions
        bot_agents = []
        with open("4_bot_agents.json", "w") as f:
            json.dump(bot_agents, f)
            
        print("All open positions killed")
        # Return closed orders
        return close_orders