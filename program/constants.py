from dydx3.constants import API_HOST_SEPOLIA, API_HOST_MAINNET
from decouple import config # Enable us to access our .env variables

# !!!! SELECT MODE !!!!
MODE = "PRODUCTION" # "DEVELOPMENT" or "PRODUCTION"

# Close all open positions and orders
ABORT_ALL_POSITIONS = False # Recommendation: Testnet -> True, Production -> False

# Find Cointegrated Pairs
FIND_COINTEGRATED = True

# Manage exits
MANAGE_EXITS = True

# Manage entries
PLACE_TRADES = True

# W's note: Exit when z_score_current crosses "zero" (default) or "the opposite of z_score_traded"
# EXIT_WHEN_CROSS_ZERO = False 

# Resolution (timeframe)
RESOLUTION = "1HOUR" # Hourly timeframe

# Stats Window (When calculating a rolling average for Z-score)
WINDOW = 21 # Do a rolling moving average based on 21 days

# Threshold - Opening
MAX_HALF_LIFE = 24
# ZSCORE_THRESHOLD = 1.5
# ZSCORE_ENTRY = 1.5 # replaced ZSCORE_THRESHOLD (always >= 0)
# ZSCORE_EXIT = 0 # replaced EXIT_WHEN_CROSS_ZERO (always >= 0)

SIGNALS = {
        'ROI%-1.5-0-0.05-0.5' : {'zscore_entry': 1.5, 'zscore_exit': 0, 'fee_rate': 0.05, 'base_bet_rato': 0.5},
        'ROI%-1.5-1.49-0.05-0.5' : {'zscore_entry': 1.5, 'zscore_exit': 1.49, 'fee_rate': 0.05, 'base_bet_rato': 0.5},   
    }

# Fund per trade and min. collateral
# Testnet
USD_PER_TRADE_TESTNET = 50 # $50 on each short and $50 on each long
USD_MIN_COLLATERAL_TESTNET = 1800 # the min. portfolio value required in your DYDX account to open a trade
# Mainnet
USD_PER_TRADE_MAINNET = 20 # $50 on each short and $50 on each long
USD_MIN_COLLATERAL_MAINNET = 20
# Export
USD_PER_TRADE = USD_PER_TRADE_MAINNET if MODE == "PRODUCTION" else USD_PER_TRADE_TESTNET
USD_MIN_COLLATERAL = USD_MIN_COLLATERAL_MAINNET if MODE == "PRODUCTION" else USD_MIN_COLLATERAL_TESTNET

# Threshold - Closing
# If we open a trade when Z-score hits -1.5, then we will close the trade when it crosses +1.5 (or 0)
CLOSE_AT_ZSCORE_CROSS = True

# Ethereum Address
WALLET_ADDRESS_TESTNET = "0xC62401919639742bBB6BBC995A78D057B261d649"
WALLET_ADDRESS_MAINNET = "0x112d294846dEFef9dE9f54848b9e3e0cdFEb15e3"
# Export
ETHEREUM_ADDRESS = WALLET_ADDRESS_MAINNET if MODE == "PRODUCTION" else WALLET_ADDRESS_TESTNET

# KEYS - Production
# Must to be on Mainnet on DYDX
STARK_PRIVATE_KEY_MAINNET = config("STARK_PRIVATE_KEY_MAINNET")
DYDX_API_KEY_MAINNET = config("DYDX_API_KEY_MAINNET")
DYDX_API_SECRET_MAINNET = config("DYDX_API_SECRET_MAINNET")
DYDX_API_PASSPHRASE_MAINNET = config("DYDX_API_PASSPHRASE_MAINNET")

# KEYS - Development
# Must to be on Testnet on DYDX
STARK_PRIVATE_KEY_TESTNET = config("STARK_PRIVATE_KEY_TESTNET")
DYDX_API_KEY_TESTNET = config("DYDX_API_KEY_TESTNET")
DYDX_API_SECRET_TESTNET = config("DYDX_API_SECRET_TESTNET")
DYDX_API_PASSPHRASE_TESTNET = config("DYDX_API_PASSPHRASE_TESTNET")

# KEYS - Export
STARK_PRIVATE_KEY = STARK_PRIVATE_KEY_MAINNET if MODE == "PRODUCTION" else STARK_PRIVATE_KEY_TESTNET
DYDX_API_KEY = DYDX_API_KEY_MAINNET if MODE == "PRODUCTION" else DYDX_API_KEY_TESTNET
DYDX_API_SECRET = DYDX_API_SECRET_MAINNET if MODE == "PRODUCTION" else DYDX_API_SECRET_TESTNET
DYDX_API_PASSPHRASE = DYDX_API_PASSPHRASE_MAINNET if MODE == "PRODUCTION" else DYDX_API_PASSPHRASE_TESTNET

# HOST - Export
HOST = API_HOST_MAINNET if MODE == "PRODUCTION" else API_HOST_SEPOLIA

# HTTP PROVIDER (Alchemy)
HTTP_PROVIDER = config("HTTP_PROVIDER_MAINNET") if MODE == "PRODUCTION" else config("HTTP_PROVIDER_TESTNET")

# Wallet Private Key - Export
ETH_PRIVATE_KEY = config("WALLET_PRIVATE_KEY_MAINNET") if MODE == "PRODUCTION" else config("WALLET_PRIVATE_KEY_TESTNET")

