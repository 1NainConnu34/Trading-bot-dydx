from dydx3 import Client
from dydx3.constants import *
import time
from decimal import Decimal
import pandas as pd
from datetime import datetime

ETHEREUM_ADDRESS = 'YOUR_ETHEREUM_ADDRESS'

# Connection with the account
client = Client(
    network_id=NETWORK_ID_MAINNET,
    host=API_HOST_MAINNET,
    default_ethereum_address=ETHEREUM_ADDRESS,
    api_key_credentials={ 'key': 'YOUR_KEY', 
                         'secret': 'YOU_SECRET-', 
                         'passphrase': 'YOUR_PASSPHRASE'},
    stark_private_key='YOUR_STARK_PRIVATE_KEY',
)

account_response = client.private.get_account()

position_id = account_response.data['account']['positionId']

# Information for top 10 Market Cap coins on dydx
coins = ["BTC-USD", "ETH-USD", "ADA-USD", "DOGE-USD", "MATIC-USD", "SOL-USD", "DOT-USD", "LTC-USD", "AVAX-USD", "TRX-USD"]
coins_open_pos = [-0.93, -1.21, -1.4, -1.33, -1.92, -1.97, -1.62, -1.33, -1.97, -1.22]
coins_data = []
digits_after_comma = [4, 3, 0, -1, 0, 1, 1, 2, 1, -1]

hour = datetime.now().hour

def get_data_coin(coin):
    return client.public.get_markets(coin).data['markets'][coin]

for coin in coins:
    coins_data.append(get_data_coin(coin))

def get_ask_bid(coin):
    market = client.public.get_orderbook(coin)
    ask = market.data['asks']
    bid = market.data['bids']
    best_ask = ask[0]['price']
    best_bid = bid[0]['price']
    for i in range(1, len(ask)):
        best_ask = str(min(float(ask[i]['price']), float(best_ask)))
    for i in range(1, len(bid)):
        best_bid = str(max(float(bid[i]['price']), float(best_bid)))
    return [best_ask, best_bid]

def get_market_price(coin):
    market = client.public.get_markets()
    price = pd.DataFrame(market.data['markets'])
    return float(price[coin]['indexPrice'])

def create_order(side, coin_data, position_id, coin, size, time_in_force):
    if side == ORDER_SIDE_BUY:
        ask_bid = get_ask_bid(coin)
        price = Decimal(ask_bid[0]) + Decimal(coin_data['tickSize']) * Decimal('20')
        price = Decimal(price).quantize(Decimal(coin_data['tickSize']))
        order_params = {'position_id': position_id, 'market': coin, 'side': ORDER_SIDE_BUY,
        'order_type': ORDER_TYPE_MARKET, 'post_only': False, 'size': str(size),
        'price': str(price), 'limit_fee': '0.1', 'time_in_force': time_in_force,
        'expiration_epoch_seconds': time.time() + 120}
        return client.private.create_order(**order_params)
    else:
        ask_bid = get_ask_bid(coin)
        price = Decimal(ask_bid[1]) - Decimal(coin_data['tickSize']) * Decimal('20')
        price = Decimal(price).quantize(Decimal(coin_data['tickSize']))
        order_params = {'position_id': position_id, 'market': coin, 'side': ORDER_SIDE_SELL,
        'order_type': ORDER_TYPE_MARKET, 'post_only': False, 'size': str(size),
        'price': str(price), 'limit_fee': '0.1', 'time_in_force': time_in_force,
        'expiration_epoch_seconds': time.time() + 120}
        return client.private.create_order(**order_params)

def close_position(coin, account_response, position_id, coin_data):
    if account_response[coin]['side'] == 'LONG':
        create_order(ORDER_SIDE_SELL, coin_data, position_id, coin, account_response[coin]['size'], "FOK")
    else:
        create_order(ORDER_SIDE_BUY, coin_data, position_id, coin, str(abs(float(account_response[coin]['size']))), "FOK")

def get_size(coin, size_in_fiat):
    price_coin = get_market_price(coin)
    nb_digits = digits_after_comma[coins.index(coin)]
    if nb_digits == 0:
        return int(round(size_in_fiat / price_coin))
    else:
        return round(size_in_fiat / price_coin, nb_digits)


while True:
    print("Waiting for hour", (hour + 1) % 24, "\n")
    while datetime.now().hour == hour:
        time.sleep(30)
    hour = datetime.now().hour
    file = open("trade_history.txt", "a")

    # Closing open position
    print("Closing all open positions that exist")
    print("Hour: ", hour, "\n", sep="")
    list_coins = []
    account_response = client.private.get_account().data['account']['openPositions']
    if len(account_response) > 0:
        for coin in account_response.keys():
            list_coins.append(coin)
        for coin in list_coins:
            close_position(coin, account_response, position_id, coins_data[coins.index(coin)])
            print("Closing a long postion with", coin)
    else:
        print("There is 0 open position")

    print("\nAnalyzing in 45 seconds\n")
    time.sleep(45)

    
    # Opening new positions if the conditions are met
    balance = float(client.private.get_account().data['account']['quoteBalance'])
    print("Opening new positions if the conditions are met :\n")
    list_index = []
    nb_position_open = 0
    for i in range(len(coins)):
        info_last_candle = client.public.get_candles(coins[i], resolution="1HOUR").data['candles'][1]
        open = info_last_candle['open']
        close = info_last_candle['close']
        percentage = (float(close) - float(open)) / float(open) * 100
        print("Coin and percentage : ", coins[i], " ", percentage, "%", sep="")
        if (percentage <= coins_open_pos[i]):
            list_index.append(i)
    for i in list_index:
        nb_position_open += 1
        create_order(ORDER_SIDE_BUY, coins_data[i], position_id, coins[i], get_size(coins[i], balance / (len(list_index) + 0.0125 * len(list_index))), "IOC")
        print("\nOpening a long position with", coins[i])
    if (nb_position_open <= 1):
        print(nb_position_open + "position created\n")
    else:
        print(nb_position_open + "positions created\n")

    # Actualizing trade_history.txt
    print("Actualizing trade_history.txt\n\n")
    for coin in list_coins:
        last_position = client.private.get_positions(market=coin, status=POSITION_STATUS_CLOSED).data['positions'][-1]
        text = "Trade open with "
        text += coins[0] + " from " + str(hour - 1) + "h to " + str(hour) + "h\n"
        text += "Realized PNL : " + last_position['realizedPnl'] + "\n"
        file.write(text)
    if len(list_coins) != 0:
        text = "Balance now : " + "$" + client.private.get_account().data['account']['quoteBalance'] + "\n"
        file.write(text)
    file.close()
