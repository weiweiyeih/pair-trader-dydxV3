from func_private import place_market_order, check_order_status
from datetime import datetime, timedelta
from func_messaging import send_message
import time

from pprint import pprint


# Class: Agent for managing opening and checking trades
class BotAgent:

  """
    Primary function of BotAgent handles opening and checking order status
  """

  # Initialize class
  def __init__(
    self,
    client,
    market_1,
    market_2,
    base_side,
    base_size,
    base_price,
    quote_side,
    quote_size,
    quote_price,
    accept_failsafe_base_price,
    z_score,
    half_life,
    hedge_ratio,
  ):

    # Initialize class variables
    self.client = client
    self.market_1 = market_1
    self.market_2 = market_2
    self.base_side = base_side
    self.base_size = base_size
    self.base_price = base_price
    self.quote_side = quote_side
    self.quote_size = quote_size
    self.quote_price = quote_price
    self.accept_failsafe_base_price = accept_failsafe_base_price
    self.z_score = z_score
    self.half_life = half_life
    self.hedge_ratio = hedge_ratio

    # Initialize output variable
    # Default pair status options are FAILED, LIVE, (CLOSE), ERROR
    self.order_dict = {
      "market_1": market_1,
      "market_2": market_2,
      "hedge_ratio": hedge_ratio,
      "z_score": z_score, # z-score entered
      "half_life": half_life,
      "order_id_m1": "",
      "order_m1_size": base_size,
      "order_m1_side": base_side,
      "order_time_m1": "",
      "order_id_m2": "",
      "order_m2_size": quote_size,
      "order_m2_side": quote_side,
      "order_time_m2": "",
      "order_entry_price_m1": "", # W's added note -> entry
      "order_entry_price_m2": "", # W's added note -> entry
      "order_exit_price_m1": "", # W's added note -> exit
      "order_exit_price_m2": "", # W's added note -> exit
      "order_exit_time_m1": "", # W's added note -> exit
      "order_exit_time_m2": "", # W's added note -> exit
      "z_score_entry_signal": "", # W's added note -> entry
      "z_score_exit_signal": "", # W's added note -> entry
      "z_score_exited": "", # W's added note -> exit
      "pair_status": "", # REMINDER: W's dict pair_status: ERROR & LIVE + EXITED
      "comments": "",
    }
    
    # ================ W's note - start =======================
  def place_base_order(self):
    print(f"Placing base order ({self.market_1})...")
    print(f"Z-Score: {round(self.z_score, 2)}, Side: {self.base_side}, Size: {self.base_size}, Price: {self.base_price}")
    
    try:
      base_order = place_market_order(
      self.client,
      market=self.market_1,
      side=self.base_side,
      size=self.base_size,
      price=self.base_price,
      reduce_only=False
    )

      # Store the order id
      self.order_dict["order_id_m1"] = base_order["order"]["id"]
      self.order_dict["order_time_m1"] = datetime.now().isoformat()
      self.order_dict["order_entry_price_m1"] = self.base_price # W's added note
      print(f"Base order ({self.market_1}) placed")
    except Exception as e:
      self.order_dict["pair_status"] = "ERROR"
      self.order_dict["comments"] = f"Error placing base order ({self.market_1}): {e}"
      print(f"Error placing base order ({self.market_1}): {e}")
      return self.order_dict
    
  
  def base_order_status(self):
    # Allow time to process
    time.sleep(2)
    print(f"Checking base order ({self.market_1}) status...")
    order_status = check_order_status(self.client, self.order_dict["order_id_m1"])
    print(f"Base order status: {order_status}")
    return order_status
    '''
      == dYdX Order Statuses == 
      PENDING	    Order has yet to be processed by the matching engine.
      OPEN	      Order is active and on the orderbook. Could be partially filled.
      FILLED	    Fully filled.
      CANCELED	  Canceled, for one of the cancel reasons. Could be partially filled.
      UNTRIGGERED	Triggerable order that has not yet been triggered.
      (FAILED)    Order not exists, Added by check_order_status()
      '''
  
  def place_quote_order(self):
    print(f"Placing quote order ({self.market_2})...")
    print(f"Z-Score: {self.z_score}, Side: {self.quote_side}, Size: {self.quote_size}, Price: {self.quote_price}")
    
    try:
      quote_order = place_market_order(
      self.client,
      market=self.market_2,
      side=self.quote_side,
      size=self.quote_size,
      price=self.quote_price,
      reduce_only=False
    )

      # Store the order id
      self.order_dict["order_id_m2"] = quote_order["order"]["id"]
      self.order_dict["order_time_m2"] = datetime.now().isoformat()
      self.order_dict["order_entry_price_m2"] = self.quote_price # W's added note
      print(f"Quote order ({self.market_2}) placed")
    except Exception as e:
      self.order_dict["pair_status"] = "ERROR"
      self.order_dict["comments"] = f"Error placing quote order ({self.market_2}): {e}"
      print(f"Error placing quote order ({self.market_2}): {e}")
      return self.order_dict
    
  
  def quote_order_status(self):
    # Allow time to process
    time.sleep(2)
    print(f"Checking quote order ({self.market_2}) status...")
    order_status = check_order_status(self.client, self.order_dict["order_id_m2"])
    print(f"Quote order status: {order_status}")
    return order_status
    
  def cancel_base_order_if_not_filled(self):
    print("Canceling base order as it's not filled...")
    self.client.private.cancel_order(order_id=self.order_dict["order_id_m1"])
    
    time.sleep(2)
    base_order_to_cancel = self.base_order_status()
    if base_order_to_cancel != "CANCELED":
      print(f"Failing canceling base order after it's not filled - market: {self.market_1}, status: {base_order_to_cancel}. Exiting bot -> Consider cancel manually!")
      self.order_dict["pair_status"] = "ERROR"
      exit(1)
    
    self.order_dict["pair_status"] = "ERROR"
    print(f"Base order ({self.market_1}) canceled")
    
    
  def cancel_quote_order_if_not_filled(self):
    print("Canceling quote order as it's not filled...")
    self.client.private.cancel_order(order_id=self.order_dict["order_id_m2"])
    
    time.sleep(2)
    quote_order_to_cancel = self.quote_order_status()
    if quote_order_to_cancel != "CANCELED":
      print(f"Failing canceling quote order after it's not filled - market: {self.market_2}, status: {quote_order_to_cancel}. Exiting bot -> Consider cancel manually!")
      self.order_dict["pair_status"] = "ERROR"
      exit(1)
    
    self.order_dict["pair_status"] = "ERROR"
    print(f"Quote order ({self.market_2}) canceled")
      
  def close_base_position_if_quote_order_not_filled(self):
    print("Closing base position as quote order was not filled...")
    try:
      close_base_order = place_market_order(
        self.client,
        market=self.market_1,
        side=self.quote_side,
        size=self.base_size,
        price=self.accept_failsafe_base_price,
        reduce_only=True
      )

      
    # Ensure order is live before proceeding
      time.sleep(2)
      close_base_order_status = check_order_status(self.client, close_base_order["order"]["id"])
      if close_base_order_status == "FILLED":
        print(f"Base position ({self.market_1}) closed as quote order was not filled")
        self.order_dict["pair_status"] = "ERROR"
        
      else:
        print(f"Failed closing base position - market: {self.market_1}, status: {close_base_order_status}. Exiting bot -> Consider cancel manually!")
        self.order_dict["pair_status"] = "ERROR"

        # Send Message
        send_message(f"Failed closing base position - market: {self.market_1}, status: {close_base_order_status}. Exiting bot -> Consider cancel manually!")

        # ABORT
        exit(1)
    except Exception as e:
      self.order_dict["pair_status"] = "ERROR"
      self.order_dict["comments"] = f"Erroring closing base position - {self.market_1}: {e}"
      print(f"Error closing base position - market: {self.market_1}, status: {close_base_order_status}. Exiting bot -> Consider cancel manually!")
      # print("-- Exiting bot!!!")
      self.order_dict["pair_status"] = "ERROR"

      # Send Message
      send_message(f"Error closing base position - market: {self.market_1}, status: {close_base_order_status}. Exiting bot!!!")

      # ABORT
      exit(1)

  def open_trades(self):
    print(f"----- Opening trade for {self.market_1} (base) & {self.market_2} (quote) -----")
    
    self.place_base_order()
    
    base_order_status = self.base_order_status()
    
    '''
    REMINDER: dydx order status
      == dYdX Order Statuses == 
      PENDING	    Order has yet to be processed by the matching engine.
      OPEN	      Order is active and on the orderbook. Could be partially filled.
      FILLED	    Fully filled.
      CANCELED	  Canceled, for one of the cancel reasons. Could be partially filled.
      UNTRIGGERED	Triggerable order that has not yet been triggered.
      (FAILED)    Order not exists, Added by check_order_status()
      '''
      
    if base_order_status != "FILLED":
      if base_order_status != "CANCELED":  # if not canceled -> proceed to cancel
          self.cancel_base_order_if_not_filled()
          
    
    # if base_order_status != "FAILED": # (dydx status) order exists
      
    #   if base_order_status != "FILLED": # but not filled
        
    #     if base_order_status != "CANCELED":  # if not canceled -> proceed to cancel
    #       self.cancel_base_order_if_not_filled()
        
      # self.order_dict["pair_status"] = "FAILED"
      
      
      self.order_dict["pair_status"] = "ERROR"
      return self.order_dict
    
    # base_order_status == "FILLED" -> proceed to quote order
    else:
      self.place_quote_order()
      
      quote_order_status = self.quote_order_status()
      
      if quote_order_status != "FILLED":
        
        if quote_order_status != "CANCELED":
          self.cancel_quote_order_if_not_filled()
        
        self.close_base_position_if_quote_order_not_filled()
        
        self.order_dict["pair_status"] = "ERROR"
        return self.order_dict
      
      # quote_order_status == "FILLED"
      else:
        
        self.order_dict["pair_status"] = "LIVE"
        return self.order_dict

          
      
      
    # ================ W's note - end =========================

  
      